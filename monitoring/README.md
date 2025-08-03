# HR Resume Search - Performance Monitoring

Comprehensive monitoring setup for the HR Resume Search API targeting <200ms response times.

## 🎯 Performance Targets

- **API Response Time**: <200ms (95th percentile)
- **Database Query Time**: <100ms (95th percentile)  
- **Search Request Time**: <150ms (95th percentile)
- **Cache Hit Rate**: >80%
- **Error Rate**: <1%
- **Uptime**: >99.9%

## 📊 Monitoring Stack

### Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Redis**: Caching layer for performance optimization
- **Node Exporter**: System-level metrics

### Metrics Collected

#### API Performance
- Request rate and response times by endpoint
- Error rates (4xx, 5xx) by status code
- Request/response payload sizes
- Concurrent active connections

#### Search Performance  
- Search request duration by search type
- Search result counts and quality scores
- Cache hit/miss rates by cache type
- Zero result search rates

#### Database Performance
- Query execution times by operation type
- Connection pool utilization
- Active connections and query queue length
- Index usage and table scan rates

#### Resume Processing
- Parsing success/failure rates by file type
- Processing duration for different file sizes
- Upload sizes and formats
- Error categorization

#### System Health
- Memory and CPU usage
- Disk I/O and network metrics
- Application uptime and restarts
- Cache memory utilization

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
# Navigate to monitoring directory
cd monitoring/

# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Start HR Resume Search API

```bash
# Navigate to project root
cd ..

# Install dependencies (if not already done)
make install

# Run database migrations with performance indexes
make db-migrate

# Start the API server with metrics enabled
make dev
```

### 3. Access Monitoring Interfaces

- **Grafana Dashboard**: http://localhost:3000
  - Username: `admin`
  - Password: `admin_change_me`
  - Dashboard: "HR Resume Search - Performance Dashboard"

- **Prometheus Metrics**: http://localhost:9090
  - Targets: http://localhost:9090/targets
  - Rules: http://localhost:9090/rules

- **API Metrics Endpoint**: http://localhost:8000/metrics
  - Prometheus format metrics
  - Summary: http://localhost:8000/metrics/summary

### 4. Load Test for Performance Validation

```bash
# Install load testing tools
pip install locust

# Run basic load test (if available)
# locust -f tests/load_test.py --host=http://localhost:8000
```

## 📈 Dashboard Overview

### Key Panels

1. **API Request Rate**: Requests per second trending
2. **Response Time Distribution**: P50, P95, P99 percentiles
3. **Search Performance**: Search-specific latency metrics
4. **Database Query Performance**: DB operation timing
5. **Cache Hit Rate**: Cache effectiveness metrics
6. **Search Results Quality**: Match score distributions
7. **Resume Processing Rate**: Document processing metrics
8. **Error Rate by Endpoint**: Error tracking and alerting
9. **System Resources**: Memory, CPU, connections

### Alert Conditions

- ⚠️ **Warning**: Response time >200ms for 2+ minutes
- 🚨 **Critical**: Response time >1s for 1+ minute
- ⚠️ **Warning**: Error rate >5% for 3+ minutes  
- ⚠️ **Warning**: Cache hit rate <50% for 10+ minutes
- ⚠️ **Warning**: DB query time >100ms for 5+ minutes

## 🛠️ Configuration

### Environment Variables

```bash
# Enable metrics collection
ENABLE_METRICS=true

# Prometheus server (optional - auto-starts on port 9090)
PROMETHEUS_URL=http://localhost:9090

# Grafana dashboard (optional)
GRAFANA_URL=http://localhost:3000
```

### Prometheus Configuration

Edit `prometheus.yml` to customize:
- Scrape intervals
- Target endpoints
- Recording rules
- Alert thresholds

### Grafana Customization

- Import `grafana_dashboard.json` for the pre-built dashboard
- Customize panels, thresholds, and alerts
- Add custom queries for specific business metrics

## 🔧 Troubleshooting

### Common Issues

1. **Metrics not appearing**:
   ```bash
   # Check if metrics endpoint is accessible
   curl http://localhost:8000/metrics
   
   # Verify Prometheus is scraping
   curl http://localhost:9090/targets
   ```

2. **High response times**:
   ```bash
   # Check database performance
   make db-status
   
   # Verify cache is working  
   curl http://localhost:8000/metrics/summary
   ```

3. **Database connection issues**:
   ```bash
   # Check connection pool metrics
   # Look for db_connections_active vs db_connection_pool_size
   ```

### Performance Optimization

1. **Enable Redis caching** (already implemented):
   - Search result caching (5min TTL)
   - Candidate profile caching (10min TTL)  
   - Colleague analysis caching (15min TTL)

2. **Database indexes** (already implemented):
   - B-tree indexes on frequently queried columns
   - GIN indexes for JSONB operations
   - Composite indexes for complex queries

3. **Query optimization**:
   - Monitor slow query logs
   - Use EXPLAIN ANALYZE for query planning
   - Consider read replicas for heavy search loads

## 📊 Performance Baselines

### Expected Performance (after optimizations)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| API Response (P95) | <200ms | TBD | 🟡 Monitor |
| Search Response (P95) | <150ms | TBD | 🟡 Monitor |  
| DB Query (P95) | <100ms | TBD | 🟡 Monitor |
| Cache Hit Rate | >80% | TBD | 🟡 Monitor |
| Error Rate | <1% | TBD | 🟡 Monitor |

### Load Testing Results

Run load tests to establish baselines:

```bash
# Example test scenarios
- 10 concurrent users, 1000 requests
- 50 concurrent users, 5000 requests  
- 100 concurrent users, 10000 requests
```

## 🔄 Continuous Monitoring

### Daily Tasks
- [ ] Review error rate trends
- [ ] Check cache hit rate efficiency
- [ ] Monitor response time percentiles
- [ ] Verify all alerts are functional

### Weekly Tasks  
- [ ] Analyze search result quality metrics
- [ ] Review database query performance
- [ ] Check system resource utilization
- [ ] Update performance baselines

### Monthly Tasks
- [ ] Performance test with realistic load
- [ ] Review and tune alert thresholds
- [ ] Update monitoring dashboard
- [ ] Capacity planning analysis

## 📚 Additional Resources

- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [FastAPI Monitoring Guide](https://fastapi.tiangolo.com/advanced/monitoring/)

## 🆘 Support

For monitoring issues:
1. Check service logs: `docker-compose -f docker-compose.monitoring.yml logs <service>`
2. Verify configuration files
3. Review Prometheus targets and rules
4. Test metric endpoints manually

---

**Status**: ✅ Monitoring infrastructure complete and ready for performance validation