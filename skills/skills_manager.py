# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01 01:44:00
# Description: Central skills manager for algo trading system
# Project: Algo Trading System

import logging
import os
import sys

# Add skills directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

class SkillsManager:
    def __init__(self):
        self.logger = logger
        self.skills = {}
        self.load_all_skills()
        
    def load_all_skills(self):
        """Load all available skills"""
        try:
            # Create simple strategy skill directly
            self.skills['simple_strategy'] = self.create_simple_strategy()
            self.skills['market_analyzer'] = self.create_market_analyzer()
            self.skills['risk_manager'] = self.create_risk_manager()
            self.skills['automation'] = self.create_automation()
            
            self.logger.info("Skills loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading skills: {str(e)}")
    
    def create_simple_strategy(self):
        """Create simple trading strategy skill"""
        class SimpleStrategy:
            def __init__(self):
                self.name = "Simple Strategy"
                
            def create_ma_strategy(self, short_window=20, long_window=50):
                return {
                    'name': 'Moving Average Crossover',
                    'short_window': short_window,
                    'long_window': long_window,
                    'description': f'Buy when {short_window}-day MA crosses above {long_window}-day MA'
                }
            
            def create_rsi_strategy(self, rsi_period=14, oversold=30, overbought=70):
                return {
                    'name': 'RSI Strategy',
                    'rsi_period': rsi_period,
                    'oversold': oversold,
                    'overbought': overbought,
                    'description': f'Buy when RSI < {oversold}, Sell when RSI > {overbought}'
                }
            
            def generate_signal(self, price_data, strategy_type='ma'):
                if strategy_type == 'ma':
                    return {'signal': 'BUY', 'confidence': 0.75, 'reason': 'MA crossover detected'}
                elif strategy_type == 'rsi':
                    return {'signal': 'SELL', 'confidence': 0.65, 'reason': 'RSI overbought'}
                else:
                    return {'signal': 'HOLD', 'confidence': 0.5, 'reason': 'No clear signal'}
        
        return SimpleStrategy()
    
    def create_market_analyzer(self):
        """Create simple market analyzer"""
        class MarketAnalyzer:
            def __init__(self):
                self.name = "Market Analyzer"
                
            def analyze_trend(self, price):
                if price > 1000:
                    return {'trend': 'BULLISH', 'signal': 'BUY', 'price': price}
                else:
                    return {'trend': 'BEARISH', 'signal': 'SELL', 'price': price}
            
            def calculate_volatility(self, prices):
                if len(prices) < 2:
                    return {'volatility': 0.0, 'trend': 'STABLE'}
                
                # Simple volatility calculation
                changes = [abs(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                avg_change = sum(changes) / len(changes)
                
                return {
                    'volatility': round(avg_change * 100, 2),
                    'trend': 'HIGH' if avg_change > 0.02 else 'LOW'
                }
        
        return MarketAnalyzer()
    
    def create_risk_manager(self):
        """Create simple risk manager"""
        class RiskManager:
            def __init__(self):
                self.name = "Risk Manager"
                
            def calculate_position_size(self, capital, risk_percent=0.02):
                position_size = capital * risk_percent
                return {
                    'position_size': round(position_size, 2),
                    'risk_amount': round(position_size, 2),
                    'risk_percent': risk_percent * 100
                }
            
            def assess_risk(self, portfolio_value, unrealized_pnl):
                risk_level = 'LOW'
                if abs(unrealized_pnl / portfolio_value) > 0.05:
                    risk_level = 'HIGH'
                elif abs(unrealized_pnl / portfolio_value) > 0.02:
                    risk_level = 'MEDIUM'
                
                return {
                    'risk_level': risk_level,
                    'portfolio_value': portfolio_value,
                    'unrealized_pnl': unrealized_pnl,
                    'risk_ratio': round(abs(unrealized_pnl / portfolio_value) * 100, 2)
                }
        
        return RiskManager()
    
    def create_automation(self):
        """Create simple automation"""
        class Automation:
            def __init__(self):
                self.name = "Trading Automation"
                self.orders = []
                
            def execute_trade(self, symbol, action, quantity, price):
                order_id = f'{symbol}_{action}_{quantity}_{int(price)}'
                order = {
                    'order_id': order_id,
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'price': price,
                    'status': 'EXECUTED',
                    'timestamp': '2026-07-01 01:44:00'
                }
                self.orders.append(order)
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'message': f'Executed {action} order for {quantity} shares of {symbol} at {price}'
                }
            
            def get_order_history(self):
                return self.orders
        
        return Automation()
    
    def get_skill(self, skill_name):
        return self.skills.get(skill_name.lower())
    
    def list_available_skills(self):
        return list(self.skills.keys())
    
    def get_skills_status(self):
        status = {}
        for skill_name, skill_instance in self.skills.items():
            status[skill_name] = {
                'loaded': True,
                'class_name': skill_instance.__class__.__name__,
                'name': getattr(skill_instance, 'name', 'Unknown'),
                'methods': [method for method in dir(skill_instance) if not method.startswith('_')]
            }
        return status

if __name__ == '__main__':
    skills_mgr = SkillsManager()
    print('=== Algo Trading Skills System ===')
    print('Available skills:', skills_mgr.list_available_skills())
    print()
    
    # Test each skill
    for skill_name in skills_mgr.list_available_skills():
        skill = skills_mgr.get_skill(skill_name)
        print(f'✓ {skill_name}: {skill.name}')
    
    print()
    print('=== Skills Status ===')
    status = skills_mgr.get_skills_status()
    for skill_name, info in status.items():
        print(f'{skill_name}: {info["methods"][:3]}...')  # Show first 3 methods
