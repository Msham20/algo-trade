"""
Scheduler for daily automated slot purchases
"""
import schedule
import time
import logging
from datetime import datetime
from trading_agent import TradingAgent
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class TradingScheduler:
    """Schedule and execute daily trading tasks"""
    
    def __init__(self):
        self.agent = TradingAgent()
        self.running = False
    
    def setup_daily_job(self):
        """Setup daily slot purchase job"""
        buy_time = Config.DAILY_BUY_TIME
        
        schedule.every().day.at(buy_time).do(self.execute_daily_purchase)
        logger.info(f"Daily slot purchase scheduled for {buy_time}")
    
    def execute_daily_purchase(self):
        """Execute daily purchase (wrapper for agent method)"""
        logger.info("=" * 50)
        logger.info(f"Daily slot purchase triggered at {datetime.now()}")
        logger.info("=" * 50)
        
        # Ensure connected (will auto-login if needed)
        if not self.agent.is_connected:
            logger.warning("Not connected. Attempting to reconnect...")
            if not self.agent.connect():
                logger.error("Failed to reconnect. Skipping daily purchase.")
                self.agent.notifier.send_whatsapp(
                    "⚠️ Daily Purchase Skipped\n\n"
                    "Could not connect to Zerodha API.\n"
                    "The bot will retry tomorrow."
                )
                return
        
        # Execute purchase with market analysis
        self.agent.execute_daily_slot_purchase()
    
    def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("Trading scheduler started")
        logger.info(f"Waiting for scheduled time: {Config.DAILY_BUY_TIME}")
        
        # Send initial notification
        self.agent.notifier.send_whatsapp(
            f"🤖 Trading Agent Started\n\nDaily slot purchase scheduled for {Config.DAILY_BUY_TIME}\n\nAgent is running in background."
        )
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Trading scheduler stopped")
        schedule.clear()
    
    def run_once_now(self):
        """Execute purchase immediately (for testing)"""
        logger.info("Executing immediate slot purchase (test mode)")
        self.agent.execute_daily_slot_purchase()
