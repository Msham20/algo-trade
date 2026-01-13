"""
Auto Trading Module
Automatically executes trades based on NIFTY signals without manual permission
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Callable
from enum import Enum

from nifty_signal_analyzer import get_analyzer, NiftySignalAnalyzer
from paper_trading import get_paper_engine, PaperTradingEngine
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class TradingMode(Enum):
    PAPER = "paper"  # Paper trading (no real money)
    LIVE = "live"    # Live trading (real money - requires Zerodha)


class AutoTrader:
    """
    Automatic trading bot that executes trades based on NIFTY signals.
    Runs in paper mode by default for safety.
    """
    
    def __init__(self, 
                 mode: TradingMode = TradingMode.PAPER,
                 quantity: int = 50,
                 min_signal_strength: int = 40,
                 check_interval_seconds: int = 300,  # 5 minutes
                 max_trades_per_day: int = 5):
        """
        Initialize the auto trader.
        
        Args:
            mode: PAPER or LIVE trading mode
            quantity: Number of units per trade
            min_signal_strength: Minimum signal strength to execute trade (0-100)
            check_interval_seconds: How often to check for signals
            max_trades_per_day: Maximum trades allowed per day
        """
        self.mode = mode
        self.quantity = quantity
        self.min_signal_strength = min_signal_strength
        self.check_interval = check_interval_seconds
        self.max_trades_per_day = max_trades_per_day
        
        self.analyzer = get_analyzer()
        self.paper_engine = get_paper_engine()
        self.kite = None  # For live trading
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._trades_today = 0
        self._last_trade_time: Optional[datetime] = None
        self._last_signal: Optional[str] = None
        self._callbacks: list[Callable] = []
        
        # Trading session times (IST)
        self.market_open_hour = 9
        self.market_open_minute = 15
        self.market_close_hour = 15
        self.market_close_minute = 30
        
        # Status tracking
        self.status = {
            'is_running': False,
            'mode': mode.value,
            'last_check': None,
            'last_signal': None,
            'trades_today': 0,
            'last_trade': None,
            'errors': []
        }
    
    def set_kite(self, kite):
        """Set Kite connection for live trading"""
        self.kite = kite
        self.analyzer.kite = kite
    
    def add_callback(self, callback: Callable):
        """Add callback for trade notifications"""
        self._callbacks.append(callback)
    
    def _notify(self, event: str, data: Dict):
        """Notify all callbacks"""
        for cb in self._callbacks:
            try:
                cb(event, data)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        now = datetime.now()
        
        # Check if weekday (Monday = 0, Sunday = 6)
        if now.weekday() >= 5:
            return False
        
        market_open = now.replace(
            hour=self.market_open_hour, 
            minute=self.market_open_minute, 
            second=0
        )
        market_close = now.replace(
            hour=self.market_close_hour, 
            minute=self.market_close_minute, 
            second=0
        )
        
        return market_open <= now <= market_close
    
    def should_trade(self, signal: Dict) -> tuple[bool, str]:
        """
        Determine if we should execute a trade based on signal.
        
        Returns:
            Tuple of (should_trade: bool, reason: str)
        """
        # Check if signal is actionable (not HOLD)
        if signal.get('signal') == 'HOLD':
            return False, "Signal is HOLD - no trade"
        
        # Check signal strength
        strength = signal.get('strength', 0)
        if strength < self.min_signal_strength:
            return False, f"Signal strength {strength}% below minimum {self.min_signal_strength}%"
        
        # Check max trades per day
        if self._trades_today >= self.max_trades_per_day:
            return False, f"Max trades per day ({self.max_trades_per_day}) reached"
        
        # Check if we already have an open trade in same direction
        open_trades = self.paper_engine.get_open_trades()
        if open_trades:
            current_signal = signal.get('signal', '')
            for trade in open_trades:
                if 'BUY' in current_signal and trade['trade_type'] == 'BUY':
                    return False, "Already have an open BUY trade"
                if 'SELL' in current_signal and trade['trade_type'] == 'SELL':
                    return False, "Already have an open SELL trade"
        
        # Prevent rapid consecutive trades (minimum 5 min between trades)
        if self._last_trade_time:
            time_since_last = datetime.now() - self._last_trade_time
            if time_since_last < timedelta(minutes=5):
                return False, "Too soon after last trade (cooldown: 5 min)"
        
        # Prevent trading same signal repeatedly
        signal_key = f"{signal.get('signal')}_{signal.get('score', 0)}"
        if signal_key == self._last_signal:
            return False, "Same signal as last trade"
        
        return True, "Trade conditions met"
    
    def execute_trade(self, signal: Dict) -> Optional[Dict]:
        """
        Execute a trade based on signal.
        
        Args:
            signal: Signal data from analyzer
            
        Returns:
            Trade details or None
        """
        try:
            if self.mode == TradingMode.PAPER:
                # Paper trade
                trade = self.paper_engine.open_trade(signal, quantity=self.quantity)
                
                trade_data = {
                    'id': trade.id,
                    'mode': 'PAPER',
                    'symbol': trade.symbol,
                    'type': trade.trade_type,
                    'entry_price': trade.entry_price,
                    'stop_loss': trade.stop_loss,
                    'target': trade.target,
                    'quantity': trade.quantity,
                    'time': datetime.now().isoformat()
                }
                
                self._trades_today += 1
                self._last_trade_time = datetime.now()
                self._last_signal = f"{signal.get('signal')}_{signal.get('score', 0)}"
                
                logger.info(f"AUTO TRADE: {trade.trade_type} @ ₹{trade.entry_price} (Paper)")
                self._notify('trade_executed', trade_data)
                
                self.status['trades_today'] = self._trades_today
                self.status['last_trade'] = trade_data
                
                return trade_data
                
            elif self.mode == TradingMode.LIVE:
                if not self.kite:
                    logger.error("Kite not connected for live trading")
                    return None
                
                # Live trade via Zerodha
                signal_type = signal.get('signal', '')
                transaction_type = 'BUY' if 'BUY' in signal_type else 'SELL'
                
                order_id = self.kite.place_order(
                    variety='regular',
                    exchange='NSE',
                    tradingsymbol='NIFTY',
                    transaction_type=transaction_type,
                    quantity=self.quantity,
                    product='MIS',
                    order_type='MARKET'
                )
                
                trade_data = {
                    'id': order_id,
                    'mode': 'LIVE',
                    'type': transaction_type,
                    'price': signal.get('price'),
                    'quantity': self.quantity,
                    'time': datetime.now().isoformat()
                }
                
                self._trades_today += 1
                self._last_trade_time = datetime.now()
                
                logger.info(f"LIVE TRADE: {transaction_type} Order ID: {order_id}")
                self._notify('trade_executed', trade_data)
                
                self.status['trades_today'] = self._trades_today
                self.status['last_trade'] = trade_data
                
                return trade_data
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            self.status['errors'].append({
                'time': datetime.now().isoformat(),
                'error': str(e)
            })
            return None
    
    def check_and_trade(self) -> Optional[Dict]:
        """
        Check current signal and execute trade if conditions are met.
        
        Returns:
            Trade data if trade was executed, None otherwise
        """
        try:
            # Get current signal
            signal = self.analyzer.generate_signals()
            
            self.status['last_check'] = datetime.now().isoformat()
            self.status['last_signal'] = {
                'signal': signal.get('signal'),
                'strength': signal.get('strength'),
                'price': signal.get('price')
            }
            
            if signal.get('error'):
                logger.warning(f"Signal error: {signal.get('error')}")
                return None
            
            # Update paper trades with current price
            if signal.get('price'):
                self.paper_engine.check_and_update_trades(signal['price'])
            
            # Check if we should trade
            should_trade, reason = self.should_trade(signal)
            
            logger.info(f"Signal: {signal.get('signal')} [{signal.get('strength')}%] - {reason}")
            
            if should_trade:
                return self.execute_trade(signal)
            
            return None
            
        except Exception as e:
            logger.error(f"Check and trade error: {e}")
            self.status['errors'].append({
                'time': datetime.now().isoformat(),
                'error': str(e)
            })
            return None
    
    def _trading_loop(self):
        """Main trading loop - runs in background thread"""
        logger.info(f"Auto trader started in {self.mode.value.upper()} mode")
        
        while self._running:
            try:
                # Reset daily counters at market open
                now = datetime.now()
                if now.hour == self.market_open_hour and now.minute == self.market_open_minute:
                    self._trades_today = 0
                    logger.info("Daily trade counter reset")
                
                # Only trade during market hours (or always for paper mode)
                if self.mode == TradingMode.PAPER or self.is_market_hours():
                    try:
                        self.check_and_trade()
                    except Exception as e:
                        logger.error(f"Error during check_and_trade: {e}")
                        self.status['errors'].append({
                            'time': datetime.now().isoformat(),
                            'error': f"Check error: {str(e)}"
                        })
                else:
                    logger.debug("Outside market hours, skipping check")
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Trading loop iteration error: {e}")
                time.sleep(min(60, self.check_interval))  # Wait a bit on error before retrying
    
    def start(self):
        """Start automatic trading"""
        if self._running:
            logger.warning("Auto trader already running")
            return False
        
        self._running = True
        self.status['is_running'] = True
        
        self._thread = threading.Thread(target=self._trading_loop, daemon=True)
        self._thread.start()
        
        logger.info("Auto trader started")
        self._notify('started', {'mode': self.mode.value})
        
        return True
    
    def stop(self):
        """Stop automatic trading"""
        if not self._running:
            return False
        
        self._running = False
        self.status['is_running'] = False
        
        if self._thread:
            self._thread.join(timeout=5)
        
        logger.info("Auto trader stopped")
        self._notify('stopped', {})
        
        return True
    
    def get_status(self) -> Dict:
        """Get current auto trader status"""
        return {
            **self.status,
            'paper_stats': self.paper_engine.get_stats(),
            'open_trades': self.paper_engine.get_open_trades(),
            'is_market_hours': self.is_market_hours()
        }


# Singleton instance
_auto_trader: Optional[AutoTrader] = None


def get_auto_trader() -> AutoTrader:
    """Get or create the auto trader instance"""
    global _auto_trader
    if _auto_trader is None:
        _auto_trader = AutoTrader()
    return _auto_trader


if __name__ == "__main__":
    # Quick test
    print("Starting Auto Trader in PAPER mode...")
    
    trader = get_auto_trader()
    
    # Add a simple callback
    def on_trade(event, data):
        print(f"\n🔔 Event: {event}")
        print(f"   Data: {data}")
    
    trader.add_callback(on_trade)
    
    # Check once
    print("\nChecking signal...")
    result = trader.check_and_trade()
    
    if result:
        print(f"\n✅ Trade executed: {result}")
    else:
        print("\n⏸️ No trade executed")
    
    print(f"\nStatus: {trader.get_status()}")
