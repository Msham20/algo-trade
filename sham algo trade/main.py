"""
Main entry point for Zerodha Trading Agent
"""
import sys
import logging
from trading_agent import TradingAgent
from scheduler import TradingScheduler
from auth import ZerodhaAuth
from config import Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_authentication():
    """Setup Zerodha authentication"""
    auth = ZerodhaAuth()
    
    print("\n" + "=" * 60)
    print("ZERODHA TRADING AGENT - AUTHENTICATION SETUP")
    print("=" * 60)
    print("\nTo authenticate with Zerodha:")
    print("1. Visit the login URL below")
    print("2. Login with your Zerodha credentials (email/phone)")
    print("3. After login, you'll be redirected with a request_token")
    print("4. Copy the request_token from the URL")
    print("\nLogin URL:")
    print(auth.get_login_url())
    print("\n" + "-" * 60)
    
    request_token = input("\nEnter the request_token from redirect URL: ").strip()
    
    if not request_token:
        print("Error: Request token is required")
        return None
    
    try:
        kite = auth.login_with_request_token(request_token)
        print("\n✅ Successfully authenticated with Zerodha!")
        print(f"Access Token: {kite.access_token[:20]}...")
        return kite
    except Exception as e:
        print(f"\n❌ Authentication failed: {str(e)}")
        return None

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("ZERODHA AUTOMATED TRADING AGENT")
    print("=" * 60)
    print("\nThis agent will:")
    print("• Automatically buy slots daily at configured time")
    print("• Send SMS and WhatsApp notifications")
    print("• Run without user permission (automated)")
    print("\n" + "-" * 60)
    
    # Initialize agent
    agent = TradingAgent()
    
    # Check authentication
    if not agent.auth.is_authenticated():
        print("\n⚠️  Not authenticated. Setting up authentication...")
        kite = setup_authentication()
        if not kite:
            print("\n❌ Authentication setup failed. Exiting.")
            sys.exit(1)
        agent.kite = kite
        agent.is_connected = True
    else:
        print("\n✅ Already authenticated")
        agent.connect()
    
    # Menu
    while True:
        print("\n" + "=" * 60)
        print("MENU")
        print("=" * 60)
        print("1. Execute slot purchase now (test)")
        print("2. Start daily automated scheduler")
        print("3. Check positions")
        print("4. Check margins")
        print("5. Re-authenticate")
        print("6. Exit")
        print("-" * 60)
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            print("\n🔄 Executing slot purchase...")
            order_id = agent.buy_slot()
            if order_id:
                print(f"✅ Order placed successfully. Order ID: {order_id}")
            else:
                print("❌ Order placement failed. Check logs for details.")
        
        elif choice == '2':
            print("\n🚀 Starting daily automated scheduler...")
            print(f"⏰ Slot purchase scheduled for: {Config.DAILY_BUY_TIME}")
            print("📱 You will receive notifications via SMS and WhatsApp")
            print("\n⚠️  Press Ctrl+C to stop the scheduler")
            print("-" * 60)
            
            scheduler = TradingScheduler()
            scheduler.setup_daily_job()
            try:
                scheduler.start()
            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping scheduler...")
                scheduler.stop()
                print("✅ Scheduler stopped")
        
        elif choice == '3':
            print("\n📊 Fetching positions...")
            positions = agent.get_positions()
            if positions:
                print("\nCurrent Positions:")
                for pos in positions:
                    print(f"  • {pos.get('tradingsymbol')}: {pos.get('quantity')} @ ₹{pos.get('average_price', 0)}")
            else:
                print("No open positions")
        
        elif choice == '4':
            print("\n💰 Fetching margins...")
            margins = agent.get_margins()
            if margins:
                equity = margins.get('equity', {})
                print(f"\nEquity Margins:")
                print(f"  • Available: ₹{equity.get('available', {}).get('cash', 0)}")
                print(f"  • Utilised: ₹{equity.get('utilised', {}).get('debits', 0)}")
            else:
                print("Could not fetch margins")
        
        elif choice == '5':
            print("\n🔄 Re-authenticating...")
            kite = setup_authentication()
            if kite:
                agent.kite = kite
                agent.is_connected = True
                print("✅ Re-authentication successful")
            else:
                print("❌ Re-authentication failed")
        
        elif choice == '6':
            print("\n👋 Exiting...")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
