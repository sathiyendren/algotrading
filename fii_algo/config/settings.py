"""
FII Algo Trading System Configuration
Centralized settings for all components
"""

import os
from datetime import time
from typing import Dict, List

class TradingConfig:
    """Main configuration class for FII algo trading system."""
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://algotrader:password@localhost:5432/algotrading')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # NSE Configuration
    NSE_BASE_URL = 'https://www.nseindia.com'
    NSE_API_BASE = 'https://www.nseindia.com/api'
    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # Market Hours
    MARKET_OPEN = time(9, 15)
    MARKET_CLOSE = time(15, 30)
    MARKET_DAYS = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
    
    # Data Collection
    COLLECTION_INTERVAL = 30  # seconds
    OPTION_CHAIN_SYMBOLS = ['NIFTY', 'BANKNIFTY']
    MAX_STRIKES = 50
    
    # FII Scoring
    FII_WEIGHTS = {
        'cash_flow': 0.4,
        'participant_oi': 0.3,
        'option_chain': 0.2,
        'vix': 0.1
    }
    
    # Risk Management
    MAX_POSITION_SIZE = 100000  # Rs
    MAX_RISK_PER_TRADE = 0.02  # 2%
    STOP_LOSS_PERCENTAGE = 0.05  # 5%
    
    # Kite API (Zerodha)
    KITE_API_KEY = os.getenv('KITE_API_KEY')
    KITE_API_SECRET = os.getenv('KITE_API_SECRET')
    KITE_ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN')
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # API Server
    API_HOST = '0.0.0.0'
    API_PORT = 8000
    API_DEBUG = False
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s'
    
    @classmethod
    def get_database_config(cls) -> Dict:
        """Get database configuration."""
        return {
            'url': cls.DATABASE_URL,
            'echo': False,
            'pool_pre_ping': True
        }
    
    @classmethod
    def get_redis_config(cls) -> Dict:
        """Get Redis configuration."""
        return {
            'url': cls.REDIS_URL,
            'decode_responses': True
        }

# Event calendar for important dates
EVENT_CALENDAR = {
    'rbi_policy': {
        '2024-02-08': 'RBI Monetary Policy',
        '2024-04-05': 'RBI Monetary Policy',
        '2024-06-07': 'RBI Monetary Policy',
        '2024-08-08': 'RBI Monetary Policy',
        '2024-10-04': 'RBI Monetary Policy',
        '2024-12-06': 'RBI Monetary Policy',
    },
    'budget': {
        '2024-02-01': 'Union Budget',
        '2024-07-23': 'Union Budget',
    },
    'expiry': {
        # Weekly expiry (Thursday)
        '2024-07-04': 'Weekly Expiry',
        '2024-07-11': 'Weekly Expiry',
        '2024-07-18': 'Weekly Expiry',
        '2024-07-25': 'Weekly Expiry',
        # Monthly expiry (last Thursday)
        '2024-07-25': 'Monthly Expiry',
    }
}
