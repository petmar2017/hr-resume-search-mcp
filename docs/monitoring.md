# Monitoring & Observability Guide - HR Resume Search MCP API

## 📊 Monitoring Overview

Comprehensive monitoring stack using Prometheus, Grafana, Loki, and Tempo for metrics, dashboards, logs, and traces.

## 🎯 Key Metrics

### Application Metrics

#### API Performance
```python
# Response time percentiles
api_response_time_seconds{
  endpoint="/api/v1/resumes/search",
  method="GET",
  quantile="0.99"
} < 2.0  # 99th percentile under 2 seconds

# Request rate
rate(api_requests_total[5m]) > 0  # Requests per second

# Error rate
rate(api_errors_total[5m]) / rate(api_requests_total[5m]) < 0.01  # <1% error rate
```

#### Business Metrics
```python
# Resume processing
resumes_processed_total  # Total resumes processed
resume_processing_duration_seconds  # Processing time
resume_processing_queue_size  # Queue length

# Search metrics
searches_performed_total  # Total searches
search_result_count  # Results per search
search_duration_seconds  # Search time
```

### System Metrics

#### Resource Usage
```yaml
# CPU Usage
container_cpu_usage_seconds_total < 0.8  # <80% CPU

# Memory Usage
container_memory_working_set_bytes / container_spec_memory_limit_bytes < 0.8  # <80% memory

# Disk I/O
rate(container_fs_reads_bytes_total[5m])  # Read throughput
rate(container_fs_writes_bytes_total[5m])  # Write throughput
```

#### Database Metrics
```sql
# Connection pool
pg_stat_database_numbackends  # Active connections
pg_stat_database_conflicts  # Conflicts
pg_stat_database_deadlocks  # Deadlocks

# Query performance
pg_stat_statements_mean_exec_time  # Average query time
pg_stat_statements_calls  # Query frequency
```

## 🔧 Prometheus Setup

### Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
```

### Application Instrumentation

```python
# api/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
import time

# Metrics definitions
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'api_active_users',
    'Currently active users'
)

resume_processing_queue = Gauge(
    'resume_processing_queue_size',
    'Number of resumes in processing queue'
)

# Middleware for metrics collection
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

## 📈 Grafana Dashboards

### API Performance Dashboard

```json
{
  "dashboard": {
    "title": "HR Resume API Performance",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time (p99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(api_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(api_errors_total[5m]) / rate(api_requests_total[5m]) * 100"
          }
        ]
      }
    ]
  }
}
```

### Business Metrics Dashboard

```json
{
  "dashboard": {
    "title": "HR Resume Business Metrics",
    "panels": [
      {
        "title": "Resumes Processed Today",
        "targets": [
          {
            "expr": "increase(resumes_processed_total[1d])"
          }
        ]
      },
      {
        "title": "Search Volume",
        "targets": [
          {
            "expr": "rate(searches_performed_total[1h])"
          }
        ]
      },
      {
        "title": "Processing Queue",
        "targets": [
          {
            "expr": "resume_processing_queue_size"
          }
        ]
      }
    ]
  }
}
```

## 📝 Loki Logging

### Configuration

```yaml
# loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks
```

### Application Logging

```python
# api/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Structured logging
def log_api_request(request, response, duration):
    logger.info(
        "API Request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration * 1000,
            "user_id": request.user.id if hasattr(request, 'user') else None,
            "ip": request.client.host
        }
    )

def log_resume_processing(resume_id, status, duration):
    logger.info(
        "Resume Processing",
        extra={
            "resume_id": resume_id,
            "status": status,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### Log Queries

```logql
# API errors in last hour
{job="api"} |= "ERROR" | json | __error__="" | rate[1h]

# Slow requests (>2s)
{job="api"} | json | duration_ms > 2000

# Failed resume processing
{job="api"} |= "Resume Processing" | json | status="failed"

# User activity
{job="api"} | json | user_id="123" | rate[5m]
```

## 🔍 Tempo Tracing

### Configuration

```yaml
# tempo-config.yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
        http:

