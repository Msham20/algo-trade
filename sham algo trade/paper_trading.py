"""
Paper Trading Module
Simulates trades without real money for testing signal accuracy
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

PAPER_TRADES_FILE = "paper_trades.json"


@dataclass
class PaperTrade:
    """Represents a paper trade"""
    id: str
    symbol: str
    entry_price: float
    quantity: int
    trade_type: str  # BUY or SELL
    stop_loss: float
    target: float
    entry_time: str
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    pnl: Optional[float] = None
    status: str = "OPEN"  # OPEN, CLOSED, STOPPED_OUT, TARGET_HIT
    signal_strength: int = 0
    indicators: Dict = None
    
    def __post_init__(self):
        if self.indicators is None:
            self.indicators = {}


class PaperTradingEngine:
    """
    Paper trading engine for testing signals without real money.
    Tracks virtual trades, calculates P&L, and measures signal accuracy.
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades: List[PaperTrade] = []
        self.open_trades: List[PaperTrade] = []
        self._load_trades()
    
    def _load_trades(self):
        """Load saved trades from file"""
        if os.path.exists(PAPER_TRADES_FILE):
            try:
                with open(PAPER_TRADES_FILE, 'r') as f:
                    data = json.load(f)
                    self.trades = [PaperTrade(**t) for t in data.get('trades', [])]
                    self.capital = data.get('capital', self.initial_capital)
                    self.open_trades = [t for t in self.trades if t.status == "OPEN"]
                    logger.info(f"Loaded {len(self.trades)} paper trades")
            except Exception as e:
                logger.error(f"Error loading trades: {e}")
                self.trades = []
                self.open_trades = []
    
    def _save_trades(self):
        """Save trades to file"""
        try:
            data = {
                'capital': self.capital,
                'trades': [asdict(t) for t in self.trades]
            }
            with open(PAPER_TRADES_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trades: {e}")
    
    def open_trade(self, signal: Dict, quantity: int = 1) -> PaperTrade:
        """
        Open a new paper trade based on signal.
        
        Args:
            signal: Signal data from NiftySignalAnalyzer
            quantity: Number of units to trade
        
        Returns:
            PaperTrade object
        """
        trade_type = "BUY" if signal['signal'] in ['STRONG_BUY', 'BUY'] else "SELL"
        
        trade = PaperTrade(
            id=f"PT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            symbol=signal.get('symbol', 'NIFTY 50'),
            entry_price=signal['price'],
            quantity=quantity,
            trade_type=trade_type,
            stop_loss=signal['stop_loss'],
            target=signal['target'],
            entry_time=datetime.now().isoformat(),
            signal_strength=signal.get('strength', 0),
            indicators=signal.get('indicators', {})
        )
        
        self.trades.append(trade)
        self.open_trades.append(trade)
        self._save_trades()
        
        logger.info(f"Paper trade opened: {trade.id} - {trade_type} @ ₹{trade.entry_price}")
        return trade
    
    def close_trade(self, trade_id: str, exit_price: float, reason: str = "MANUAL") -> Optional[PaperTrade]:
        """
        Close an open paper trade.
        
        Args:
            trade_id: ID of the trade to close
            exit_price: Current price to close at
            reason: Reason for closing (TARGET_HIT, STOPPED_OUT, MANUAL)
        
        Returns:
            Updated PaperTrade object or None
        """
        for trade in self.open_trades:
            if trade.id == trade_id:
                trade.exit_price = exit_price
                trade.exit_time = datetime.now().isoformat()
                trade.status = reason
                
                # Calculate P&L
                if trade.trade_type == "BUY":
                    trade.pnl = (exit_price - trade.entry_price) * trade.quantity
                else:
                    trade.pnl = (trade.entry_price - exit_price) * trade.quantity
                
                # Update capital
                self.capital += trade.pnl
                
                self.open_trades.remove(trade)
                self._save_trades()
                
                logger.info(f"Paper trade closed: {trade.id} - P&L: ₹{trade.pnl:.2f}")
                return trade
        
        return None
    
    def check_and_update_trades(self, current_price: float):
        """
        Check open trades and close if stop-loss or target hit.
        
        Args:
            current_price: Current market price
        """
        trades_to_close = []
        
        for trade in self.open_trades:
            if trade.trade_type == "BUY":
                if current_price <= trade.stop_loss:
                    trades_to_close.append((trade.id, current_price, "STOPPED_OUT"))
                elif current_price >= trade.target:
                    trades_to_close.append((trade.id, current_price, "TARGET_HIT"))
            else:  # SELL
                if current_price >= trade.stop_loss:
                    trades_to_close.append((trade.id, current_price, "STOPPED_OUT"))
                elif current_price <= trade.target:
                    trades_to_close.append((trade.id, current_price, "TARGET_HIT"))
        
        for trade_id, price, reason in trades_to_close:
            self.close_trade(trade_id, price, reason)
    
    def get_stats(self) -> Dict:
        """
        Get paper trading statistics.
        
        Returns:
            Dictionary with trading stats
        """
        closed_trades = [t for t in self.trades if t.status != "OPEN"]
        
        if not closed_trades:
            return {
                'total_trades': len(self.trades),
                'open_trades': len(self.open_trades),
                'closed_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'capital': self.capital,
                'initial_capital': self.initial_capital,
                'return_pct': 0
            }
        
        winning = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing = [t for t in closed_trades if t.pnl and t.pnl <= 0]
        total_pnl = sum(t.pnl or 0 for t in closed_trades)
        total_profit = sum(t.pnl for t in winning)
        total_loss = abs(sum(t.pnl for t in losing))
        
        # Calculate average win/loss
        avg_win = total_profit / len(winning) if winning else 0
        avg_loss = total_loss / len(losing) if losing else 0
        
        # Calculate targets hit vs stopped out
        targets_hit = len([t for t in closed_trades if t.status == "TARGET_HIT"])
        stopped_out = len([t for t in closed_trades if t.status == "STOPPED_OUT"])
        
        return {
            'total_trades': len(self.trades),
            'open_trades': len(self.open_trades),
            'closed_trades': len(closed_trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': round(len(winning) / len(closed_trades) * 100, 1) if closed_trades else 0,
            'total_pnl': round(total_pnl, 2),
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'targets_hit': targets_hit,
            'stopped_out': stopped_out,
            'capital': round(self.capital, 2),
            'initial_capital': self.initial_capital,
            'return_pct': round((self.capital - self.initial_capital) / self.initial_capital * 100, 2)
        }
    
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades as dictionaries"""
        return [asdict(t) for t in self.open_trades]
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get trade history (most recent first)"""
        sorted_trades = sorted(self.trades, key=lambda t: t.entry_time, reverse=True)
        return [asdict(t) for t in sorted_trades[:limit]]
    
    def reset(self):
        """Reset paper trading - clear all trades and reset capital"""
        self.trades = []
        self.open_trades = []
        self.capital = self.initial_capital
        self._save_trades()
        logger.info("Paper trading reset")


# Singleton instance
_paper_engine: Optional[PaperTradingEngine] = None


def get_paper_engine() -> PaperTradingEngine:
    """Get or create the paper trading engine instance"""
    global _paper_engine
    if _paper_engine is None:
        _paper_engine = PaperTradingEngine()
    return _paper_engine


if __name__ == "__main__":
    # Quick test
    engine = get_paper_engine()
    
    # Simulate a signal
    test_signal = {
        'symbol': 'NIFTY 50',
        'price': 24500,
        'signal': 'BUY',
        'strength': 65,
        'stop_loss': 24400,
        'target': 24650,
        'indicators': {'rsi': 45}
    }
    
    # Open trade
    trade = engine.open_trade(test_signal, quantity=50)
    print(f"Opened trade: {trade.id}")
    
    # Check stats
    stats = engine.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
