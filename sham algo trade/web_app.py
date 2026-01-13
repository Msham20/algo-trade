"""
Web Application for Automated Trading Bot
Provides web interface to monitor and control the trading bot
"""
import os
import json
import logging
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from trading_agent import TradingAgent
from scheduler import TradingScheduler
from market_analyzer import MarketAnalyzer
from config import Config
from nifty_signal_analyzer import NiftySignalAnalyzer, get_analyzer
from paper_trading import get_paper_engine
from auto_trader import get_auto_trader

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global bot instance
trading_agent = None
scheduler = None
bot_status = {
    'is_running': False,
    'is_connected': False,
    'last_activity': None,
    'last_trade': None,
    'last_analysis': None,
    'errors': [],
    'auto_logs': []
}

def add_auto_log(message, type='info'):
    """Add a message to the auto-trading logs"""
    log_entry = {
        'time': datetime.now().strftime('%H:%M:%S'),
        'message': message,
        'type': type
    }
    bot_status['auto_logs'].append(log_entry)
    # Keep last 50 logs
    if len(bot_status['auto_logs']) > 50:
        bot_status['auto_logs'].pop(0)

def on_auto_trade(event, data):
    """Callback for auto-trader events"""
    if event == 'trade_executed':
        msg = f"🚀 Auto Trade: {data['type']} {data.get('symbol', 'NIFTY')} @ ₹{data.get('entry_price', data.get('price'))}"
        add_auto_log(msg, 'success')
        
        # Send notifications using TradingAgent's notifier
        global trading_agent
        if trading_agent and trading_agent.notifier:
            try:
                # Format notification message
                notify_msg = f"🤖 Automated Trade Executed\n\n" \
                             f"Type: {data['type']}\n" \
                             f"Price: ₹{data.get('entry_price', data.get('price'))}\n" \
                             f"Quantity: {data.get('quantity')}\n" \
                             f"Mode: {data.get('mode')}\n" \
                             f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                trading_agent.notifier.send_whatsapp(notify_msg)
                trading_agent.notifier.send_sms(f"Auto Trade: {data['type']} @ {data.get('entry_price', data.get('price'))}")
            except Exception as e:
                logger.error(f"Failed to send trade notification: {e}")
    
    elif event == 'started':
        add_auto_log(f"🤖 Auto Trader started in {data['mode'].upper()} mode", 'info')
    elif event == 'stopped':
        add_auto_log("⏹️ Auto Trader stopped", 'warning')

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current bot status"""
    global trading_agent, scheduler
    
    status = bot_status.copy()
    
    if trading_agent:
        status['is_connected'] = trading_agent.is_connected
        if trading_agent.kite:
            try:
                profile = trading_agent.kite.profile()
                status['user_name'] = profile.get('user_name', 'N/A')
                status['email'] = profile.get('email', 'N/A')
            except:
                pass
    
    if scheduler:
        status['is_running'] = scheduler.running
    
    return jsonify(status)

@app.route('/api/start', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    global trading_agent, scheduler
    
    try:
        if scheduler and scheduler.running:
            return jsonify({'success': False, 'message': 'Bot is already running'})
        
        # Initialize agent
        trading_agent = TradingAgent()
        
        # Connect
        if not trading_agent.connect():
            return jsonify({'success': False, 'message': 'Failed to connect to Zerodha'})
        
        # Initialize scheduler
        scheduler = TradingScheduler()
        scheduler.agent = trading_agent
        scheduler.setup_daily_job()
        
        # Start scheduler in background thread
        def run_scheduler():
            scheduler.start()
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        bot_status['is_running'] = True
        bot_status['is_connected'] = True
        bot_status['last_activity'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'Trading bot started successfully',
            'status': bot_status
        })
        
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        bot_status['errors'].append({
            'time': datetime.now().isoformat(),
            'error': str(e)
        })
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    global scheduler
    
    try:
        if scheduler:
            scheduler.stop()
        
        bot_status['is_running'] = False
        bot_status['last_activity'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'Trading bot stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping bot: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to Zerodha"""
    global trading_agent
    
    try:
        if not trading_agent:
            trading_agent = TradingAgent()
        
        if trading_agent.connect():
            bot_status['is_connected'] = True
            bot_status['last_activity'] = datetime.now().isoformat()
            return jsonify({
                'success': True,
                'message': 'Connected to Zerodha successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect to Zerodha'
            })
            
    except Exception as e:
        logger.error(f"Error connecting: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/analyze', methods=['POST'])
def analyze_market():
    """Analyze market for a symbol"""
    global trading_agent
    
    try:
        data = request.get_json()
        symbol = data.get('symbol', Config.SLOT_SYMBOL)
        
        if not trading_agent or not trading_agent.is_connected:
            return jsonify({
                'success': False,
                'message': 'Not connected to Zerodha'
            })
        
        if not trading_agent.analyzer:
            trading_agent.analyzer = MarketAnalyzer(trading_agent.kite)
        
        analysis = trading_agent.analyzer.analyze_symbol(symbol)
        
        bot_status['last_analysis'] = {
            'time': datetime.now().isoformat(),
            'symbol': symbol,
            'analysis': analysis
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing market: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/trade/execute', methods=['POST'])
def execute_trade():
    """Execute a trade manually"""
    global trading_agent
    
    try:
        if not trading_agent or not trading_agent.is_connected:
            return jsonify({
                'success': False,
                'message': 'Not connected to Zerodha'
            })
        
        data = request.get_json()
        use_analysis = data.get('use_analysis', True)
        
        if use_analysis:
            order_id = trading_agent.analyze_and_buy_slot()
        else:
            order_id = trading_agent.buy_slot()
        
        if order_id:
            bot_status['last_trade'] = {
                'time': datetime.now().isoformat(),
                'order_id': order_id
            }
            bot_status['last_activity'] = datetime.now().isoformat()
            
            return jsonify({
                'success': True,
                'message': 'Trade executed successfully',
                'order_id': order_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Trade execution failed or no suitable opportunity found'
            })
            
    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/positions')
def get_positions():
    """Get current positions"""
    global trading_agent
    
    try:
        if not trading_agent or not trading_agent.is_connected:
            return jsonify({'success': False, 'positions': []})
        
        positions = trading_agent.get_positions()
        return jsonify({
            'success': True,
            'positions': positions
        })
        
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/margins')
def get_margins():
    """Get available margins"""
    global trading_agent
    
    try:
        if not trading_agent or not trading_agent.is_connected:
            return jsonify({'success': False, 'margins': None})
        
        margins = trading_agent.get_margins()
        return jsonify({
            'success': True,
            'margins': margins
        })
        
    except Exception as e:
        logger.error(f"Error getting margins: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    return jsonify({
        'success': True,
        'config': {
            'daily_buy_time': Config.DAILY_BUY_TIME,
            'slot_symbol': Config.SLOT_SYMBOL,
            'slot_quantity': Config.SLOT_QUANTITY,
            'min_analysis_score': Config.MIN_ANALYSIS_SCORE,
            'symbols_to_analyze': Config.SYMBOLS_TO_ANALYZE
        }
    })

@app.route('/api/logs')
def get_logs():
    """Get recent logs"""
    try:
        log_file = Config.LOG_FILE
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Return last 100 lines
                recent_logs = lines[-100:] if len(lines) > 100 else lines
                return jsonify({
                    'success': True,
                    'logs': ''.join(recent_logs)
                })
        else:
            return jsonify({
                'success': True,
                'logs': 'No logs available yet'
            })
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

# ==================== NIFTY SIGNAL ROUTES ====================

@app.route('/nifty')
def nifty_dashboard():
    """NIFTY 5-min signal analyzer dashboard"""
    return render_template('nifty_signals.html')

@app.route('/api/nifty/signals')
def get_nifty_signals():
    """Get current NIFTY signals and analysis"""
    try:
        analyzer = get_analyzer()
        
        # If we have a connected trading agent, use its Kite connection
        if trading_agent and trading_agent.is_connected:
            analyzer.kite = trading_agent.kite
        
        signals = analyzer.generate_signals()
        
        # Update paper trades with current price
        paper_engine = get_paper_engine()
        if signals.get('price'):
            paper_engine.check_and_update_trades(signals['price'])
        
        return jsonify(signals)
        
    except Exception as e:
        logger.error(f"Error getting NIFTY signals: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/nifty/chart-data')
def get_nifty_chart_data():
    """Get NIFTY 5-min OHLC data for charting"""
    try:
        days = request.args.get('days', 2, type=int)
        days = min(days, 5)  # Max 5 days
        
        analyzer = get_analyzer()
        
        if trading_agent and trading_agent.is_connected:
            analyzer.kite = trading_agent.kite
        
        chart_data = analyzer.get_chart_data(days=days)
        return jsonify(chart_data)
        
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({'error': str(e), 'candles': []})

@app.route('/api/nifty/analysis')
def get_nifty_full_analysis():
    """Get full NIFTY analysis report"""
    try:
        analyzer = get_analyzer()
        
        if trading_agent and trading_agent.is_connected:
            analyzer.kite = trading_agent.kite
        
        signals = analyzer.generate_signals()
        chart_data = analyzer.get_chart_data(days=2)
        
        return jsonify({
            'signals': signals,
            'chart_data': chart_data
        })
        
    except Exception as e:
        logger.error(f"Error getting full analysis: {str(e)}")
        return jsonify({'error': str(e)})

# ==================== PAPER TRADING ROUTES ====================

@app.route('/api/paper/trade', methods=['POST'])
def paper_trade():
    """Execute a paper trade based on current signal"""
    try:
        data = request.get_json() or {}
        quantity = data.get('quantity', 50)
        
        analyzer = get_analyzer()
        signals = analyzer.generate_signals()
        
        if signals.get('error'):
            return jsonify({'success': False, 'message': signals['error']})
        
        if signals['signal'] == 'HOLD':
            return jsonify({
                'success': False, 
                'message': 'Current signal is HOLD - no trade recommended'
            })
        
        paper_engine = get_paper_engine()
        trade = paper_engine.open_trade(signals, quantity=quantity)
        
        return jsonify({
            'success': True,
            'message': f"Paper trade opened: {trade.trade_type} @ ₹{trade.entry_price}",
            'trade': {
                'id': trade.id,
                'symbol': trade.symbol,
                'type': trade.trade_type,
                'entry_price': trade.entry_price,
                'stop_loss': trade.stop_loss,
                'target': trade.target,
                'quantity': trade.quantity
            }
        })
        
    except Exception as e:
        logger.error(f"Error executing paper trade: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/paper/close', methods=['POST'])
def close_paper_trade():
    """Close a paper trade"""
    try:
        data = request.get_json()
        trade_id = data.get('trade_id')
        
        if not trade_id:
            return jsonify({'success': False, 'message': 'trade_id required'})
        
        # Get current price
        analyzer = get_analyzer()
        signals = analyzer.generate_signals()
        current_price = signals.get('price', 0)
        
        paper_engine = get_paper_engine()
        trade = paper_engine.close_trade(trade_id, current_price, reason="MANUAL")
        
        if trade:
            return jsonify({
                'success': True,
                'message': f"Trade closed with P&L: ₹{trade.pnl:.2f}",
                'trade': {
                    'id': trade.id,
                    'pnl': trade.pnl,
                    'exit_price': trade.exit_price,
                    'status': trade.status
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Trade not found'})
        
    except Exception as e:
        logger.error(f"Error closing paper trade: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/paper/trades')
def get_paper_trades():
    """Get paper trading positions and history"""
    try:
        paper_engine = get_paper_engine()
        
        return jsonify({
            'success': True,
            'open_trades': paper_engine.get_open_trades(),
            'history': paper_engine.get_trade_history(limit=20),
            'stats': paper_engine.get_stats()
        })
        
    except Exception as e:
        logger.error(f"Error getting paper trades: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/paper/stats')
def get_paper_stats():
    """Get paper trading statistics"""
    try:
        paper_engine = get_paper_engine()
        return jsonify({
            'success': True,
            'stats': paper_engine.get_stats()
        })
        
    except Exception as e:
        logger.error(f"Error getting paper stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/paper/reset', methods=['POST'])
def reset_paper_trading():
    """Reset paper trading - clear all trades"""
    try:
        paper_engine = get_paper_engine()
        paper_engine.reset()
        
        return jsonify({
            'success': True,
            'message': 'Paper trading reset successfully'
        })
        
    except Exception as e:
        logger.error(f"Error resetting paper trading: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

# ==================== AUTO TRADING ROUTES ====================

@app.route('/api/auto/start', methods=['POST'])
def start_auto_trading():
    """Start automatic trading (paper mode by default)"""
    try:
        data = request.get_json() or {}
        
        auto_trader = get_auto_trader()
        
        # Configure from request
        if 'min_strength' in data:
            auto_trader.min_signal_strength = int(data['min_strength'])
        if 'quantity' in data:
            auto_trader.quantity = int(data['quantity'])
        if 'interval' in data:
            auto_trader.check_interval = int(data['interval'])
        
        # Connect Kite if available
        if trading_agent and trading_agent.is_connected:
            auto_trader.set_kite(trading_agent.kite)
        
        # Add callback for logs and notifications
        auto_trader.add_callback(on_auto_trade)
        
        if auto_trader.start():
            return jsonify({
                'success': True,
                'message': f'Auto trading started in {auto_trader.mode.value.upper()} mode',
                'status': auto_trader.get_status()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Auto trading already running'
            })
        
    except Exception as e:
        logger.error(f"Error starting auto trading: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auto/stop', methods=['POST'])
def stop_auto_trading():
    """Stop automatic trading"""
    try:
        auto_trader = get_auto_trader()
        
        if auto_trader.stop():
            return jsonify({
                'success': True,
                'message': 'Auto trading stopped',
                'status': auto_trader.get_status()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Auto trading not running'
            })
        
    except Exception as e:
        logger.error(f"Error stopping auto trading: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auto/status')
def get_auto_status():
    """Get auto trading status"""
    try:
        auto_trader = get_auto_trader()
        return jsonify({
            'success': True,
            'status': auto_trader.get_status(),
            'auto_logs': bot_status['auto_logs']
        })
        
    except Exception as e:
        logger.error(f"Error getting auto status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auto/trade-now', methods=['POST'])
def auto_trade_now():
    """Execute a trade immediately based on current signal"""
    try:
        auto_trader = get_auto_trader()
        
        # Update analyzer with Kite if available
        if trading_agent and trading_agent.is_connected:
            auto_trader.set_kite(trading_agent.kite)
        
        result = auto_trader.check_and_trade()
        
        if result:
            return jsonify({
                'success': True,
                'message': f"Trade executed: {result['type']} @ ₹{result['entry_price']}",
                'trade': result
            })
        else:
            # Get current signal for info
            signal = auto_trader.analyzer.generate_signals()
            return jsonify({
                'success': False,
                'message': 'No trade executed - conditions not met',
                'current_signal': {
                    'signal': signal.get('signal'),
                    'strength': signal.get('strength'),
                    'price': signal.get('price')
                }
            })
        
    except Exception as e:
        logger.error(f"Error executing auto trade: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auto/settings', methods=['GET', 'POST'])
def auto_settings():
    """Get or update auto trading settings"""
    try:
        auto_trader = get_auto_trader()
        
        if request.method == 'POST':
            data = request.get_json() or {}
            
            if 'min_strength' in data:
                auto_trader.min_signal_strength = int(data['min_strength'])
            if 'quantity' in data:
                auto_trader.quantity = int(data['quantity'])
            if 'interval' in data:
                auto_trader.check_interval = int(data['interval'])
            if 'max_trades' in data:
                auto_trader.max_trades_per_day = int(data['max_trades'])
            
            return jsonify({
                'success': True,
                'message': 'Settings updated',
                'settings': {
                    'min_strength': auto_trader.min_signal_strength,
                    'quantity': auto_trader.quantity,
                    'interval': auto_trader.check_interval,
                    'max_trades': auto_trader.max_trades_per_day,
                    'mode': auto_trader.mode.value
                }
            })
        else:
            return jsonify({
                'success': True,
                'settings': {
                    'min_strength': auto_trader.min_signal_strength,
                    'quantity': auto_trader.quantity,
                    'interval': auto_trader.check_interval,
                    'max_trades': auto_trader.max_trades_per_day,
                    'mode': auto_trader.mode.value
                }
            })
        
    except Exception as e:
        logger.error(f"Error with auto settings: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/config/update', methods=['POST'])
def update_config():
    """Update Zerodha configuration in .env"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        # Validate required fields
        required = ['apiKey', 'apiSecret', 'userId', 'password']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'})

        # Update .env file
        env_path = '.env'
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
        elif os.path.exists('env_template.txt'):
            with open('env_template.txt', 'r') as f:
                lines = f.readlines()
        
        updates = {
            'ZERODHA_API_KEY': data['apiKey'],
            'ZERODHA_API_SECRET': data['apiSecret'],
            'ZERODHA_USER_ID': data['userId'],
            'ZERODHA_PASSWORD': data['password'],
            'ZERODHA_TOTP_SECRET': data.get('totpSecret', '')
        }
        
        new_lines = []
        updated_keys = set()
        
        for line in lines:
            if '=' in line:
                key = line.split('=')[0].strip()
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Add keys that weren't in the file
        for key, val in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={val}\n")
        
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
            
        # Reload Config
        import importlib
        import config
        importlib.reload(config)
        
        # Re-initialize TradingAgent with new config
        global trading_agent
        if trading_agent:
            try:
                # Update auth parameters in existing agent
                trading_agent.auth.api_key = updates['ZERODHA_API_KEY']
                trading_agent.auth.api_secret = updates['ZERODHA_API_SECRET']
                trading_agent.auth.user_id = updates['ZERODHA_USER_ID']
                trading_agent.auth.password = updates['ZERODHA_PASSWORD']
                trading_agent.auth.totp_secret = updates['ZERODHA_TOTP_SECRET']
                # Clear existing tokens to force re-auth
                trading_agent.auth.clear_token()
            except:
                trading_agent = None  # Force re-creation on next use
        
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Run the web app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)


