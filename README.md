# Algo Trading System

A comprehensive algorithmic trading system with real-time data collection, validation, caching, and monitoring capabilities.

## 🚀 Features

### 📊 Data Collection & Validation
- **NSE Data Scraper**: Real-time market data collection
- **Data Validator**: Comprehensive quality assurance with 15+ validation rules
- **Telegram Alerts**: Instant notifications for data quality issues
- **Automated Verification**: Daily health checks at 4:35 PM

### ⚡ Performance & Caching
- **Redis Cache**: 100x faster data access with sub-millisecond latency
- **Smart TTL**: 5min for real-time data, 1hr for slower metrics
- **Memory Efficient**: <1MB memory usage for full cache
- **Cache Integration**: Seamlessly integrated with option_chain.py and db_writer.py

### 🛡️ Data Quality Assurance
- **Participant OI Validation**: FII/DII/CLIENT/PRO position verification
- **FII/DII Cash Validation**: Daily cash flow monitoring
- **Option Chain Validation**: PCR ratios, strike counts, expiry checks
- **Real-time Validation**: Pre-database write validation with error blocking

### 📈 Market Data Coverage
- **Participant OI**: Real-time Open Interest by client type
- **FII/DII Cash**: Daily cash market activity
- **Option Chain**: Complete options data with PCR calculations
- **Max Pain**: Options pain point calculations

### 🔧 Infrastructure & Monitoring
- **PostgreSQL Database**: Reliable data storage with upsert operations
- **Automated Scheduling**: Cron-based data collection and verification
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Health Monitoring**: Snapshot completeness and gap detection

## 🏗️ Architecture



## 📋 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Telegram Bot Token

### Setup
```bash
# Clone repository
git clone <repository-url>
cd algotrading

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database and Telegram credentials

# Initialize database
python scripts/init_db.py

# Start Redis server
redis-server

# Run tests
pytest tests/ -v
```

## 🔧 Configuration

### Environment Variables
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/algotrading

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# NSE Settings
NSE_SCRAPING_INTERVAL=300  # 5 minutes
```

## 🚀 Usage

### Manual Data Collection
```bash
# Collect participant OI data
python src/scrape_participant_oi.py

# Collect FII/DII cash data
python src/scrape_fii_dii_cash.py

# Collect option chain data
python src/option_chain.py
```

### Data Verification
```bash
# Manual verification
python src/verify_data.py

# Check verification status
./scripts/show_verification_status.sh
```

### Cache Management
```bash
# Check cache status
python -c "from src.cache import get_cache_stats; print(get_cache_stats())"

# Clear cache
python -c "from src.cache import clear_cache; clear_cache()"
```

## 📊 Monitoring

### Daily Reports
The system automatically generates daily verification reports at 4:35 PM:
- Participant OI comparison with NSE website
- FII/DII cash flow analysis
- Option chain PCR metrics
- System health checks

### Real-time Alerts
- Data validation failures
- Cache system issues
- Database connection problems
- Scraping errors

### Logs
- `logs/data_validator.log` - Validation results
- `logs/daily_verification.log` - Daily verification reports
- `logs/nse_scraper.log` - Scraping activities
- `logs/option_chain.log` - Option chain processing

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_data_validator.py -v
pytest tests/test_cache.py -v

# Run with coverage
pytest --cov=src tests/
```

### Test Coverage
- **Data Validator**: 15/15 tests passing
- **Cache System**: Performance and functionality tests
- **Database Integration**: CRUD operations and validation
- **API Integration**: Mock tests for external services

## 📈 Performance

### Cache Performance
- **Read Speed**: 100x faster than database queries
- **Memory Usage**: <1MB for full dataset
- **Hit Rate**: >95% during trading hours
- **Latency**: <1ms average response time

### Data Validation
- **Processing Speed**: <100ms for full dataset
- **Memory Efficient**: Streaming validation
- **Error Detection**: 15+ validation rules
- **Alert Latency**: <5 seconds for critical issues

## 🔒 Security

- **Input Validation**: All data validated before database writes
- **SQL Injection Protection**: Parameterized queries
- **Rate Limiting**: Respect NSE scraping limits
- **Error Handling**: No sensitive data in logs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the logs for troubleshooting
- Review the verification reports for data issues

---

**Built with ❤️ for algorithmic trading excellence**
