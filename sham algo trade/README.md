# Zerodha Automated Trading Agent

An algorithmic trading agent that automatically buys slots on Zerodha daily without requiring user permission. The agent sends notifications via SMS and WhatsApp to keep you informed.

## Features

- 🤖 **Automated Trading**: Automatically buys slots daily at configured time
- 📱 **Notifications**: Sends SMS and WhatsApp messages for all trades
- 🔐 **Secure Authentication**: Login with email/phone number
- ⏰ **Scheduled Execution**: Runs daily without user intervention
- 📊 **Position Tracking**: Monitor your positions and margins
- 🔄 **Auto-retry**: Handles connection issues gracefully

## Prerequisites

1. **Zerodha Account**: Active Zerodha trading account
2. **Zerodha API Access**: 
   - Visit https://kite.trade/apps/
   - Create a new app
   - Get API Key and API Secret
3. **Twilio Account** (for SMS/WhatsApp):
   - Sign up at https://www.twilio.com/
   - Get Account SID and Auth Token
   - Configure WhatsApp Business API (optional)
4. **Python 3.8+**

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your credentials:
   - Zerodha API credentials
   - Twilio credentials (for SMS/WhatsApp)
   - Email settings (optional)
   - Trading parameters (symbol, quantity, etc.)

## Setup

### 1. Zerodha API Setup

1. Go to https://kite.trade/apps/
2. Click "Create new app"
3. Fill in app details
4. Copy API Key and API Secret to `.env` file
5. Enable TOTP in your Zerodha account settings
6. Get your TOTP secret key

### 2. Twilio Setup (SMS/WhatsApp)

1. Sign up at https://www.twilio.com/
2. Get a phone number from Twilio
3. Copy Account SID and Auth Token to `.env`
4. For WhatsApp:
   - Enable WhatsApp Sandbox or Business API
   - Add your number to approved recipients

### 3. Email Setup (Optional)

1. For Gmail, create an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App Passwords
   - Generate password for "Mail"
   - Use this password in `.env`

## Usage

### First Time Setup

1. **Run the agent**:
   ```bash
   python main.py
   ```

2. **Authenticate with Zerodha**:
   - The agent will show a login URL
   - Visit the URL and login with your Zerodha credentials
   - After login, copy the `request_token` from the redirect URL
   - Paste it in the terminal

3. **Configure trading parameters** in `.env`:
   - `SLOT_SYMBOL`: Symbol to trade (e.g., `NSE:SBIN`)
   - `SLOT_QUANTITY`: Number of shares
   - `SLOT_ORDER_TYPE`: `MARKET` or `LIMIT`
   - `SLOT_PRODUCT`: `MIS`, `CNC`, or `NRML`
   - `DAILY_BUY_TIME`: Time to execute (e.g., `09:15`)

### Daily Operation

1. **Start the scheduler**:
   ```bash
   python main.py
   ```
   - Choose option `2` to start daily automated scheduler
   - The agent will run in the background
   - It will automatically buy slots at the configured time

2. **Test before going live**:
   - Choose option `1` to test slot purchase
   - Verify notifications are working
   - Check positions with option `3`

### Running as a Service (Windows)

Create a batch file `start_agent.bat`:
```batch
@echo off
cd /d "C:\Users\PC\sham algo trade"
python main.py
pause
```

Or use Task Scheduler to run it at startup.

## Configuration

### Trading Parameters

Edit `.env` file:

```env
# What to buy
SLOT_SYMBOL=NSE:SBIN          # Exchange:Symbol
SLOT_QUANTITY=1                # Number of shares
SLOT_ORDER_TYPE=MARKET         # MARKET or LIMIT
SLOT_PRODUCT=MIS               # MIS, CNC, or NRML

# When to buy
DAILY_BUY_TIME=09:15          # HH:MM format (24-hour)
```

### Notification Settings

- **SMS**: Configured via Twilio
- **WhatsApp**: Configured via Twilio WhatsApp API
- **Email**: Optional, via SMTP

## How It Works

1. **Authentication**: 
   - Uses Zerodha Kite Connect API
   - Login with email/phone and password
   - TOTP for 2FA

2. **Scheduling**:
   - Uses `schedule` library for daily execution
   - Checks market hours before executing
   - Runs automatically without user intervention

3. **Trading**:
   - Places market/limit orders via Kite API
   - Handles order placement and tracking
   - Sends notifications after execution

4. **Notifications**:
   - SMS via Twilio
   - WhatsApp via Twilio
   - Email via SMTP (optional)

## Important Notes

⚠️ **Risk Warning**: 
- Automated trading involves financial risk
- Test thoroughly before using real money
- Start with small quantities
- Monitor your account regularly

🔒 **Security**:
- Never share your `.env` file
- Keep API keys secure
- Use strong passwords
- Enable 2FA on all accounts

📝 **Token Expiry**:
- Zerodha access tokens expire
- You may need to re-authenticate periodically
- Consider implementing token refresh logic

## Troubleshooting

### Authentication Issues
- Verify API Key and Secret are correct
- Check TOTP secret is valid
- Ensure request_token is copied correctly

### Notification Issues
- Verify Twilio credentials
- Check phone numbers are in correct format (+country code)
- For WhatsApp, ensure number is approved

### Trading Issues
- Check market is open
- Verify sufficient margin
- Check symbol format (EXCHANGE:SYMBOL)
- Review logs in `trading_agent.log`

## File Structure

```
.
├── main.py              # Main entry point
├── trading_agent.py     # Core trading logic
├── auth.py              # Authentication module
├── notifications.py     # SMS/WhatsApp/Email service
├── scheduler.py         # Daily scheduling
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create from .env.example)
└── README.md            # This file
```

## Support

For issues or questions:
1. Check logs in `trading_agent.log`
2. Verify all credentials in `.env`
3. Test each component individually

## License

This project is for educational purposes. Use at your own risk.

## Disclaimer

This software is provided as-is. Trading involves financial risk. The authors are not responsible for any losses incurred. Always test thoroughly before using with real money.
