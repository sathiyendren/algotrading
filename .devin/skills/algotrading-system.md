# Algo Trading System - Devin AI Skill

## 🎯 Overview
This skill provides comprehensive support for the algo trading system, including data collection, validation, caching, monitoring, and maintenance operations.

## 🔧 Capabilities

### Data Management
- **Real-time Data Collection**: NSE market data scraping with error handling
- **Data Validation**: 15+ validation rules ensuring data quality
- **Database Operations**: PostgreSQL with upsert and transaction management
- **Cache Management**: Redis caching with intelligent TTL strategies

### System Monitoring
- **Health Checks**: System status and performance monitoring
- **Data Verification**: Daily automated verification reports
- **Alert Management**: Telegram notification system
- **Log Analysis**: Comprehensive error tracking and debugging

### Performance Optimization
- **Cache Performance**: 100x faster data access with Redis
- **Query Optimization**: Database performance tuning
- **Memory Management**: Efficient data structures and cleanup
- **Load Handling**: High-frequency data processing

## 🏗️ System Architecture

### Core Components
- **NSE Scraper**: Real-time market data collection
- **Data Validator**: Quality assurance and validation
- **Redis Cache**: High-performance data caching
- **PostgreSQL**: Reliable data storage
- **Telegram Bot**: Alert and notification system

### Data Flow


## 📊 Key Features

### Data Collection
- Participant OI (FII/DII/CLIENT/PRO)
- FII/DII Cash market activity
- Complete Option Chain data
- Max pain calculations

### Validation Rules
- Negative value detection
- Missing data validation
- PCR ratio validation (0.1-3.0)
- Stale expiry detection
- Imbalance alerts

### Performance Metrics
- Cache hit rate: >95%
- Response time: <1ms
- Memory usage: <1MB
- Validation speed: <100ms

## 🚀 Usage Commands

### Data Operations


### Monitoring


### Maintenance


## 🔍 Troubleshooting

### Common Issues
- **Data Validation Failures**: Check logs/data_validator.log
- **Cache Issues**: Verify Redis connection and memory
- **Database Errors**: Check connection and disk space
- **Scraping Failures**: Verify NSE website accessibility

### Health Checks
- **Data Quality**: Run verify_data.py
- **Cache Performance**: Check get_cache_stats()
- **System Logs**: Review all log files
- **Test Coverage**: Run pytest tests/

## 📈 Performance Monitoring

### Key Metrics
- Data collection success rate
- Cache hit/miss ratios
- Validation processing time
- Database query performance
- Alert response times

### Optimization Tips
- Monitor cache TTL settings
- Optimize database indexes
- Review validation rules
- Check memory usage patterns

## 🛡️ Security Considerations

### Data Protection
- Input validation on all data
- Secure database connections
- Rate limiting for scraping
- Error message sanitization

### Access Control
- Environment variable configuration
- Database credential management
- API token security
- Log file permissions

## 📝 Development Guidelines

### Code Quality
- Comprehensive test coverage
- Clear documentation
- Error handling patterns
- Performance optimization

### Best Practices
- Use Redis for frequently accessed data
- Validate all data before storage
- Log all operations for debugging
- Monitor system health continuously

## 🔄 Automation

### Scheduled Tasks
- **4:35 PM Daily**: Automated data verification
- **Every 5 min**: Option chain collection
- **Real-time**: Data validation and caching
- **Continuous**: Health monitoring and alerts

### Cron Jobs


## 📞 Support

### Getting Help
- Check system logs for errors
- Run verification scripts
- Review test results
- Monitor cache performance

### Contact Information
- System logs: /opt/algotrading/logs/
- Data verification: src/verify_data.py
- Test suite: tests/test_data_validator.py
- Cache management: src/cache.py

---

**This skill provides comprehensive support for maintaining and optimizing the algo trading system with focus on reliability, performance, and automation.**
