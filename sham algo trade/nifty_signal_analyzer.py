"""
NIFTY 5-Minute Signal Analyzer
Identifies buy/sell signals for intraday trading with minimum loss focus
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from kiteconnect import KiteConnect
except ImportError:
    KiteConnect = None

from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class SignalType(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class Signal:
    """Represents a trading signal"""
    signal_type: SignalType
    strength: int  # 0-100
    price: float
    stop_loss: float
    target: float
    reason: str
    timestamp: datetime
    indicators: Dict


class NiftySignalAnalyzer:
    """
    Analyzes NIFTY 5-minute charts for intraday signal identification.
    Focuses on profitable trades with minimum loss using multiple indicators.
    """
    
    # NIFTY 50 instrument token for Zerodha
    NIFTY_TOKEN = 256265  # NSE:NIFTY 50
    NIFTY_SYMBOL = "NIFTY 50"
    
    def __init__(self, kite: Optional['KiteConnect'] = None):
        self.kite = kite
        self.signals_history: List[Signal] = []
        self._cache = {}
        self._cache_time = None
        
    def get_5min_data(self, days: int = 5) -> pd.DataFrame:
        """
        Fetch 5-minute OHLC data for NIFTY.
        
        Args:
            days: Number of days of historical data (max 60 for 5-min)
        
        Returns:
            DataFrame with OHLC data
        """
        # Use cache if available and recent (< 1 min old)
        cache_key = f"nifty_5min_{days}"
        if cache_key in self._cache and self._cache_time:
            if (datetime.now() - self._cache_time).seconds < 60:
                return self._cache[cache_key]
        
        if self.kite is None:
            logger.warning("Kite not connected, using demo data")
            return self._generate_demo_data(days)
        
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            historical_data = self.kite.historical_data(
                instrument_token=self.NIFTY_TOKEN,
                from_date=from_date,
                to_date=to_date,
                interval="5minute"
            )
            
            if not historical_data:
                logger.warning("No data received, using demo data")
                return self._generate_demo_data(days)
            
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Cache the data
            self._cache[cache_key] = df
            self._cache_time = datetime.now()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching NIFTY data: {str(e)}")
            return self._generate_demo_data(days)
    
    def _generate_demo_data(self, days: int = 5) -> pd.DataFrame:
        """Generate demo data for testing without Zerodha connection"""
        periods = days * 75  # ~75 5-min candles per trading day
        
        # Generate realistic NIFTY-like price movement
        np.random.seed(42)
        base_price = 24500
        
        dates = pd.date_range(
            end=datetime.now(),
            periods=periods,
            freq='5min'
        )
        
        # Filter to market hours only (9:15 AM - 3:30 PM IST)
        dates = dates[
            (dates.hour > 9) | ((dates.hour == 9) & (dates.minute >= 15))
        ]
        dates = dates[
            (dates.hour < 15) | ((dates.hour == 15) & (dates.minute <= 30))
        ]
        
        # Generate price movements
        returns = np.random.normal(0, 0.0015, len(dates))
        prices = base_price * np.cumprod(1 + returns)
        
        # Create OHLC data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            volatility = np.random.uniform(0.001, 0.003)
            high = close * (1 + volatility)
            low = close * (1 - volatility)
            open_price = prices[i-1] if i > 0 else close
            volume = np.random.randint(100000, 500000)
            
            data.append({
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })
        
        df = pd.DataFrame(data, index=dates[-len(data):])
        return df
    
    # ==================== TECHNICAL INDICATORS ====================
    
    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, df: pd.DataFrame, 
                       fast: int = 12, slow: int = 26, 
                       signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_supertrend(self, df: pd.DataFrame, 
                             period: int = 10, 
                             multiplier: float = 3.0) -> Dict[str, pd.Series]:
        """
        Calculate SuperTrend indicator.
        SuperTrend is excellent for trend identification and stop-loss placement.
        """
        hl2 = (df['high'] + df['low']) / 2
        
        # Calculate ATR
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Calculate basic upper and lower bands
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)
        
        # Initialize SuperTrend columns
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        
        # Calculate SuperTrend
        for i in range(period, len(df)):
            if i == period:
                supertrend.iloc[i] = basic_upper.iloc[i]
                direction.iloc[i] = -1
                continue
            
            # Previous values
            prev_st = supertrend.iloc[i-1]
            prev_dir = direction.iloc[i-1]
            curr_close = df['close'].iloc[i]
            prev_close = df['close'].iloc[i-1]
            
            # Calculate final upper and lower bands
            if basic_upper.iloc[i] < prev_st or prev_close > prev_st:
                final_upper = basic_upper.iloc[i]
            else:
                final_upper = prev_st
            
            if basic_lower.iloc[i] > prev_st or prev_close < prev_st:
                final_lower = basic_lower.iloc[i]
            else:
                final_lower = prev_st
            
            # Determine SuperTrend value and direction
            if prev_dir == -1 and curr_close > prev_st:
                supertrend.iloc[i] = final_lower
                direction.iloc[i] = 1
            elif prev_dir == 1 and curr_close < prev_st:
                supertrend.iloc[i] = final_upper
                direction.iloc[i] = -1
            elif prev_dir == -1:
                supertrend.iloc[i] = final_upper
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = final_lower
                direction.iloc[i] = 1
        
        return {
            'supertrend': supertrend,
            'direction': direction,  # 1 = bullish, -1 = bearish
            'atr': atr
        }
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price.
        VWAP is essential for intraday trading decisions.
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap
    
    def detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        Detect key candlestick patterns for signal confirmation.
        """
        patterns = {}
        
        if len(df) < 3:
            return patterns
        
        # Get last 3 candles
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        # Calculate body and shadows for current candle
        body = abs(c3['close'] - c3['open'])
        upper_shadow = c3['high'] - max(c3['open'], c3['close'])
        lower_shadow = min(c3['open'], c3['close']) - c3['low']
        total_range = c3['high'] - c3['low']
        
        if total_range == 0:
            return patterns
        
        # Doji (small body, long shadows)
        patterns['doji'] = body < (total_range * 0.1)
        
        # Hammer (bullish reversal - small body, long lower shadow)
        patterns['hammer'] = (
            lower_shadow > (body * 2) and 
            upper_shadow < body and
            c3['close'] > c3['open']
        )
        
        # Shooting Star (bearish reversal - small body, long upper shadow)
        patterns['shooting_star'] = (
            upper_shadow > (body * 2) and 
            lower_shadow < body and
            c3['close'] < c3['open']
        )
        
        # Bullish Engulfing
        patterns['bullish_engulfing'] = (
            c2['close'] < c2['open'] and  # Previous red
            c3['close'] > c3['open'] and  # Current green
            c3['open'] < c2['close'] and  # Opens below prev close
            c3['close'] > c2['open']      # Closes above prev open
        )
        
        # Bearish Engulfing
        patterns['bearish_engulfing'] = (
            c2['close'] > c2['open'] and  # Previous green
            c3['close'] < c3['open'] and  # Current red
            c3['open'] > c2['close'] and  # Opens above prev close
            c3['close'] < c2['open']      # Closes below prev open
        )
        
        # Morning Star (bullish reversal pattern)
        patterns['morning_star'] = (
            c1['close'] < c1['open'] and  # First candle bearish
            abs(c2['close'] - c2['open']) < (c1['high'] - c1['low']) * 0.3 and  # Small body
            c3['close'] > c3['open'] and  # Third candle bullish
            c3['close'] > (c1['open'] + c1['close']) / 2  # Close above midpoint
        )
        
        # Evening Star (bearish reversal pattern)
        patterns['evening_star'] = (
            c1['close'] > c1['open'] and  # First candle bullish
            abs(c2['close'] - c2['open']) < (c1['high'] - c1['low']) * 0.3 and  # Small body
            c3['close'] < c3['open'] and  # Third candle bearish
            c3['close'] < (c1['open'] + c1['close']) / 2  # Close below midpoint
        )
        
        return patterns
    
    def calculate_support_resistance(self, df: pd.DataFrame, 
                                     lookback: int = 50) -> Dict[str, List[float]]:
        """
        Calculate support and resistance levels using pivot points and price action.
        """
        recent_df = df.tail(lookback)
        
        # Find local highs and lows
        highs = []
        lows = []
        
        for i in range(2, len(recent_df) - 2):
            # Local high
            if (recent_df['high'].iloc[i] > recent_df['high'].iloc[i-1] and
                recent_df['high'].iloc[i] > recent_df['high'].iloc[i-2] and
                recent_df['high'].iloc[i] > recent_df['high'].iloc[i+1] and
                recent_df['high'].iloc[i] > recent_df['high'].iloc[i+2]):
                highs.append(recent_df['high'].iloc[i])
            
            # Local low
            if (recent_df['low'].iloc[i] < recent_df['low'].iloc[i-1] and
                recent_df['low'].iloc[i] < recent_df['low'].iloc[i-2] and
                recent_df['low'].iloc[i] < recent_df['low'].iloc[i+1] and
                recent_df['low'].iloc[i] < recent_df['low'].iloc[i+2]):
                lows.append(recent_df['low'].iloc[i])
        
        # Cluster nearby levels
        def cluster_levels(levels: List[float], threshold: float = 20) -> List[float]:
            if not levels:
                return []
            sorted_levels = sorted(levels)
            clusters = [[sorted_levels[0]]]
            
            for level in sorted_levels[1:]:
                if level - clusters[-1][-1] < threshold:
                    clusters[-1].append(level)
                else:
                    clusters.append([level])
            
            return [sum(c) / len(c) for c in clusters]
        
        return {
            'resistance': cluster_levels(highs),
            'support': cluster_levels(lows)
        }

    def calculate_cpr(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate Central Pivot Range (CPR) and Pivot Points using previous day's data.
        """
        try:
            # Group by day to get previous day's OHLC
            df_daily = df.resample('D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last'
            }).dropna()
            
            if len(df_daily) < 1:
                return {}
                
            prev_day = df_daily.iloc[-1]
            if df.index[-1].date() == df_daily.index[-1].date() and len(df_daily) > 1:
                prev_day = df_daily.iloc[-2]
                
            h, l, c = prev_day['high'], prev_day['low'], prev_day['close']
            
            range_val = h - l
            pivot = (h + l + c) / 3
            bc = (h + l) / 2
            tc = (pivot - bc) + pivot
            
            # Standard Pivot Levels
            r1 = (2 * pivot) - l
            s1 = (2 * pivot) - h
            r2 = pivot + range_val
            s2 = pivot - range_val
            r3 = r1 + range_val
            s3 = s1 - range_val
            
            # CPR Width analysis
            cpr_width = abs(tc - bc)
            width_perc = (cpr_width / pivot) * 100
            
            return {
                'pivot': round(pivot, 2),
                'bc': round(min(bc, tc), 2),
                'tc': round(max(bc, tc), 2),
                'r1': round(r1, 2),
                's1': round(s1, 2),
                'r2': round(r2, 2),
                's2': round(s2, 2),
                'r3': round(r3, 2),
                's3': round(s3, 2),
                'width': round(cpr_width, 2),
                'width_perc': round(width_perc, 3),
                'type': 'Narrow' if width_perc < 0.1 else ('Wide' if width_perc > 0.25 else 'Average')
            }
        except Exception as e:
            logger.error(f"Error calculating CPR: {e}")
            return {}

    def calculate_fibonacci_levels(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate Fibonacci Retracement levels based on the current day's high/low.
        """
        try:
            # Get data for the current day only
            current_date = df.index[-1].date()
            today_df = df[df.index.date == current_date]
            
            if today_df.empty:
                return {}
                
            high = today_df['high'].max()
            low = today_df['low'].min()
            diff = high - low
            
            if diff == 0:
                return {}
                
            return {
                'high': round(high, 2),
                'low': round(low, 2),
                'fib_236': round(high - 0.236 * diff, 2),
                'fib_382': round(high - 0.382 * diff, 2),
                'fib_500': round(high - 0.500 * diff, 2),
                'fib_618': round(high - 0.618 * diff, 2),
                'fib_786': round(high - 0.786 * diff, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating Fibonacci: {e}")
            return {}
    
    # ==================== SIGNAL GENERATION ====================
    
    def generate_signals(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Generate comprehensive trading signals with all indicators.
        
        Returns:
            Dictionary with signal details, indicators, and recommendations
        """
        if df is None:
            df = self.get_5min_data(days=5)
        
        if df.empty or len(df) < 30:
            return {
                'error': 'Insufficient data for analysis',
                'signal': SignalType.HOLD.value,
                'strength': 0
            }
        
        # Calculate all indicators
        ema9 = self.calculate_ema(df, 9)
        ema21 = self.calculate_ema(df, 21)
        rsi = self.calculate_rsi(df)
        macd_data = self.calculate_macd(df)
        supertrend_data = self.calculate_supertrend(df)
        vwap = self.calculate_vwap(df)
        patterns = self.detect_candlestick_patterns(df)
        support_resistance = self.calculate_support_resistance(df)
        
        # Get latest values
        latest = df.iloc[-1]
        latest_close = latest['close']
        
        # Signal scoring system
        score = 0
        signals = []
        
        # EMA Crossover (9/21 for intraday)
        ema9_val = ema9.iloc[-1]
        ema21_val = ema21.iloc[-1]
        ema9_prev = ema9.iloc[-2]
        ema21_prev = ema21.iloc[-2]
        
        if ema9_val > ema21_val and ema9_prev <= ema21_prev:
            score += 20
            signals.append("🟢 EMA 9/21 Bullish Crossover")
        elif ema9_val < ema21_val and ema9_prev >= ema21_prev:
            score -= 20
            signals.append("🔴 EMA 9/21 Bearish Crossover")
        elif ema9_val > ema21_val:
            score += 10
            signals.append("📈 EMA 9 above EMA 21 (Uptrend)")
        else:
            score -= 10
            signals.append("📉 EMA 9 below EMA 21 (Downtrend)")
        
        # RSI
        rsi_val = rsi.iloc[-1]
        if rsi_val < 30:
            score += 15
            signals.append(f"🟢 RSI Oversold ({rsi_val:.1f})")
        elif rsi_val > 70:
            score -= 15
            signals.append(f"🔴 RSI Overbought ({rsi_val:.1f})")
        elif 40 < rsi_val < 60:
            score += 5
            signals.append(f"➖ RSI Neutral ({rsi_val:.1f})")
        
        # MACD
        macd_val = macd_data['macd'].iloc[-1]
        macd_signal = macd_data['signal'].iloc[-1]
        macd_hist = macd_data['histogram'].iloc[-1]
        macd_hist_prev = macd_data['histogram'].iloc[-2]
        
        if macd_val > macd_signal and macd_hist > 0:
            score += 15
            signals.append("🟢 MACD Bullish")
        elif macd_val < macd_signal and macd_hist < 0:
            score -= 15
            signals.append("🔴 MACD Bearish")
        
        # MACD histogram increasing
        if macd_hist > macd_hist_prev:
            score += 5
            signals.append("📈 MACD Momentum Increasing")
        else:
            score -= 5
            signals.append("📉 MACD Momentum Decreasing")
        
        # SuperTrend
        st_val = supertrend_data['supertrend'].iloc[-1]
        st_dir = supertrend_data['direction'].iloc[-1]
        atr_val = supertrend_data['atr'].iloc[-1]
        
        if st_dir == 1:
            score += 20
            signals.append(f"🟢 SuperTrend Bullish (Support: {st_val:.2f})")
        else:
            score -= 20
            signals.append(f"🔴 SuperTrend Bearish (Resistance: {st_val:.2f})")
        
        # VWAP
        vwap_val = vwap.iloc[-1]
        if latest_close > vwap_val:
            score += 10
            signals.append(f"🟢 Price above VWAP ({vwap_val:.2f})")
        else:
            score -= 10
            signals.append(f"🔴 Price below VWAP ({vwap_val:.2f})")
        
        # Candlestick Patterns
        if patterns.get('hammer') or patterns.get('bullish_engulfing') or patterns.get('morning_star'):
            score += 15
            pattern_name = 'Hammer' if patterns.get('hammer') else ('Bullish Engulfing' if patterns.get('bullish_engulfing') else 'Morning Star')
            signals.append(f"🟢 {pattern_name} Pattern Detected")
        
        if patterns.get('shooting_star') or patterns.get('bearish_engulfing') or patterns.get('evening_star'):
            score -= 15
            pattern_name = 'Shooting Star' if patterns.get('shooting_star') else ('Bearish Engulfing' if patterns.get('bearish_engulfing') else 'Evening Star')
            signals.append(f"🔴 {pattern_name} Pattern Detected")
        
        # CPR Strategy Logic
        cpr = self.calculate_cpr(df)
        if cpr:
            pivot = cpr['pivot']
            tc = cpr['tc']
            bc = cpr['bc']
            
            if latest_close > tc:
                score += 15
                signals.append(f"🟢 Above CPR (Bullish) - CPR {cpr['type']}")
            elif latest_close < bc:
                score -= 15
                signals.append(f"🔴 Below CPR (Bearish) - CPR {cpr['type']}")
            else:
                signals.append(f"➖ Inside CPR (Neutral/Sideways) - CPR {cpr['type']}")
                
        # Fibonacci Strategy Logic
        fib = self.calculate_fibonacci_levels(df)
        if fib:
            # Check price relative to golden ratio (0.618)
            fib618 = fib['fib_618']
            fib500 = fib['fib_500']
            
            if latest_close > fib618:
                score += 10
                signals.append(f"🟢 Above Fib 0.618 Golden Ratio ({fib618})")
            elif latest_close < fib618:
                if latest_close > fib500:
                    signals.append(f"➖ Between Fib 0.50 and 0.618")
                else:
                    score -= 5
                    signals.append(f"🔴 Below Fib 0.618 Golden Ratio")

        # Determine signal type
        if score >= 50:
            signal_type = SignalType.STRONG_BUY
        elif score >= 25:
            signal_type = SignalType.BUY
        elif score <= -50:
            signal_type = SignalType.STRONG_SELL
        elif score <= -25:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        
        # Calculate stop-loss and target based on ATR
        if signal_type in [SignalType.STRONG_BUY, SignalType.BUY]:
            stop_loss = latest_close - (atr_val * 1.5)
            target = latest_close + (atr_val * 2.5)  # 1:1.67 risk-reward
        elif signal_type in [SignalType.STRONG_SELL, SignalType.SELL]:
            stop_loss = latest_close + (atr_val * 1.5)
            target = latest_close - (atr_val * 2.5)
        else:
            stop_loss = latest_close - (atr_val * 1.5)
            target = latest_close + (atr_val * 1.5)
        
        # Risk-Reward calculation
        risk = abs(latest_close - stop_loss)
        reward = abs(target - latest_close)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        result = {
            'symbol': self.NIFTY_SYMBOL,
            'price': round(latest_close, 2),
            'signal': signal_type.value,
            'strength': min(100, abs(score)),
            'score': score,
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'signals': signals,
            'indicators': {
                'ema9': round(ema9_val, 2),
                'ema21': round(ema21_val, 2),
                'rsi': round(rsi_val, 2),
                'macd': round(macd_val, 2),
                'macd_signal': round(macd_signal, 2),
                'macd_histogram': round(macd_hist, 2),
                'supertrend': round(st_val, 2),
                'supertrend_direction': 'BULLISH' if st_dir == 1 else 'BEARISH',
                'vwap': round(vwap_val, 2),
                'atr': round(atr_val, 2)
            },
            'patterns': {k: bool(v) for k, v in patterns.items() if v},
            'support_resistance': {
                'support': [round(s, 2) for s in support_resistance['support'][-3:]],
                'resistance': [round(r, 2) for r in support_resistance['resistance'][-3:]]
            },
            'cpr': cpr,
            'fibonacci': fib,
            'timestamp': datetime.now().isoformat(),
            'timeframe': '5min'
        }
        
        return result
    
    def get_chart_data(self, days: int = 2) -> Dict:
        """
        Get chart data formatted for frontend visualization.
        
        Returns:
            Dictionary with OHLC data and indicator overlays
        """
        df = self.get_5min_data(days=days)
        
        if df.empty:
            return {'error': 'No data available', 'candles': []}
        
        # Calculate indicators
        ema9 = self.calculate_ema(df, 9)
        ema21 = self.calculate_ema(df, 21)
        supertrend_data = self.calculate_supertrend(df)
        vwap = self.calculate_vwap(df)
        
        # Format candle data
        candles = []
        for i, (date, row) in enumerate(df.iterrows()):
            candle = {
                'time': int(date.timestamp()),
                'open': round(row['open'], 2),
                'high': round(row['high'], 2),
                'low': round(row['low'], 2),
                'close': round(row['close'], 2),
                'volume': int(row['volume'])
            }
            candles.append(candle)
        
        # Format indicator data
        indicators = {
            'ema9': [{'time': int(d.timestamp()), 'value': round(v, 2)} 
                     for d, v in ema9.dropna().items()],
            'ema21': [{'time': int(d.timestamp()), 'value': round(v, 2)} 
                      for d, v in ema21.dropna().items()],
            'supertrend': [{'time': int(d.timestamp()), 'value': round(v, 2)} 
                           for d, v in supertrend_data['supertrend'].dropna().items()],
            'vwap': [{'time': int(d.timestamp()), 'value': round(v, 2)} 
                     for d, v in vwap.dropna().items()]
        }
        
        # Add CPR levels as horizontal lines (last day only)
        cpr = self.calculate_cpr(df)
        if cpr:
            indicators['cpr'] = {
                'pivot': cpr['pivot'],
                'tc': cpr['tc'],
                'bc': cpr['bc'],
                'r1': cpr['r1'],
                's1': cpr['s1'],
                'r2': cpr['r2'],
                's2': cpr['s2'],
                'r3': cpr['r3'],
                's3': cpr['s3']
            }
            
        # Add Fibonacci levels
        fib = self.calculate_fibonacci_levels(df)
        if fib:
            indicators['fibonacci'] = fib
        
        return {
            'candles': candles,
            'indicators': indicators,
            'last_updated': datetime.now().isoformat()
        }


# Singleton instance for use across the application
_analyzer_instance: Optional[NiftySignalAnalyzer] = None


def get_analyzer(kite: Optional['KiteConnect'] = None) -> NiftySignalAnalyzer:
    """Get or create the signal analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = NiftySignalAnalyzer(kite)
    elif kite is not None and _analyzer_instance.kite is None:
        _analyzer_instance.kite = kite
    return _analyzer_instance


if __name__ == "__main__":
    # Quick test
    analyzer = NiftySignalAnalyzer()
    signals = analyzer.generate_signals()
    
    print("\n" + "="*60)
    print("NIFTY 5-MIN SIGNAL ANALYSIS")
    print("="*60)
    print(f"Price: ₹{signals['price']}")
    print(f"Signal: {signals['signal']} (Strength: {signals['strength']}%)")
    print(f"Stop Loss: ₹{signals['stop_loss']}")
    print(f"Target: ₹{signals['target']}")
    print(f"Risk/Reward: 1:{signals['risk_reward_ratio']}")
    print("\nSignals:")
    for s in signals['signals']:
        print(f"  {s}")
    print("\nIndicators:")
    for k, v in signals['indicators'].items():
        print(f"  {k}: {v}")
