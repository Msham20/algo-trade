# Web Interface for Automated Trading Bot

A beautiful, modern web dashboard to monitor and control your automated trading bot.

## Features

✅ **Real-time Dashboard** - Monitor bot status, connections, and trades  
✅ **Market Analysis** - Analyze any symbol with technical indicators  
✅ **Trade Execution** - Execute trades manually from the web interface  
✅ **Position Tracking** - View current positions and margins  
✅ **Live Logs** - Monitor bot activity in real-time  
✅ **Responsive Design** - Works on desktop, tablet, and mobile  

## Quick Start

### 1. Install Dependencies

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Ensure your `.env` file is configured with:
- Zerodha API credentials
- Twilio credentials (for notifications)
- Trading parameters

### 3. Start Web Server

```bash
python run_web.py
```

### 4. Access Dashboard

Open your browser and navigate to:

```
http://localhost:5000
```

## Web Interface Features

### Control Panel

- **Connect to Zerodha**: Establish connection to Zerodha API
- **Start Bot**: Start the automated trading bot
- **Stop Bot**: Stop the bot (scheduled trades will not execute)
- **Execute Trade Now**: Manually trigger a trade with market analysis

### Status Dashboard

Real-time status cards showing:
- **Bot Status**: Whether the bot is running or stopped
- **Connection Status**: Connection to Zerodha API
- **Last Trade**: Details of the most recent trade
- **Last Analysis**: Most recent market analysis

### Market Analysis

1. Enter a symbol (e.g., `NSE:SBIN`)
2. Click "Analyze"
3. View detailed analysis including:
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Current Price
   - Analysis Score
   - Trading Signals
   - Buy/Sell/Hold Recommendation

### Positions & Margins

- **Positions**: View all open positions with details
- **Margins**: Check available cash and utilized margins
- Refresh buttons to get latest data

### Logs

View real-time logs of bot activity:
- Connection status
- Trade executions
- Market analysis results
- Errors and warnings

## API Endpoints

The web interface uses REST API endpoints:

- `GET /api/status` - Get bot status
- `POST /api/start` - Start the bot
- `POST /api/stop` - Stop the bot
- `POST /api/connect` - Connect to Zerodha
- `POST /api/analyze` - Analyze market for a symbol
- `POST /api/trade/execute` - Execute a trade
- `GET /api/positions` - Get current positions
- `GET /api/margins` - Get available margins
- `GET /api/logs` - Get recent logs
- `GET /api/config` - Get configuration

## Screenshots

The dashboard features:
- Dark theme with modern UI
- Real-time status updates (every 3 seconds)
- Toast notifications for actions
- Loading indicators
- Responsive design

## Troubleshooting

### Web server won't start

- Check if port 5000 is available
- Ensure Flask is installed: `pip install flask flask-cors`
- Check for errors in console

### Can't connect to Zerodha

- Verify credentials in `.env` file
- Check network connection
- Ensure Zerodha API is accessible

### Status not updating

- Check browser console for errors
- Verify API endpoints are responding
- Check network tab for failed requests

## Security Notes

⚠️ **Important**: The web interface runs on `0.0.0.0:5000` by default, making it accessible from any device on your network.

For production use:
1. Add authentication/authorization
2. Use HTTPS
3. Restrict access to localhost or use a reverse proxy
4. Implement rate limiting

## Customization

### Change Port

Edit `run_web.py`:

```python
app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
```

### Change Update Interval

Edit `static/js/app.js`:

```javascript
statusCheckInterval = setInterval(updateStatus, 5000); // 5 seconds
```

### Customize Theme

Edit `static/css/style.css` to change colors, fonts, and styling.

## Integration

The web interface works alongside the automated bot:
- Start the bot from the web interface
- Bot continues running in background
- Web interface shows real-time status
- Both can run simultaneously

## Support

For issues:
1. Check browser console for JavaScript errors
2. Check server logs in terminal
3. Verify `.env` configuration
4. Review `trading_agent.log` for detailed logs
