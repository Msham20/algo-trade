"""
Market Analysis Module for Trading Bot
Analyzes market conditions and identifies best trading opportunities
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from kiteconnect import KiteConnect
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Analyze market conditions and identify trading opportunities"""
    
    def __init__(self, kite: KiteConnect):
        self.kite = kite
        self.analysis_cache = {}
    
    def get_historical_data(self, instrument_token: int, interval: str = "day", 
                           days: int = 30) -> pd.DataFrame:
        """
        Get historical data for analysis
        
        Args:
            instrument_token: Zerodha instrument token
            interval: 'minute', '3minute', '5minute', '10minute', '15minute', 
                     '30minute', '60minute', 'day'
            days: Number of days of historical data
        """
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Convert to Kite format
            interval_map = {
                "minute": "minute",
                "3minute": "3minute",
                "5minute": "5minute",
                "day": "day"
            }
            
            kite_interval = interval_map.get(interval, "day")
            
            # Fetch historical data
            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=kite_interval
            )
            
            if not historical_data:
                logger.warning(f"No historical data found for token {instrument_token}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return pd.DataFrame()
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (RSI)"""
        if len(df) < period:
            return pd.Series(index=df.index, dtype=float)
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, 
                       signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(df) < slow:
            return {
                'macd': pd.Series(index=df.index, dtype=float),
                'signal': pd.Series(index=df.index, dtype=float),
                'histogram': pd.Series(index=df.index, dtype=float)
            }
        
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
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, 
                                   std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        if len(df) < period:
            return {
                'upper': pd.Series(index=df.index, dtype=float),
                'middle': pd.Series(index=df.index, dtype=float),
                'lower': pd.Series(index=df.index, dtype=float)
            }
        
        middle = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    def calculate_moving_averages(self, df: pd.DataFrame, 
                                  periods: List[int] = [20, 50, 200]) -> Dict[str, pd.Series]:
        """Calculate multiple moving averages"""
        ma_dict = {}
        for period in periods:
            if len(df) >= period:
                ma_dict[f'MA{period}'] = df['close'].rolling(window=period).mean()
            else:
                ma_dict[f'MA{period}'] = pd.Series(index=df.index, dtype=float)
        
        return ma_dict
    
    def analyze_symbol(self, symbol: str, exchange: str = "NSE") -> Dict:
        """
        Comprehensive analysis of a trading symbol
        
        Returns:
            Dictionary with analysis results and buy/sell signals
        """
        try:
            # Get instrument token
            instruments = self.kite.instruments(exchange)
            instrument = next(
                (inst for inst in instruments 
                 if inst['tradingsymbol'] == symbol.split(':')[-1] 
                 or inst['tradingsymbol'] == symbol),
                None
            )
            
            if not instrument:
                logger.error(f"Instrument not found: {symbol}")
                return {
                    'symbol': symbol,
                    'error': 'Instrument not found',
                    'recommendation': 'SKIP',
                    'score': 0
                }
            
            instrument_token = instrument['instrument_token']
            
            # Get historical data
            df = self.get_historical_data(instrument_token, interval="day", days=60)
            
            if df.empty or len(df) < 20:
                logger.warning(f"Insufficient data for {symbol}")
                return {
                    'symbol': symbol,
                    'error': 'Insufficient data',
                    'recommendation': 'SKIP',
                    'score': 0
                }
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(df)
            macd_data = self.calculate_macd(df)
            bb_data = self.calculate_bollinger_bands(df)
            ma_data = self.calculate_moving_averages(df, [20, 50, 200])
            
            # Get latest values
            latest_close = df['close'].iloc[-1]
            latest_rsi = rsi.iloc[-1] if not rsi.empty else 50
            latest_macd = macd_data['macd'].iloc[-1] if not macd_data['macd'].empty else 0
            latest_signal = macd_data['signal'].iloc[-1] if not macd_data['signal'].empty else 0
            latest_histogram = macd_data['histogram'].iloc[-1] if not macd_data['histogram'].empty else 0
            
            bb_upper = bb_data['upper'].iloc[-1] if not bb_data['upper'].empty else latest_close
            bb_lower = bb_data['lower'].iloc[-1] if not bb_data['lower'].empty else latest_close
            bb_middle = bb_data['middle'].iloc[-1] if not bb_data['middle'].empty else latest_close
            
            ma20 = ma_data.get('MA20', pd.Series()).iloc[-1] if 'MA20' in ma_data and not ma_data['MA20'].empty else latest_close
            ma50 = ma_data.get('MA50', pd.Series()).iloc[-1] if 'MA50' in ma_data and not ma_data['MA50'].empty else latest_close
            
            # Calculate buy/sell score
            score = 0
            signals = []
            
            # RSI Analysis (30-70 range is neutral, <30 oversold, >70 overbought)
            if latest_rsi < 30:
                score += 30
                signals.append("RSI: Oversold (Bullish)")
            elif latest_rsi > 70:
                score -= 30
                signals.append("RSI: Overbought (Bearish)")
            elif 40 < latest_rsi < 60:
                score += 10
                signals.append("RSI: Neutral-Bullish")
            
            # MACD Analysis
            if latest_macd > latest_signal and latest_histogram > 0:
                score += 25
                signals.append("MACD: Bullish crossover")
            elif latest_macd < latest_signal and latest_histogram < 0:
                score -= 25
                signals.append("MACD: Bearish crossover")
            
            # Bollinger Bands Analysis
            if latest_close < bb_lower:
                score += 20
                signals.append("BB: Price near lower band (Buy opportunity)")
            elif latest_close > bb_upper:
                score -= 20
                signals.append("BB: Price near upper band (Sell opportunity)")
            elif bb_lower < latest_close < bb_middle:
                score += 10
                signals.append("BB: Price in lower half (Mild bullish)")
            
            # Moving Average Analysis
            if latest_close > ma20 > ma50:
                score += 15
                signals.append("MA: Price above MAs (Bullish trend)")
            elif latest_close < ma20 < ma50:
                score -= 15
                signals.append("MA: Price below MAs (Bearish trend)")
            
            # Volume Analysis
            if len(df) > 1:
                avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
                latest_volume = df['volume'].iloc[-1]
                if latest_volume > avg_volume * 1.2:
                    score += 10
                    signals.append("Volume: Above average (Strong interest)")
            
            # Determine recommendation
            if score >= 40:
                recommendation = "STRONG_BUY"
            elif score >= 20:
                recommendation = "BUY"
            elif score >= -20:
                recommendation = "HOLD"
            elif score >= -40:
                recommendation = "SELL"
            else:
                recommendation = "STRONG_SELL"
            
            analysis_result = {
                'symbol': symbol,
                'current_price': latest_close,
                'rsi': round(latest_rsi, 2),
                'macd': round(latest_macd, 2),
                'macd_signal': round(latest_signal, 2),
                'bollinger_upper': round(bb_upper, 2),
                'bollinger_lower': round(bb_lower, 2),
                'ma20': round(ma20, 2),
                'ma50': round(ma50, 2),
                'score': score,
                'recommendation': recommendation,
                'signals': signals,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Analysis for {symbol}: {recommendation} (Score: {score})")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'recommendation': 'SKIP',
                'score': 0
            }
    
    def find_best_opportunity(self, symbols: List[str], min_score: int = 20) -> Optional[Dict]:
        """
        Analyze multiple symbols and find the best buying opportunity
        
        Args:
            symbols: List of symbols to analyze
            min_score: Minimum score required for recommendation
        
        Returns:
            Best opportunity dictionary or None
        """
        best_opportunity = None
        best_score = -float('inf')
        
        logger.info(f"Analyzing {len(symbols)} symbols for best opportunity...")
        
        for symbol in symbols:
            try:
                analysis = self.analyze_symbol(symbol)
                
                if analysis.get('recommendation') in ['BUY', 'STRONG_BUY']:
                    score = analysis.get('score', 0)
                    if score >= min_score and score > best_score:
                        best_score = score
                        best_opportunity = analysis
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
                continue
        
        if best_opportunity:
            logger.info(f"Best opportunity found: {best_opportunity['symbol']} "
                       f"with score {best_opportunity['score']}")
        else:
            logger.warning("No suitable buying opportunity found")
        
        return best_opportunity
    
    def get_market_sentiment(self) -> Dict:
        """Get overall market sentiment by analyzing Nifty 50"""
        try:
            # Analyze Nifty 50 as market indicator
            nifty_analysis = self.analyze_symbol("NSE:NIFTY 50")
            
            sentiment = "NEUTRAL"
            if nifty_analysis.get('score', 0) > 20:
                sentiment = "BULLISH"
            elif nifty_analysis.get('score', 0) < -20:
                sentiment = "BEARISH"
            
            return {
                'sentiment': sentiment,
                'nifty_score': nifty_analysis.get('score', 0),
                'nifty_price': nifty_analysis.get('current_price', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting market sentiment: {str(e)}")
            return {
                'sentiment': 'UNKNOWN',
                'error': str(e)
            }
