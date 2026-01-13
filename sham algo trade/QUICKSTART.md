# Quick Start Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Setup Configuration

### Option A: Use Setup Helper (Recommended)
```bash
python setup_helper.py
```

### Option B: Manual Setup
1. Copy `env_template.txt` to `.env`
2. Edit `.env` and fill in your credentials:
   - Zerodha API credentials from https://kite.trade/apps/
   - Twilio credentials from https://www.twilio.com/
   - Trading parameters (symbol, quantity, etc.)

## Step 3: Get Zerodha API Credentials

1. Visit https://kite.trade/apps/
2. Click "Create new app"
3. Fill in:
   - App name: "Trading Agent"
   - Redirect URL: `http://127.0.0.1:8000/callback`
4. Copy API Key and API Secret to `.env`

## Step 4: Get Twilio Credentials (for SMS/WhatsApp)

1. Sign up at https://www.twilio.com/
2. Get a phone number
3. Copy Account SID and Auth Token to `.env`
4. For WhatsApp: Enable WhatsApp Sandbox in Twilio Console

## Step 5: Run the Agent

```bash
python main.py
```

## Step 6: Authenticate

1. When prompted, visit the login URL shown
2. Login with your Zerodha credentials (email/phone)
3. After login, you'll be redirected to a URL like:
   ```
   http://127.0.0.1:8000/callback?request_token=XXXXXX&action=login&status=success
   ```
4. Copy the `request_token` value
5. Paste it in the terminal

## Step 7: Start Automated Trading

1. Choose option `2` from the menu
2. The agent will run daily at the configured time
3. You'll receive SMS and WhatsApp notifications for each trade

## Testing

Before going live:
1. Use option `1` to test a slot purchase
2. Verify notifications are working
3. Check positions with option `3`
4. Start with small quantities

## Important Notes

- ⚠️ **Test thoroughly** before using real money
- 🔒 **Keep `.env` file secure** - never share it
- 📱 **Verify notifications** are working
- 💰 **Start small** - test with minimum quantities
- 🔄 **Token expires** - you may need to re-authenticate periodically

## Troubleshooting

### "Not authenticated" error
- Run authentication again (option 5 in menu)
- Check API Key and Secret in `.env`

### Notifications not working
- Verify Twilio credentials
- Check phone number format (+country code)
- For WhatsApp, ensure number is approved in Twilio

### Order placement fails
- Check market is open (9:15 AM - 3:30 PM IST)
- Verify sufficient margin
- Check symbol format: `EXCHANGE:SYMBOL` (e.g., `NSE:SBIN`)

## Running as Background Service

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "At startup")
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\Users\PC\sham algo trade\main.py`
7. Start in: `C:\Users\PC\sham algo trade`

### Linux/Mac (systemd/cron)
Create a service file or cron job to run `python main.py` at startup.
