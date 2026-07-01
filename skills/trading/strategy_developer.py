# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01 01:35:00
# Description: Trading strategy development and backtesting skill
# Project: Algo Trading System

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

class TradingStrategyDeveloper:
    def __init__(self):
        self.logger = logger
        self.strategies = {}
        
    def create_moving_average_strategy(self, short_window=20, long_window=50):
        strategy_code = f'''
def moving_average_strategy(data, short_window={short_window}, long_window={long_window}):
    data["MA_short"] = data["close"].rolling(window=short_window).mean()
    data["MA_long"] = data["close"].rolling(window=long_window).mean()
    data["signal"] = 0
    data.loc[data["MA_short"] > data["MA_long"], "signal"] = 1
    data.loc[data["MA_short"] < data["MA_long"], "signal"] = -1
    return data
'''
        return {
            'name': 'Moving Average Crossover',
            'type': 'technical',
            'parameters': {'short_window': short_window, 'long_window': long_window},
            'code': strategy_code
        }
    
    def create_rsi_strategy(self, rsi_period=14, oversold=30, overbought=70):
        strategy_code = f'''
def rsi_strategy(data, rsi_period={rsi_period}, oversold={oversold}, overbought={overbought}):
    delta = data["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))
    data["signal"] = 0
    data.loc[data["RSI"] < oversold, "signal"] = 1
    data.loc[data["RSI"] > overbought, "signal"] = -1
    return data
'''
        return {
            'name': 'RSI Mean Reversion',
            'type': 'technical',
            'parameters': {'rsi_period': rsi_period, 'oversold': oversold, 'overbought': overbought},
            'code': strategy_code
        }
    
    def backtest_strategy(self, strategy_data, initial_capital=10000):
        try:
            strategy_data['returns'] = strategy_data['close'].pct_change()
            strategy_data['strategy_returns'] = strategy_data['returns'] * strategy_data['signal'].shift(1)
            strategy_data['cumulative_returns'] = (1 + strategy_data['strategy_returns']).cumprod()
            strategy_data['portfolio_value'] = initial_capital * strategy_data['cumulative_returns']
            
            total_return = (strategy_data['portfolio_value'].iloc[-1] / initial_capital - 1) * 100
            sharpe_ratio = strategy_data['strategy_returns'].mean() / strategy_data['strategy_returns'].std() * np.sqrt(252)
            max_drawdown = (strategy_data['portfolio_value'].cummax() - strategy_data['portfolio_value']).max() / strategy_data['portfolio_value'].cummax().max() * 100
            
            winning_trades = strategy_data[strategy_data['strategy_returns'] > 0]['strategy_returns'].count()
            total_trades = strategy_data[strategy_data['strategy_returns'] != 0]['strategy_returns'].count()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'total_return': round(total_return, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'final_portfolio_value': round(strategy_data['portfolio_value'].iloc[-1], 2),
                'total_trades': int(total_trades)
            }
        except Exception as e:
            self.logger.error("Backtesting error: %s", str(e))
            return {'error': str(e)}

if __name__ == "__main__":
    strategy_dev = TradingStrategyDeveloper()
    ma_strategy = strategy_dev.create_moving_average_strategy(20, 50)
    print(f"Created strategy: {ma_strategy['name']}")
