"""
Helper script to setup environment file
"""
import os

def create_env_file():
    """Create .env file from user input"""
    print("\n" + "=" * 60)
    print("ZERODHA TRADING AGENT - SETUP HELPER")
    print("=" * 60)
    print("\nThis script will help you create the .env configuration file.")
    print("You can skip any field by pressing Enter (you can edit .env later).\n")
    
    env_content = []
    
    # Zerodha API
    print("\n--- Zerodha API Credentials ---")
    print("Get these from https://kite.trade/apps/")
    api_key = input("ZERODHA_API_KEY: ").strip()
    api_secret = input("ZERODHA_API_SECRET: ").strip()
    user_id = input("ZERODHA_USER_ID: ").strip()
    password = input("ZERODHA_PASSWORD: ").strip()
    totp_secret = input("ZERODHA_TOTP_SECRET: ").strip()
    
    # Trading Parameters
    print("\n--- Trading Parameters ---")
    slot_symbol = input("SLOT_SYMBOL (default: NSE:SBIN): ").strip() or "NSE:SBIN"
    slot_quantity = input("SLOT_QUANTITY (default: 1): ").strip() or "1"
    slot_order_type = input("SLOT_ORDER_TYPE (default: MARKET): ").strip() or "MARKET"
    slot_product = input("SLOT_PRODUCT (default: MIS): ").strip() or "MIS"
    
    # Market Analysis Parameters
    print("\n--- Market Analysis Parameters ---")
    min_score = input("MIN_ANALYSIS_SCORE (default: 20): ").strip() or "20"
    symbols_to_analyze = input("SYMBOLS_TO_ANALYZE (comma-separated, e.g., NSE:SBIN,NSE:RELIANCE): ").strip() or ""
    
    # Twilio
    print("\n--- Twilio Credentials (for SMS/WhatsApp) ---")
    print("Get these from https://www.twilio.com/")
    twilio_sid = input("TWILIO_ACCOUNT_SID: ").strip()
    twilio_token = input("TWILIO_AUTH_TOKEN: ").strip()
    twilio_phone = input("TWILIO_PHONE_NUMBER (e.g., +1234567890): ").strip()
    user_phone = input("USER_PHONE_NUMBER (e.g., +1234567890): ").strip()
    whatsapp_num = input("WHATSAPP_NUMBER (optional): ").strip()
    
    # Email
    print("\n--- Email Settings (Optional) ---")
    smtp_server = input("SMTP_SERVER (default: smtp.gmail.com): ").strip() or "smtp.gmail.com"
    smtp_port = input("SMTP_PORT (default: 587): ").strip() or "587"
    email_user = input("EMAIL_USER: ").strip()
    email_password = input("EMAIL_PASSWORD: ").strip()
    notification_email = input("NOTIFICATION_EMAIL: ").strip()
    
    # Scheduling
    print("\n--- Scheduling ---")
    daily_buy_time = input("DAILY_BUY_TIME (default: 09:15): ").strip() or "09:15"
    timezone = input("TIMEZONE (default: Asia/Kolkata): ").strip() or "Asia/Kolkata"
    
    # Build .env content
    env_content.append("# Zerodha API Credentials")
    env_content.append(f"ZERODHA_API_KEY={api_key}")
    env_content.append(f"ZERODHA_API_SECRET={api_secret}")
    env_content.append(f"ZERODHA_USER_ID={user_id}")
    env_content.append(f"ZERODHA_PASSWORD={password}")
    env_content.append(f"ZERODHA_TOTP_SECRET={totp_secret}")
    env_content.append("")
    env_content.append("# Trading Parameters")
    env_content.append(f"SLOT_SYMBOL={slot_symbol}")
    env_content.append(f"SLOT_QUANTITY={slot_quantity}")
    env_content.append(f"SLOT_ORDER_TYPE={slot_order_type}")
    env_content.append(f"SLOT_PRODUCT={slot_product}")
    env_content.append("")
    env_content.append("# Market Analysis Parameters")
    env_content.append(f"MIN_ANALYSIS_SCORE={min_score}")
    if symbols_to_analyze:
        env_content.append(f"SYMBOLS_TO_ANALYZE={symbols_to_analyze}")
    env_content.append("")
    env_content.append("# Twilio Credentials")
    env_content.append(f"TWILIO_ACCOUNT_SID={twilio_sid}")
    env_content.append(f"TWILIO_AUTH_TOKEN={twilio_token}")
    env_content.append(f"TWILIO_PHONE_NUMBER={twilio_phone}")
    env_content.append(f"USER_PHONE_NUMBER={user_phone}")
    env_content.append(f"WHATSAPP_NUMBER={whatsapp_num}")
    env_content.append("")
    env_content.append("# Email Settings")
    env_content.append(f"SMTP_SERVER={smtp_server}")
    env_content.append(f"SMTP_PORT={smtp_port}")
    env_content.append(f"EMAIL_USER={email_user}")
    env_content.append(f"EMAIL_PASSWORD={email_password}")
    env_content.append(f"NOTIFICATION_EMAIL={notification_email}")
    env_content.append("")
    env_content.append("# Scheduling")
    env_content.append(f"DAILY_BUY_TIME={daily_buy_time}")
    env_content.append(f"TIMEZONE={timezone}")
    env_content.append("")
    env_content.append("# Logging")
    env_content.append("LOG_LEVEL=INFO")
    env_content.append("LOG_FILE=trading_agent.log")
    
    # Write to file
    env_path = ".env"
    with open(env_path, 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f"\n✅ Configuration saved to {env_path}")
    print("\n⚠️  Important: Keep this file secure and never share it!")
    print("\nNext steps:")
    print("1. Review and edit .env if needed")
    print("2. Run: python main.py")
    print("3. Follow authentication steps")

if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
