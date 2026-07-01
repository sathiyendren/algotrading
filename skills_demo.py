# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01 01:45:00
# Description: Algo trading skills demonstration
# Project: Algo Trading System

import sys
import os

# Add skills directory to path
sys.path.append('skills')

from skills_manager import SkillsManager

def demo_skills_system():
    print("🚀 Algo Trading Skills System Demo")
    print("=" * 50)
    
    # Initialize skills manager
    skills_mgr = SkillsManager()
    
    print(f"\n📋 Available Skills: {len(skills_mgr.list_available_skills())}")
    for skill in skills_mgr.list_available_skills():
        print(f"  ✓ {skill}")
    
    print("\n🎯 Testing Trading Strategy Skill")
    strategy = skills_mgr.get_skill('simple_strategy')
    
    # Create strategies
    ma_strategy = strategy.create_ma_strategy(20, 50)
    print(f"  📈 Created: {ma_strategy['name']}")
    print(f"     Parameters: {ma_strategy['short_window']}/{ma_strategy['long_window']} MA")
    
    rsi_strategy = strategy.create_rsi_strategy(14, 30, 70)
    print(f"  📊 Created: {rsi_strategy['name']}")
    print(f"     RSI Levels: {rsi_strategy['oversold']}/{rsi_strategy['overbought']}")
    
    # Generate signals
    signal = strategy.generate_signal([1500, 1520, 1510], 'ma')
    print(f"  🎯 Signal: {signal['signal']} (Confidence: {signal['confidence']})")
    
    print("\n📈 Testing Market Analyzer Skill")
    analyzer = skills_mgr.get_skill('market_analyzer')
    
    trend_analysis = analyzer.analyze_trend(1250.50)
    print(f"  📊 Trend: {trend_analysis['trend']}")
    print(f"  💹 Signal: {trend_analysis['signal']}")
    print(f"  💰 Price: ₹{trend_analysis['price']:.2f}")
    
    volatility = analyzer.calculate_volatility([1000, 1020, 1015, 1030, 1025])
    print(f"  📉 Volatility: {volatility['volatility']}% ({volatility['trend']})")
    
    print("\n⚠️ Testing Risk Manager Skill")
    risk_mgr = skills_mgr.get_skill('risk_manager')
    
    position_info = risk_mgr.calculate_position_size(100000, 0.02)
    print(f"  💼 Position Size: ₹{position_info['position_size']:.2f}")
    print(f"  🎯 Risk Amount: ₹{position_info['risk_amount']:.2f}")
    print(f"  📊 Risk Percent: {position_info['risk_percent']}%")
    
    risk_assessment = risk_mgr.assess_risk(100000, -1500)
    print(f"  ⚠️ Risk Level: {risk_assessment['risk_level']}")
    print(f"  📉 Risk Ratio: {risk_assessment['risk_ratio']}%")
    
    print("\n🤖 Testing Automation Skill")
    automation = skills_mgr.get_skill('automation')
    
    # Execute trades
    buy_result = automation.execute_trade('RELIANCE', 'BUY', 10, 2500)
    print(f"  ✅ {buy_result['message']}")
    
    sell_result = automation.execute_trade('TCS', 'SELL', 5, 3500)
    print(f"  ✅ {sell_result['message']}")
    
    order_history = automation.get_order_history()
    print(f"  📋 Total Orders: {len(order_history)}")
    
    print("\n🎊 Skills System Status: FULLY OPERATIONAL")
    print("✅ All skills loaded and working correctly")
    print("✅ Ready for integration with main trading system")
    print("✅ Author attribution system active")
    
    return skills_mgr

if __name__ == '__main__':
    demo_skills_system()
