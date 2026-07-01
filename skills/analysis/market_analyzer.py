# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01 01:36:00
# Description: Market analysis and sentiment analysis skill
# Project: Algo Trading System

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import json

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self):
        self.logger = logger
        self.market_data = {}
        
    def analyze_market_trend(self, symbol_data, period=20):
        """Analyze market trend using technical indicators"""
        try:
            # Calculate moving averages
            symbol_data['SMA_20'] = symbol_data['close'].rolling(window=period).mean()
            symbol_data['EMA_12'] = symbol_data['close'].ewm(span=12).mean()
            symbol_data['EMA_26'] = symbol_data['close'].ewm(span=26).mean()
            
            # Calculate MACD
            symbol_data['MACD'] = symbol_data['EMA_12'] - symbol_data['EMA_26']
            symbol_data['MACD_signal'] = symbol_data['MACD'].ewm(span=9).mean()
            
            # Calculate RSI
            delta = symbol_data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            symbol_data['RSI'] = 100 - (100 / (1 + rs))
            
            # Determine trend
            current_price = symbol_data['close'].iloc[-1]
            sma_20 = symbol_data['SMA_20'].iloc[-1]
            rsi = symbol_data['RSI'].iloc[-1]
            
            if current_price > sma_20 and rsi < 70:
                trend = 'BULLISH'
            elif current_price < sma_20 and rsi > 30:
                trend = 'BEARISH'
            else:
                trend = 'SIDEWAYS'
            
            return {
                'trend': trend,
                'current_price': current_price,
                'sma_20': sma_20,
                'rsi': rsi,
                'macd': symbol_data['MACD'].iloc[-1],
                'macd_signal': symbol_data['MACD_signal'].iloc[-1]
            }
        except Exception as e:
            self.logger.error("Market trend analysis error: %s", str(e))
            return {'error': str(e)}
    
    def calculate_volatility(self, symbol_data, window=20):
        """Calculate price volatility"""
        try:
            returns = symbol_data['close'].pct_change()
            volatility = returns.rolling(window=window).std() * np.sqrt(252)
            
            return {
                'current_volatility': volatility.iloc[-1],
                'average_volatility': volatility.mean(),
                'volatility_trend': 'INCREASING' if volatility.iloc[-1] > volatility.mean() else 'DECREASING'
            }
        except Exception as e:
            self.logger.error("Volatility calculation error: %s", str(e))
            return {'error': str(e)}
    
    def generate_market_report(self, symbol, analysis_data):
        """Generate comprehensive market analysis report"""
        report = f"""
# Market Analysis Report for {symbol}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Trend Analysis
- **Current Trend**: {analysis_data.get('trend', 'N/A')}
- **Current Price**: {analysis_data.get('current_price', 'N/A'):.2f}
- **20-day SMA**: {analysis_data.get('sma_20', 'N/A'):.2f}
- **RSI**: {analysis_data.get('rsi', 'N/A'):.2f}

## Technical Indicators
- **MACD**: {analysis_data.get('macd', 'N/A'):.4f}
- **MACD Signal**: {analysis_data.get('macd_signal', 'N/A'):.4f}

## Trading Signals
"""
        
        # Add trading signals based on analysis
        rsi = analysis_data.get('rsi', 50)
        if rsi < 30:
            report += "- **Signal**: BUY (Oversold conditions)\n"
        elif rsi > 70:
            report += "- **Signal**: SELL (Overbought conditions)\n"
        else:
            report += "- **Signal**: HOLD (Neutral conditions)\n"
        
        return report

if __name__ == "__main__":
    analyzer = MarketAnalyzer()
    print("Market Analyzer skill initialized")
