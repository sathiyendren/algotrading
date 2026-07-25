# FII Algo Trading System

Professional FII (Foreign Institutional Investor) algo trading system with advanced signal generation, risk management, and automated execution capabilities.

## 🚀 Features

### Core Components
- **Data Collection**: Real-time NSE data, option chains, VIX monitoring
- **Signal Generation**: FII scoring, chart pattern detection, technical analysis
- **Risk Management**: Position sizing, stop-loss, portfolio risk monitoring
- **Execution**: Automated order placement, strategy building
- **Monitoring**: Real-time position tracking, P&L monitoring
- **Alerts**: Telegram bot for trade alerts and system notifications
- **API**: REST API for dashboard and external integrations
- **Dashboard**: Web-based trading dashboard with real-time charts

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Redis server
- Zerodha Kite account (for trading)

### Setup Steps

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd algotrading
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configurations
   ```

4. Setup database
   ```bash
   # Create PostgreSQL database
   createdb algotrading
   # Run migrations (if using Alembic)
   alembic upgrade head
   ```

5. Start Redis server
   ```bash
   redis-server
   ```

## 🚀 Running the System

### Start the complete system
```bash
python main.py
```

### Start individual components

1. API Server only
   ```bash
   python -m fii_algo.api.fastapi_server
   ```

2. Telegram Bot only
   ```bash
   python -c "from fii_algo.alerts.telegram_bot import telegram_bot; import asyncio; asyncio.run(telegram_bot.start_bot())"
   ```

3. Data Collection only
   ```bash
   python -c "from fii_algo.data.nse_scraper import NSEDataCollector; collector = NSEDataCollector(); collector.run_continuous()"
   ```

## 📊 Web Dashboard

Access the trading dashboard at:
```
http://localhost:8000/dashboard/
```

## 🔧 API Documentation

### Health Check
```
GET /health
```

### System Status
```
GET /status
```

### Recent Signals
```
GET /signals?limit=10
```

### Generate New Signal
```
POST /signals/generate
```

### Active Positions
```
GET /positions
```

### P&L Summary
```
GET /pnl
```

### Risk Metrics
```
GET /risk
```

## 📈 Trading Strategies

### Supported Strategies
1. Bull Call Spread - Moderate bullish outlook
2. Bear Put Spread - Moderate bearish outlook
3. Long Straddle - High volatility expectation
4. Iron Condor - Range-bound markets
5. Simple Options - Directional bets

## 📱 Telegram Bot Commands

- /start - Start the bot
- /status - System status
- /positions - Current positions
- /pnl - P&L summary
- /risk - Risk metrics
- /help - Show help

## 🧪 Testing

```bash
pytest
```

## 📝 Logging

Logs are written to:
- Console output
- fii_algo/logs/trading.log

## 🚨 Risk Warnings

⚠️ IMPORTANT: This is an automated trading system that can execute real trades. Please ensure:

1. Paper Trading First: Always test with paper trading before using real money
2. Risk Limits: Set appropriate risk limits and position sizes
3. Monitoring: Monitor the system continuously during market hours
4. Backup Plans: Have manual override capabilities
5. Regulatory Compliance: Ensure compliance with local regulations

---

⚠️ Disclaimer: This software is for educational and research purposes only. Use at your own risk.
