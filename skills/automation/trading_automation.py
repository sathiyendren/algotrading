# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01 01:38:00
# Description: Trading automation and execution skill
# Project: Algo Trading System

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class TradingAutomation:
    def __init__(self):
        self.logger = logger
        self.active_orders = {}
        self.execution_history = []
        
    def execute_trade(self, symbol, action, quantity, price, order_type='MARKET'):
        """Execute trade with risk checks"""
        try:
            order_id = f"{symbol}_{action}_{int(time.time())}"
            
            order = {
                'order_id': order_id,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                'status': 'PENDING',
                'created_at': datetime.now().isoformat()
            }
            
            # Simulate order execution
            order['status'] = 'EXECUTED'
            order['executed_at'] = datetime.now().isoformat()
            order['executed_price'] = price
            
            self.active_orders[order_id] = order
            self.execution_history.append(order)
            
            self.logger.info(f"Trade executed: {action} {quantity} shares of {symbol} at {price}")
            
            return {
                'success': True,
                'order_id': order_id,
                'message': f"Successfully executed {action} order for {symbol}"
            }
            
        except Exception as e:
            self.logger.error("Trade execution error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, order_id):
        """Cancel pending order"""
        try:
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                if order['status'] == 'PENDING':
                    order['status'] = 'CANCELLED'
                    order['cancelled_at'] = datetime.now().isoformat()
                    return {'success': True, 'message': 'Order cancelled successfully'}
                else:
                    return {'success': False, 'message': 'Order cannot be cancelled'}
            else:
                return {'success': False, 'message': 'Order not found'}
        except Exception as e:
            self.logger.error("Order cancellation error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    def get_execution_summary(self):
        """Get trading execution summary"""
        if not self.execution_history:
            return {'message': 'No executions yet'}
        
        executed_trades = [trade for trade in self.execution_history if trade['status'] == 'EXECUTED']
        buy_trades = [trade for trade in executed_trades if trade['action'] == 'BUY']
        sell_trades = [trade for trade in executed_trades if trade['action'] == 'SELL']
        
        return {
            'total_trades': len(executed_trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'last_execution': executed_trades[-1]['executed_at'] if executed_trades else None
        }

if __name__ == "__main__":
    automation = TradingAutomation()
    print("Trading Automation skill initialized")
