"""
Fully Automated Trading Bot
Runs daily without any user permission - only sends SMS/WhatsApp notifications
"""
import sys
import logging
import time
from datetime import datetime
from trading_agent import TradingAgent
from scheduler import TradingScheduler
from config import Config

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function - runs fully automated trading bot
    No user interaction required - only sends notifications
    """
    logger.info("=" * 70)
    logger.info("AUTOMATED TRADING BOT - STARTING")
    logger.info("=" * 70)
    logger.info(f"Start time: {datetime.now()}")
    logger.info(f"Daily buy time: {Config.DAILY_BUY_TIME}")
    logger.info("Mode: Fully Automated (No user permission required)")
    logger.info("-" * 70)
    
    try:
        # Initialize trading agent
        logger.info("Initializing trading agent...")
        agent = TradingAgent()
        
        # Attempt to connect (will auto-login if needed)
        logger.info("Connecting to Zerodha (auto-login if needed)...")
        if not agent.connect():
            logger.error("Failed to connect to Zerodha")
            agent.notifier.send_whatsapp(
                "❌ Trading Bot Startup Failed\n\n"
                "Could not connect to Zerodha API.\n"
                "Please check your credentials and network connection."
            )
            agent.notifier.send_sms(
                "Trading Bot: Connection failed. Check logs."
            )
            sys.exit(1)
        
        logger.info("✅ Successfully connected to Zerodha")
        
        # Send startup notification
        agent.notifier.send_whatsapp(
            f"🤖 Automated Trading Bot Started\n\n"
            f"✅ Connected to Zerodha API\n"
            f"📊 Market analysis enabled\n"
            f"⏰ Daily slot purchase scheduled for {Config.DAILY_BUY_TIME}\n"
            f"📱 You will receive notifications for all trades\n\n"
            f"Bot is running in background. No action required."
        )
        agent.notifier.send_sms(
            f"Trading Bot Started. Daily trades scheduled for {Config.DAILY_BUY_TIME}"
        )
        
        # Setup and start scheduler
        logger.info("Setting up daily scheduler...")
        scheduler = TradingScheduler()
        scheduler.agent = agent  # Use the connected agent
        scheduler.setup_daily_job()
        
        logger.info("✅ Scheduler configured")
        logger.info("=" * 70)
        logger.info("TRADING BOT IS NOW RUNNING")
        logger.info("=" * 70)
        logger.info("The bot will:")
        logger.info("  • Automatically analyze market conditions daily")
        logger.info("  • Execute trades when suitable opportunities are found")
        logger.info("  • Send SMS and WhatsApp notifications for all activities")
        logger.info("  • Run without any user permission or interaction")
        logger.info("")
        logger.info("Press Ctrl+C to stop the bot")
        logger.info("=" * 70)
        
        # Start scheduler (runs indefinitely)
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 70)
        logger.info("STOPPING TRADING BOT")
        logger.info("=" * 70)
        
        try:
            agent.notifier.send_whatsapp(
                "⏹️ Trading Bot Stopped\n\n"
                "The automated trading bot has been stopped.\n"
                "No further trades will be executed."
            )
        except:
            pass
        
        logger.info("✅ Trading bot stopped gracefully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        
        try:
            agent.notifier.send_whatsapp(
                f"❌ Trading Bot Fatal Error\n\n"
                f"Error: {str(e)}\n\n"
                f"Bot has stopped. Please check logs."
            )
            agent.notifier.send_sms(
                f"Trading Bot Error: {str(e)}"
            )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
