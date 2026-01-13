"""
Main entry point to run the web application
"""
import os
import sys
from web_app import app

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("=" * 70)
    print("AUTOMATED TRADING BOT - WEB DASHBOARD")
    print("=" * 70)
    print("\nStarting web server...")
    print("Access the dashboard at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 70)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\nShutting down web server...")
        sys.exit(0)
