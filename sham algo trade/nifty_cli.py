#!/usr/bin/env python
"""
NIFTY Signal CLI Tool
Command-line interface for quick NIFTY 5-minute signal analysis
"""
import argparse
import sys
from datetime import datetime
from nifty_signal_analyzer import NiftySignalAnalyzer


def print_header():
    """Print CLI header"""
    print("\n" + "═" * 60)
    print("  🎯 NIFTY 5-MIN SIGNAL ANALYZER")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"))
    print("═" * 60)


def print_signal_badge(signal: str, strength: int) -> str:
    """Create colorful signal badge"""
    badges = {
        "STRONG_BUY": "🟢🟢 STRONG BUY",
        "BUY": "🟢 BUY",
        "HOLD": "⚪ HOLD",
        "SELL": "🔴 SELL",
        "STRONG_SELL": "🔴🔴 STRONG SELL"
    }
    return f"{badges.get(signal, signal)} [{strength}%]"


def print_full_analysis(result: dict):
    """Print comprehensive analysis"""
    print_header()
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return
    
    # Price and Signal
    print(f"\n  📊 NIFTY 50: ₹{result['price']:,.2f}")
    print(f"  📈 Signal: {print_signal_badge(result['signal'], result['strength'])}")
    print(f"  📉 Score: {result['score']}")
    
    # Risk Management
    print("\n" + "─" * 60)
    print("  💰 RISK MANAGEMENT")
    print("─" * 60)
    
    if result['signal'] in ['STRONG_BUY', 'BUY']:
        print(f"  🎯 Target:     ₹{result['target']:,.2f} (+{abs(result['target'] - result['price']):.2f})")
        print(f"  🛑 Stop Loss:  ₹{result['stop_loss']:,.2f} (-{abs(result['price'] - result['stop_loss']):.2f})")
    elif result['signal'] in ['STRONG_SELL', 'SELL']:
        print(f"  🎯 Target:     ₹{result['target']:,.2f} (-{abs(result['price'] - result['target']):.2f})")
        print(f"  🛑 Stop Loss:  ₹{result['stop_loss']:,.2f} (+{abs(result['stop_loss'] - result['price']):.2f})")
    else:
        print(f"  🎯 Target:     ₹{result['target']:,.2f}")
        print(f"  🛑 Stop Loss:  ₹{result['stop_loss']:,.2f}")
    
    print(f"  📐 Risk/Reward: 1:{result['risk_reward_ratio']}")
    
    # Active Signals
    print("\n" + "─" * 60)
    print("  🔔 ACTIVE SIGNALS")
    print("─" * 60)
    for signal in result['signals']:
        print(f"  {signal}")
    
    # Key Indicators
    print("\n" + "─" * 60)
    print("  📊 KEY INDICATORS")
    print("─" * 60)
    ind = result['indicators']
    print(f"  RSI:         {ind['rsi']:.1f} {'(Oversold)' if ind['rsi'] < 30 else '(Overbought)' if ind['rsi'] > 70 else ''}")
    print(f"  MACD:        {ind['macd']:.2f} (Signal: {ind['macd_signal']:.2f})")
    print(f"  EMA 9/21:    {ind['ema9']:.2f} / {ind['ema21']:.2f}")
    print(f"  SuperTrend:  {ind['supertrend']:.2f} ({ind['supertrend_direction']})")
    print(f"  VWAP:        {ind['vwap']:.2f} {'↑' if result['price'] > ind['vwap'] else '↓'}")
    print(f"  ATR:         {ind['atr']:.2f}")
    
    # Candlestick Patterns
    if result['patterns']:
        print("\n" + "─" * 60)
        print("  🕯️ CANDLESTICK PATTERNS")
        print("─" * 60)
        for pattern, detected in result['patterns'].items():
            if detected:
                pattern_name = pattern.replace('_', ' ').title()
                print(f"  ✓ {pattern_name}")
    
    # Support/Resistance
    sr = result['support_resistance']
    if sr['support'] or sr['resistance']:
        print("\n" + "─" * 60)
        print("  📍 SUPPORT & RESISTANCE")
        print("─" * 60)
        if sr['resistance']:
            print(f"  Resistance: {', '.join([f'₹{r:,.2f}' for r in sr['resistance']])}")
        if sr['support']:
            print(f"  Support:    {', '.join([f'₹{s:,.2f}' for s in sr['support']])}")
    
    print("\n" + "═" * 60)
    print(f"  Last Updated: {result['timestamp']}")
    print("═" * 60 + "\n")


def print_signals_only(result: dict):
    """Print only active signals"""
    print_header()
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return
    
    print(f"\n  📊 NIFTY: ₹{result['price']:,.2f}")
    print(f"  📈 {print_signal_badge(result['signal'], result['strength'])}")
    
    print("\n  Active Signals:")
    print("  " + "─" * 40)
    for signal in result['signals']:
        print(f"  {signal}")
    
    print()


def print_quick_summary(result: dict):
    """Print quick one-line summary"""
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    signal = result['signal']
    emoji = "🟢" if "BUY" in signal else "🔴" if "SELL" in signal else "⚪"
    
    print(f"{emoji} NIFTY ₹{result['price']:,.2f} | {signal} [{result['strength']}%] | SL: ₹{result['stop_loss']:,.2f} | TGT: ₹{result['target']:,.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="NIFTY 5-Minute Signal Analyzer - Identify profitable trades with minimum loss",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nifty_cli.py              Full analysis with all indicators
  python nifty_cli.py --signals    Show active signals only
  python nifty_cli.py --quick      One-line quick summary
  python nifty_cli.py --watch      Continuous monitoring (updates every 5 min)
        """
    )
    
    parser.add_argument('--signals', '-s', action='store_true',
                        help='Show only active signals')
    parser.add_argument('--quick', '-q', action='store_true',
                        help='Show quick one-line summary')
    parser.add_argument('--watch', '-w', action='store_true',
                        help='Continuous monitoring mode (Ctrl+C to exit)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output in JSON format')
    
    args = parser.parse_args()
    
    try:
        analyzer = NiftySignalAnalyzer()
        
        if args.watch:
            import time
            print("🔄 Monitoring NIFTY 5-min signals (Ctrl+C to exit)...")
            while True:
                result = analyzer.generate_signals()
                if args.quick:
                    print_quick_summary(result)
                else:
                    print_signals_only(result)
                time.sleep(300)  # 5 minutes
        else:
            result = analyzer.generate_signals()
            
            if args.json:
                import json
                print(json.dumps(result, indent=2))
            elif args.quick:
                print_quick_summary(result)
            elif args.signals:
                print_signals_only(result)
            else:
                print_full_analysis(result)
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
