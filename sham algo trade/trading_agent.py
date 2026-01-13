"""
Main Trading Agent for automated slot buying with market analysis
"""
import logging
from datetime import datetime
from kiteconnect import KiteConnect
from auth import ZerodhaAuth
from notifications import NotificationService
from market_analyzer import MarketAnalyzer
from config import Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingAgent:
    """Automated trading agent for Zerodha"""
    
    def __init__(self):
        self.auth = ZerodhaAuth()
        self.notifier = NotificationService()
        self.kite = None
        self.is_connected = False
        self.analyzer = None
    
    def connect(self):
        """Connect to Zerodha API with automated authentication"""
        try:
            # Ensure authenticated (will auto-login if needed)
            if not self.auth.ensure_authenticated():
                logger.error("Authentication failed")
                self.notifier.notify_error("Authentication failed. Please check credentials.")
                return False
            
            self.kite = self.auth.get_kite_instance()
            self.is_connected = True
            
            # Initialize market analyzer
            self.analyzer = MarketAnalyzer(self.kite)
            
            logger.info("Successfully connected to Zerodha")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            self.notifier.notify_error(f"Connection failed: {str(e)}")
            return False
    
    def analyze_and_buy_slot(self, symbols_to_analyze=None, min_score=20):
        """
        Analyze market and buy the best opportunity automatically
        
        Args:
            symbols_to_analyze: List of symbols to analyze (default: uses config symbol)
            min_score: Minimum analysis score required to buy
        """
        if not self.is_connected or not self.analyzer:
            logger.error("Not connected or analyzer not initialized")
            if not self.connect():
                return None
        
        try:
            # Get market sentiment first
            logger.info("Analyzing market sentiment...")
            sentiment = self.analyzer.get_market_sentiment()
            logger.info(f"Market sentiment: {sentiment.get('sentiment')}")
            
            # Determine symbols to analyze
            if symbols_to_analyze is None:
                # Use default symbol from config
                default_symbol = Config.SLOT_SYMBOL
                symbols_to_analyze = [default_symbol]
            
            # Find best opportunity
            logger.info(f"Analyzing {len(symbols_to_analyze)} symbol(s) for best opportunity...")
            best_opportunity = self.analyzer.find_best_opportunity(symbols_to_analyze, min_score)
            
            if not best_opportunity:
                logger.warning("No suitable buying opportunity found based on analysis")
                self.notifier.send_whatsapp(
                    f"📊 Market Analysis Complete\n\n"
                    f"No suitable buying opportunity found.\n"
                    f"Market sentiment: {sentiment.get('sentiment')}\n"
                    f"Minimum score required: {min_score}\n\n"
                    f"No trade executed."
                )
                return None
            
            # Execute buy order for best opportunity
            symbol = best_opportunity['symbol']
            quantity = Config.SLOT_QUANTITY
            order_type = Config.SLOT_ORDER_TYPE
            product = Config.SLOT_PRODUCT
            
            logger.info(f"Best opportunity: {symbol} (Score: {best_opportunity['score']})")
            logger.info(f"Analysis signals: {', '.join(best_opportunity.get('signals', []))}")
            
            # Place order
            order_id = self.buy_slot(symbol, quantity, order_type, product)
            
            if order_id:
                # Send detailed notification with analysis
                analysis_msg = f"""
📊 Automated Trade Executed - Market Analysis

Symbol: {symbol}
Recommendation: {best_opportunity['recommendation']}
Analysis Score: {best_opportunity['score']}/100

Technical Indicators:
• RSI: {best_opportunity.get('rsi', 'N/A')}
• MACD: {best_opportunity.get('macd', 'N/A')}
• Current Price: ₹{best_opportunity.get('current_price', 'N/A')}

Signals:
{chr(10).join('• ' + s for s in best_opportunity.get('signals', []))}

Order ID: {order_id}
Market Sentiment: {sentiment.get('sentiment')}

This trade was automatically executed based on market analysis.
                """.strip()
                
                self.notifier.send_whatsapp(analysis_msg)
                self.notifier.send_sms(analysis_msg)
            
            return order_id
            
        except Exception as e:
            error_msg = f"Failed to analyze and buy: {str(e)}"
            logger.error(error_msg)
            self.notifier.notify_error(error_msg)
            return None
    
    def buy_slot(self, symbol=None, quantity=None, order_type=None, product=None):
        """
        Buy a slot automatically (without analysis - direct buy)
        
        Args:
            symbol: Trading symbol (default from config)
            quantity: Quantity to buy (default from config)
            order_type: MARKET or LIMIT (default from config)
            product: MIS, CNC, or NRML (default from config)
        """
        if not self.is_connected:
            logger.error("Not connected to Zerodha. Please connect first.")
            if not self.connect():
                return None
        
        try:
            # Use config defaults if not provided
            symbol = symbol or Config.SLOT_SYMBOL
            quantity = quantity or Config.SLOT_QUANTITY
            order_type = order_type or Config.SLOT_ORDER_TYPE
            product = product or Config.SLOT_PRODUCT
            
            # Parse symbol
            if ':' in symbol:
                exchange, tradingsymbol = symbol.split(':', 1)
            else:
                exchange = "NSE"  # Default
                tradingsymbol = symbol
            
            logger.info(f"Placing buy order: {symbol}, Quantity: {quantity}, Type: {order_type}")
            
            # Place market order
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=quantity,
                order_type=order_type,
                product=product,
                validity=self.kite.VALIDITY_DAY
            )
            
            logger.info(f"Order placed successfully. Order ID: {order_id}")
            
            # Get order details
            orders = self.kite.orders()
            order_details = next((o for o in orders if o['order_id'] == order_id), None)
            
            if order_details:
                # Send notification
                self.notifier.notify_slot_purchase(order_details)
                logger.info(f"Order details: {order_details}")
            
            return order_id
            
        except Exception as e:
            error_msg = f"Failed to buy slot: {str(e)}"
            logger.error(error_msg)
            self.notifier.notify_error(error_msg)
            return None
    
    def get_market_status(self):
        """Check if market is open"""
        try:
            if not self.is_connected:
                return False
            
            # Get market status
            # Note: This is a simplified check. You may need to adjust based on actual API
            current_time = datetime.now().time()
            market_open = datetime.strptime("09:15", "%H:%M").time()
            market_close = datetime.strptime("15:30", "%H:%M").time()
            
            return market_open <= current_time <= market_close
            
        except Exception as e:
            logger.error(f"Error checking market status: {str(e)}")
            return False
    
    def get_positions(self):
        """Get current positions"""
        try:
            if not self.is_connected:
                return []
            
            positions = self.kite.positions()
            return positions.get('net', [])
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def get_margins(self):
        """Get available margins"""
        try:
            if not self.is_connected:
                return None
            
            margins = self.kite.margins()
            return margins
            
        except Exception as e:
            logger.error(f"Error getting margins: {str(e)}")
            return None
    
    def execute_daily_slot_purchase(self):
        """
        Execute daily slot purchase with market analysis (called by scheduler)
        This runs automatically without user permission
        """
        logger.info("=" * 60)
        logger.info("Executing daily automated slot purchase with market analysis...")
        logger.info("=" * 60)
        
        # Ensure connected
        if not self.is_connected:
            logger.info("Not connected. Attempting to connect...")
            if not self.connect():
                logger.error("Failed to connect. Aborting daily purchase.")
                self.notifier.send_whatsapp("❌ Daily purchase failed: Could not connect to Zerodha")
                return
        
        # Check market status
        if not self.get_market_status():
            logger.warning("Market is closed. Skipping slot purchase.")
            self.notifier.send_whatsapp("⏰ Market is closed. Slot purchase skipped for today.")
            return
        
        # Check margins
        margins = self.get_margins()
        if margins:
            equity_margin = margins.get('equity', {})
            available = equity_margin.get('available', {})
            available_cash = available.get('cash', 0)
            logger.info(f"Available margin: ₹{available_cash}")
            
            if available_cash < 1000:  # Minimum threshold
                logger.warning("Insufficient margin available")
                self.notifier.send_whatsapp(
                    f"⚠️ Insufficient margin (₹{available_cash}). Daily purchase skipped."
                )
                return
        
        # Execute buy order with market analysis
        logger.info("Starting market analysis...")
        symbols_to_analyze = Config.SYMBOLS_TO_ANALYZE if Config.SYMBOLS_TO_ANALYZE else None
        order_id = self.analyze_and_buy_slot(
            symbols_to_analyze=symbols_to_analyze,
            min_score=Config.MIN_ANALYSIS_SCORE
        )
        
        if order_id:
            logger.info(f"✅ Daily slot purchase completed. Order ID: {order_id}")
        else:
            logger.warning("Daily slot purchase did not execute (no suitable opportunity found)")
    
    def login_with_token(self, request_token):
        """Helper method to login with request token"""
        try:
            self.kite = self.auth.login_with_request_token(request_token)
            self.is_connected = True
            logger.info("Successfully logged in with request token")
            return True
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
