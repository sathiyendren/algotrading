# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01 01:37:00
# Description: Risk management and position sizing skill
# Project: Algo Trading System

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.logger = logger
        self.max_portfolio_risk = 0.02  # 2% max portfolio risk
        self.max_position_size = 0.1    # 10% max position size
        
    def calculate_position_size(self, account_balance, risk_per_trade, stop_loss_pct, entry_price):
        """Calculate optimal position size based on risk management rules"""
        try:
            # Risk amount per trade
            risk_amount = account_balance * risk_per_trade
            
            # Stop loss price
            stop_loss_price = entry_price * (1 - stop_loss_pct)
            
            # Position size based on risk
            position_size = risk_amount / (entry_price - stop_loss_price)
            
            # Maximum position size limit
            max_shares = (account_balance * self.max_position_size) / entry_price
            position_size = min(position_size, max_shares)
            
            return {
                'position_size': round(position_size, 2),
                'risk_amount': round(risk_amount, 2),
                'stop_loss_price': round(stop_loss_price, 2),
                'max_shares_allowed': round(max_shares, 2)
            }
        except Exception as e:
            self.logger.error("Position size calculation error: %s", str(e))
            return {'error': str(e)}
    
    def assess_portfolio_risk(self, positions_data):
        """Assess overall portfolio risk"""
        try:
            total_value = sum(pos['value'] for pos in positions_data)
            total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions_data)
            
            # Calculate portfolio metrics
            portfolio_return = total_unrealized_pnl / total_value * 100 if total_value > 0 else 0
            
            # Risk assessment
            if abs(portfolio_return) > 5:
                risk_level = 'HIGH'
            elif abs(portfolio_return) > 2:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            return {
                'total_portfolio_value': total_value,
                'total_unrealized_pnl': total_unrealized_pnl,
                'portfolio_return_pct': round(portfolio_return, 2),
                'risk_level': risk_level,
                'position_count': len(positions_data)
            }
        except Exception as e:
            self.logger.error("Portfolio risk assessment error: %s", str(e))
            return {'error': str(e)}
    
    def generate_risk_alert(self, portfolio_risk):
        """Generate risk alerts based on portfolio metrics"""
        alerts = []
        
        if portfolio_risk.get('portfolio_return_pct', 0) < -5:
            alerts.append("CRITICAL: Portfolio down more than 5%")
        elif portfolio_risk.get('portfolio_return_pct', 0) < -2:
            alerts.append("WARNING: Portfolio down more than 2%")
        
        if portfolio_risk.get('position_count', 0) > 10:
            alerts.append("INFO: High number of positions (" + str(portfolio_risk['position_count']) + ")")
        
        return alerts

if __name__ == "__main__":
    risk_mgr = RiskManager()
    print("Risk Manager skill initialized")