ingester:
  trace_idle_period: 10s
  max_traces_per_user: 10000

compactor:
  compaction:
    block_retention: 1h

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces
```

### Application Tracing

```python
# api/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True
)

# Add span processor
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Auto-instrument libraries
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
RedisInstrumentor().instrument(redis_client=redis_client)

# Manual instrumentation
@app.post("/api/v1/resumes/upload")
async def upload_resume(file: UploadFile):
    with tracer.start_as_current_span("upload_resume") as span:
        span.set_attribute("file.name", file.filename)
        span.set_attribute("file.size", file.size)
        
        with tracer.start_as_current_span("validate_file"):
            # Validation logic
            pass
        
        with tracer.start_as_current_span("process_file"):
            # Processing logic
            pass
        
        return {"status": "success"}
```

## 🚨 Alerting Rules

### Prometheus Alert Rules

```yaml
# alerts.yml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) / rate(api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.99, rate(api_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow API response times"
          description: "99th percentile response time is {{ $value }}s"

      - alert: HighMemoryUsage
        expr: container_memory_working_set_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value | humanizePercentage }} of connections in use"

      - alert: ProcessingQueueBacklog
        expr: resume_processing_queue_size > 100
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Large processing queue backlog"
          description: "{{ $value }} resumes waiting to be processed"
```

### Alert Manager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'HR Resume API Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: 'critical'
    slack_configs:
      - channel: '#critical-alerts'
        title: '🚨 CRITICAL: HR Resume API'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

## 📊 SLOs (Service Level Objectives)

### Availability SLO
```yaml
slo:
  name: API Availability
  target: 99.9%  # Three 9s
  measurement: |
    1 - (
      rate(api_errors_total{status=~"5.."}[30d]) /
      rate(api_requests_total[30d])
    )
  error_budget: 43.2 minutes/month
```

### Latency SLO
```yaml
slo:
  name: API Latency
  target: 95% of requests < 1s
  measurement: |
    histogram_quantile(0.95, 
      rate(api_request_duration_seconds_bucket[30d])
    ) < 1.0
```

### Processing SLO
```yaml
slo:
  name: Resume Processing Time
  target: 90% processed within 60s
  measurement: |
    histogram_quantile(0.90,
      rate(resume_processing_duration_seconds_bucket[30d])
    ) < 60
```

## 🔄 Monitoring Runbook

### Daily Checks
1. Review error rate trends
2. Check processing queue length
3. Verify backup completion
4. Review resource usage

### Weekly Reviews
1. Analyze performance trends
2. Review SLO compliance
3. Update alert thresholds
4. Clean up old logs

### Monthly Tasks
1. Generate SLO reports
2. Capacity planning review
3. Update dashboards
4. Review incident postmortems

## 🛠️ Troubleshooting Metrics

### High CPU Usage
```promql
# Identify CPU-intensive endpoints
topk(5, rate(api_request_duration_seconds_sum[5m]))

# Check goroutine leaks (if applicable)
go_goroutines

# Database query time
avg(pg_stat_statements_mean_exec_time) by (query)
```

### Memory Leaks
```promql
# Memory growth rate
rate(container_memory_working_set_bytes[1h])

# Python object counts (if using py-spy)
python_gc_objects_collected_total
```

### Slow Queries
```sql
-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

## 📱 Mobile Monitoring

For mobile/web clients accessing the API:

```javascript
// Frontend monitoring
window.addEventListener('error', (e) => {
  fetch('/api/logs', {
    method: 'POST',
    body: JSON.stringify({
      level: 'error',
      message: e.message,
      stack: e.stack,
      url: window.location.href,
      userAgent: navigator.userAgent
    })
  });
});

// Performance monitoring
const perfData = performance.getEntriesByType('navigation')[0];
fetch('/api/metrics/frontend', {
  method: 'POST',
  body: JSON.stringify({
    loadTime: perfData.loadEventEnd - perfData.loadEventStart,
    domReady: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
    ttfb: perfData.responseStart - perfData.requestStart
  })
});
```