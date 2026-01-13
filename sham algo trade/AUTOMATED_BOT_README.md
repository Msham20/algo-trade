# Automated Trading Analysis Bot

A fully automated trading bot that analyzes the market and executes trades daily without requiring any user permission. The bot only sends SMS and WhatsApp notifications about its activities.

## Features

✅ **Fully Automated** - Runs without user permission  
✅ **Market Analysis** - Uses technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)  
✅ **Smart Trading** - Only executes trades when analysis indicates good opportunities  
✅ **Auto Login** - Automatically logs in to Zerodha API using Selenium  
✅ **Notifications** - Sends SMS and WhatsApp messages for all activities  
✅ **Daily Execution** - Automatically runs at configured time every day  

## Technical Analysis Indicators

The bot uses the following indicators to analyze market conditions:

1. **RSI (Relative Strength Index)** - Identifies overbought/oversold conditions
2. **MACD (Moving Average Convergence Divergence)** - Detects trend changes
3. **Bollinger Bands** - Identifies price volatility and potential reversals
4. **Moving Averages** - Confirms trend direction (20, 50, 200 day MAs)
5. **Volume Analysis** - Checks for unusual trading volume

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Run the setup helper to create your `.env` file:

```bash
python setup_helper.py
```

Or manually create a `.env` file with the following variables:

```env
# Zerodha API Credentials
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
ZERODHA_USER_ID=your_user_id
ZERODHA_PASSWORD=your_password
ZERODHA_TOTP_SECRET=your_totp_secret

# Trading Parameters
SLOT_SYMBOL=NSE:SBIN
SLOT_QUANTITY=1
SLOT_ORDER_TYPE=MARKET
SLOT_PRODUCT=MIS

# Twilio Credentials (for SMS/WhatsApp)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+1234567890
WHATSAPP_NUMBER=+1234567890

# Scheduling
DAILY_BUY_TIME=09:15
TIMEZONE=Asia/Kolkata
```

### 3. Get Zerodha API Credentials

1. Go to https://kite.trade/apps/
2. Create a new app or use existing one
3. Get your API Key and API Secret
4. Note your User ID and Password
5. Set up TOTP secret for 2FA

### 4. Get Twilio Credentials (for SMS/WhatsApp)

1. Sign up at https://www.twilio.com/
2. Get Account SID and Auth Token
3. Get a phone number with SMS/WhatsApp capabilities
4. Add your phone number for receiving notifications

### 5. Run the Automated Bot

```bash
python auto_trading_bot.py
```

The bot will:
- Automatically log in to Zerodha (first time may take a moment)
- Start running in the background
- Analyze market conditions daily at the configured time
- Execute trades when suitable opportunities are found
- Send notifications via SMS and WhatsApp

## How It Works

1. **Startup**: Bot automatically logs in to Zerodha API using Selenium
2. **Daily Schedule**: Bot waits for the configured daily buy time (default: 09:15)
3. **Market Analysis**: When triggered, bot analyzes market conditions using technical indicators
4. **Decision Making**: Bot calculates a score based on multiple indicators
5. **Trade Execution**: If score meets threshold (default: 20+), bot executes buy order
6. **Notifications**: Bot sends detailed SMS and WhatsApp notifications about the trade

## Trading Logic

The bot uses a scoring system:

- **Score >= 40**: STRONG_BUY - Trade executed
- **Score >= 20**: BUY - Trade executed
- **Score -20 to 20**: HOLD - No trade
- **Score < -20**: SELL/STRONG_SELL - No trade

### Scoring Factors

- RSI Analysis: +30 (oversold) to -30 (overbought)
- MACD Crossover: +25 (bullish) to -25 (bearish)
- Bollinger Bands: +20 (near lower band) to -20 (near upper band)
- Moving Averages: +15 (price above MAs) to -15 (price below MAs)
- Volume: +10 (above average volume)

## Notifications

The bot sends notifications for:

- ✅ Bot startup and connection status
- 📊 Market analysis results
- 🚀 Trade execution details
- ⚠️ Errors or issues
- ⏰ Daily status updates

## Logs

All activities are logged to:
- Console output
- `trading_agent.log` file

## Important Notes

⚠️ **Risk Warning**: This bot executes real trades with real money. Use at your own risk.

⚠️ **Testing**: Test thoroughly with small quantities before using with larger amounts.

⚠️ **Market Hours**: Bot only executes trades during market hours (09:15 - 15:30 IST).

⚠️ **Credentials**: Keep your `.env` file secure and never share it.

## Troubleshooting

### Bot won't connect to Zerodha

- Check your API credentials in `.env`
- Verify your TOTP secret is correct
- Ensure Chrome/Chromium is installed (for Selenium)

### No trades executed

- Check market analysis scores in logs
- Verify market is open
- Check available margin
- Review minimum score threshold

### Notifications not working

- Verify Twilio credentials
- Check phone number format (include country code)
- Ensure Twilio account has sufficient balance

## Stopping the Bot

Press `Ctrl+C` to stop the bot gracefully. It will send a notification before stopping.

## Support

For issues or questions, check the logs in `trading_agent.log` for detailed error messages.
