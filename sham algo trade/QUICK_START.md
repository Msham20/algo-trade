# Quick Start Guide - Automated Trading Bot

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Setup Configuration

Run the setup helper:

```bash
python setup_helper.py
```

Fill in:
- **Zerodha API credentials** (from https://kite.trade/apps/)
- **Twilio credentials** (from https://www.twilio.com/) for SMS/WhatsApp
- **Trading parameters** (symbols, quantity, etc.)

### Step 3: Run the Bot

```bash
python auto_trading_bot.py
```

That's it! The bot will:
- ✅ Automatically log in to Zerodha
- ✅ Run daily at configured time (default: 09:15)
- ✅ Analyze market and execute trades
- ✅ Send SMS/WhatsApp notifications

## 📋 What You Need

1. **Zerodha Account** with API access
   - API Key & Secret from https://kite.trade/apps/
   - User ID & Password
   - TOTP Secret (for 2FA)

2. **Twilio Account** (for notifications)
   - Account SID & Auth Token
   - Phone number with SMS/WhatsApp

3. **Python 3.8+** installed

4. **Chrome/Chromium** (for automated login)

## ⚙️ Configuration Options

Edit `.env` file to customize:

```env
# When to trade
DAILY_BUY_TIME=09:15

# Which stocks to analyze
SYMBOLS_TO_ANALYZE=NSE:SBIN,NSE:RELIANCE,NSE:TCS

# Minimum analysis score to trade
MIN_ANALYSIS_SCORE=20

# Trading parameters
SLOT_QUANTITY=1
SLOT_ORDER_TYPE=MARKET
SLOT_PRODUCT=MIS
```

## 🔔 Notifications

You'll receive notifications for:
- Bot startup
- Market analysis results
- Trade executions
- Errors or issues

## ⚠️ Important

- **Test first** with small quantities
- **Keep `.env` secure** - never share it
- **Monitor logs** in `trading_agent.log`
- **Check margin** before trading

## 🛑 Stop the Bot

Press `Ctrl+C` to stop gracefully.

## 📚 More Info

See `AUTOMATED_BOT_README.md` for detailed documentation.
