"""
Configuration file for Zerodha Trading Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Zerodha API Credentials
    ZERODHA_API_KEY = os.getenv('ZERODHA_API_KEY', '')
    ZERODHA_API_SECRET = os.getenv('ZERODHA_API_SECRET', '')
    ZERODHA_USER_ID = os.getenv('ZERODHA_USER_ID', '')
    ZERODHA_PASSWORD = os.getenv('ZERODHA_PASSWORD', '')
    ZERODHA_TOTP_SECRET = os.getenv('ZERODHA_TOTP_SECRET', '')
    
    # Trading Parameters
    SLOT_SYMBOL = os.getenv('SLOT_SYMBOL', 'NSE:SBIN')  # Default slot symbol
    SLOT_QUANTITY = int(os.getenv('SLOT_QUANTITY', '1'))
    SLOT_ORDER_TYPE = os.getenv('SLOT_ORDER_TYPE', 'MARKET')  # MARKET or LIMIT
    SLOT_PRODUCT = os.getenv('SLOT_PRODUCT', 'MIS')  # MIS, CNC, NRML
    
    # Market Analysis Parameters
    MIN_ANALYSIS_SCORE = int(os.getenv('MIN_ANALYSIS_SCORE', '20'))  # Minimum score to execute trade
    SYMBOLS_TO_ANALYZE = os.getenv('SYMBOLS_TO_ANALYZE', '').split(',') if os.getenv('SYMBOLS_TO_ANALYZE') else []  # List of symbols to analyze
    
    # Notification Settings
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')
    USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER', '')
    WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '')  # WhatsApp Business number
    
    # Email Settings (for notifications)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    EMAIL_USER = os.getenv('EMAIL_USER', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')
    
    # Scheduling
    DAILY_BUY_TIME = os.getenv('DAILY_BUY_TIME', '09:15')  # Market open time
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
    
    # Database (for storing login sessions)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_agent.db')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'trading_agent.log')
