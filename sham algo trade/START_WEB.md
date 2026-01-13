# 🚀 Start Web Interface - Quick Guide

## One Command to Start

```bash
python run_web.py
```

Then open your browser to: **http://localhost:5000**

## What You'll See

### Dashboard Features

1. **Control Panel** - Buttons to:
   - Connect to Zerodha
   - Start/Stop the bot
   - Execute trades manually

2. **Status Cards** - Real-time updates showing:
   - Bot running status
   - Connection status
   - Last trade details
   - Last analysis

3. **Market Analysis** - Enter any symbol and analyze:
   - Technical indicators (RSI, MACD)
   - Buy/Sell recommendations
   - Analysis score

4. **Positions & Margins** - View:
   - Current positions
   - Available cash
   - Utilized margins

5. **Live Logs** - Monitor all bot activity

## First Time Setup

1. **Configure `.env` file** (run `python setup_helper.py` if needed)

2. **Start web server**:
   ```bash
   python run_web.py
   ```

3. **Open browser**: http://localhost:5000

4. **Click "Connect to Zerodha"** - This will auto-login

5. **Click "Start Bot"** - Bot will run daily at configured time

## Web vs Command Line

- **Web Interface**: Visual dashboard, easy monitoring, manual controls
- **Command Line** (`auto_trading_bot.py`): Fully automated, runs in background

You can use both! The web interface is great for monitoring and manual control, while the command-line bot runs automated daily trades.

## Troubleshooting

**Port 5000 already in use?**
- Change port in `run_web.py`: `port=8080`

**Can't connect?**
- Check `.env` file has correct Zerodha credentials
- Ensure Chrome/Chromium is installed (for auto-login)

**Status not updating?**
- Check browser console (F12)
- Verify API is responding

## Next Steps

- Read `WEB_INTERFACE_README.md` for detailed documentation
- Read `AUTOMATED_BOT_README.md` for bot features
- Check `QUICK_START.md` for setup guide
