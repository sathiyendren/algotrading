# Cache Optimization Skill

## Overview
Specialized skill for optimizing and managing the Redis cache layer in the algo trading system. Focuses on performance tuning, memory management, and cache efficiency.

## Capabilities

### 1. Cache Performance Analysis
- Monitor cache hit/miss ratios
- Analyze memory usage patterns
- Identify performance bottlenecks
- Optimize TTL settings based on data access patterns

### 2. Cache Strategy Development
- Design intelligent caching strategies
- Implement cache warming techniques
- Optimize key naming conventions
- Develop cache invalidation policies

### 3. Memory Management
- Monitor Redis memory usage
- Implement efficient data serialization
- Optimize key expiration policies
- Manage cache eviction strategies

### 4. Performance Tuning
- Optimize Redis configuration
- Implement connection pooling
- Tune cache query patterns
- Monitor and improve response times

## Usage Examples

### Cache Health Check


### Cache Performance Analysis


### Cache Optimization


## Performance Metrics

### Key Performance Indicators
- **Cache Hit Ratio**: Target > 90%
- **Response Time**: < 10ms for cached data
- **Memory Efficiency**: < 1MB for typical trading day
- **API Reduction**: > 95% reduction in NSE calls

### Monitoring


## Best Practices

### 1. TTL Optimization
- Real-time data: 3-5 minutes
- Calculated indicators: 5-15 minutes
- Historical data: 1-24 hours
- Reference data: 24+ hours

### 2. Key Management
- Use consistent naming patterns
- Include symbol and date in keys
- Implement hierarchical key structure
- Use key prefixes for data types

### 3. Memory Management
- Monitor memory usage regularly
- Implement efficient serialization
- Use appropriate data structures
- Set memory limits and eviction policies

## Integration Points

### Option Chain Cache
- Automatic caching after each NSE scrape
- 5-minute TTL for real-time data
- JSON serialization for complex data

### Participant OI Cache
- Cache after database writes
- 5-minute TTL for participant data
- Optimized for frequent access patterns

### Calculated Metrics Cache
- PCR, max pain, and other indicators
- Variable TTL based on calculation frequency
- Efficient numeric storage

## Troubleshooting

### Common Issues
1. **High Memory Usage**: Check TTL settings and key expiration
2. **Low Hit Ratio**: Verify cache warming and key patterns
3. **Slow Response**: Check Redis configuration and network latency
4. **Connection Issues**: Verify Redis server status and connectivity

### Debug Commands


## Performance Benchmarks

### Before Cache
- Option chain fetch: 5-10 seconds
- PCR calculation: 2-3 seconds
- API rate limits: Frequent

### After Cache
- Option chain fetch: 10-50 milliseconds
- PCR retrieval: 5-10 milliseconds
- API reduction: 95% fewer calls

### Performance Improvement
- **Speed**: ~100x faster data retrieval
- **Reliability**: Reduced dependency on external APIs
- **Scalability**: Handles 10x more requests
- **Cost**: Lower bandwidth and infrastructure costs
