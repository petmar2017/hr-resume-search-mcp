# Performance Optimization & Monitoring Guide

**HR Resume Search MCP API - Production Performance Guide**

## Table of Contents

- [Performance Overview](#performance-overview)
- [Metrics & Monitoring](#metrics--monitoring)
- [Database Optimization](#database-optimization)
- [Search Performance](#search-performance)
- [Caching Strategies](#caching-strategies)
- [API Optimization](#api-optimization)
- [Load Testing](#load-testing)
- [Troubleshooting](#troubleshooting)
- [Monitoring Dashboards](#monitoring-dashboards)

## Performance Overview

The HR Resume Search API includes comprehensive performance monitoring and optimization features designed for production scalability.

### Performance Targets

**Response Time Targets**:
- Health endpoints: <50ms
- Authentication: <200ms  
- Simple search: <500ms
- Complex search: <1000ms
- Resume upload: <2000ms
- File processing: <30s

**Throughput Targets**:
- Peak requests: 1000 req/sec
- Concurrent users: 500
- Search queries: 100 searches/sec
- File uploads: 10 uploads/sec

**Resource Targets**:
- CPU utilization: <70% average
- Memory usage: <80% of allocated
- Database connections: <80% of pool
- Cache hit ratio: >80%

---

## Metrics & Monitoring

### Prometheus Metrics Integration

The API includes comprehensive metrics collection through the integrated metrics middleware:

```python
# api/middleware/metrics_middleware.py integration
from .middleware.metrics_middleware import MetricsMiddleware, create_metrics_endpoint

# Metrics are automatically collected for:
# - HTTP request duration and count
# - Database query performance  
# - Search operation metrics
# - Authentication metrics
# - Error rates and status codes
```

### Available Metrics

#### HTTP Metrics
```
# Request duration histogram
http_request_duration_seconds_bucket{method="GET", endpoint="/api/v1/search/candidates"}

# Request count by status
http_requests_total{method="POST", endpoint="/api/v1/auth/login", status="200"}

# Active request count
http_requests_active{endpoint="/api/v1/resumes/upload"}
```

#### Search Metrics
```
# Search request metrics (from search_metrics_collector)
search_requests_total{search_type="skills_match", user_type="user"}
search_request_duration_seconds{search_type="similar_candidates"}
search_results_count{search_type="colleagues"}
search_match_scores{search_type="skills_match"}

# Search performance
search_database_query_duration_seconds{operation="SELECT", table="candidates"}
search_cache_operations_total{operation="hit", cache_type="redis"}
```

#### Database Metrics
```
# Database connection pool
database_connections_active
database_connections_idle
database_query_duration_seconds{operation="INSERT", table="search_history"}

# Query performance
database_query_count{operation="SELECT", table="resumes"}
database_slow_queries_total{threshold="1s"}
```

#### Custom Application Metrics
```
# Resume processing
resume_processing_duration_seconds{status="completed"}
resume_parsing_errors_total{error_type="claude_api_timeout"}

# File operations
file_upload_size_bytes
file_processing_queue_length

# Authentication
auth_token_generation_duration_seconds
auth_failed_attempts_total{reason="invalid_password"}
```

### Metrics Endpoint Configuration

The metrics are exposed on a separate port for security:

```python
# In main.py, metrics are configured conditionally
if settings.enable_metrics:
    app.add_middleware(MetricsMiddleware, collect_body_size=True)
    metrics_router = create_metrics_endpoint()
    app.include_router(metrics_router, tags=["Monitoring"])
```

**Accessing Metrics**:
```bash
# Application metrics
curl http://localhost:9090/metrics

# Or through Kubernetes service
curl http://hr-api-service:9090/metrics
```

---

## Database Optimization

### Index Strategy

**Core Search Indexes**:
```sql
-- Skills-based search (GIN index for JSONB)
CREATE INDEX CONCURRENTLY idx_resume_skills_gin 
ON resumes USING gin (skills);

-- Candidate filtering
CREATE INDEX CONCURRENTLY idx_candidate_active_experience 
ON candidates (is_active, total_experience_years) 
WHERE is_active = true;

-- Work experience search
CREATE INDEX CONCURRENTLY idx_work_exp_company_dept 
ON work_experience (company, department);

-- Search history performance
CREATE INDEX CONCURRENTLY idx_search_history_user_type 
ON search_history (user_id, search_type, created_at);

-- Full-text search
CREATE INDEX CONCURRENTLY idx_resume_search_content 
ON resumes USING gin(to_tsvector('english', parsed_data::text));
```

**Composite Indexes for Complex Queries**:
```sql
-- Multi-criteria candidate search
CREATE INDEX CONCURRENTLY idx_candidate_search_composite 
ON candidates (is_active, total_experience_years, location) 
WHERE is_active = true;

-- Resume status with timestamps
CREATE INDEX CONCURRENTLY idx_resume_status_created 
ON resumes (parsing_status, created_at) 
WHERE parsing_status IN ('completed', 'processing');

-- Work experience date ranges
CREATE INDEX CONCURRENTLY idx_work_exp_dates_company 
ON work_experience (start_date, end_date, company) 
WHERE end_date IS NOT NULL;
```

### Query Optimization

**Connection Pool Configuration**:
```python
# api/database.py - Production settings
DATABASE_CONFIG = {
    "pool_size": 20,          # Base connections
    "max_overflow": 30,       # Additional connections  
    "pool_timeout": 30,       # Connection timeout
    "pool_recycle": 3600,     # Recycle connections hourly
    "pool_pre_ping": True,    # Validate connections
    "echo": False             # Disable query logging in prod
}
```

**Query Performance Monitoring**:
```sql
-- Monitor slow queries
SELECT 
    query,
    mean_time,
    calls,
    total_time,
    mean_time/calls as avg_time_per_call
FROM pg_stat_statements 
WHERE mean_time > 100  -- Queries slower than 100ms
ORDER BY mean_time DESC 
LIMIT 20;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
```

### Database Maintenance

**Automated Maintenance Script**:
```bash
#!/bin/bash
# database-maintenance.sh

# Weekly maintenance tasks
if [ $(date +%u) -eq 7 ]; then
    echo "🧹 Running weekly database maintenance..."
    
    # Vacuum and analyze
    psql $DATABASE_URL -c "VACUUM ANALYZE;"
    
    # Reindex if needed
    psql $DATABASE_URL -c "REINDEX DATABASE hr_resume_db;"
    
    # Update table statistics
    psql $DATABASE_URL -c "ANALYZE;"
    
    echo "✅ Weekly maintenance completed"
fi

# Daily cleanup
echo "🗑️ Running daily cleanup..."

# Remove old search history (older than 90 days)
psql $DATABASE_URL -c "
DELETE FROM search_history 
WHERE created_at < NOW() - INTERVAL '90 days';
"

# Clean up failed resume processing records (older than 7 days)
psql $DATABASE_URL -c "
DELETE FROM resumes 
WHERE parsing_status = 'failed' 
AND created_at < NOW() - INTERVAL '7 days';
"

echo "✅ Daily cleanup completed"
```

---

## Search Performance

### Search Metrics Integration

The search system includes comprehensive performance tracking:

```python
# From api/routers/search.py - Enhanced with metrics
from ..middleware.metrics_middleware import get_search_metrics_collector, get_db_metrics_tracker

@router.post("/candidates", response_model=SearchResponse)
async def search_candidates(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    search_metrics = get_search_metrics_collector()
    db_metrics = get_db_metrics_tracker(db)
    
    # Track search request performance
    with search_metrics.track_search_request(search_request.search_type.value, "user"):
        # Database queries are tracked automatically
        with db_metrics.track_query("SELECT", "candidates_resumes"):
            query = db.query(Candidate, Resume).join(...)
        
        # Record search results and performance
        search_metrics.record_search_results(
            search_request.search_type.value, 
            search_results, 
            match_scores
        )
```

### Search Algorithm Optimization

**Skills Matching Optimization**:
```python
# Optimized skills search with GIN index
def optimize_skills_search(skills: List[str], db: Session):
    # Use GIN index for fast JSONB containment
    skills_conditions = []
    for skill in skills:
        skills_conditions.append(
            func.jsonb_path_exists(
                Resume.skills,
                f'$[*] ? (@ like_regex "{skill}" flag "i")'
            )
        )
    return or_(*skills_conditions)

# Batch skill lookups
@lru_cache(maxsize=1000)
def get_skill_variations(skill: str) -> List[str]:
    """Cache skill variations for faster matching"""
    return [
        skill.lower(),
        skill.title(),
        skill.upper(),
        # Add common variations
    ]
```

**Experience Matching with Indexing**:
```python
def optimize_experience_query(min_exp: int, max_exp: int, db: Session):
    # Use covering index for experience range queries
    return db.query(Candidate).filter(
        Candidate.is_active == True,
        Candidate.total_experience_years.between(min_exp, max_exp)
    ).options(
        # Load only necessary columns
        load_only(Candidate.id, Candidate.uuid, Candidate.full_name)
    )
```

### Search Result Caching

**Redis Caching Strategy**:
```python
import redis.asyncio as redis
from functools import wraps

class SearchCacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = 300  # 5 minutes
    
    def cache_search_results(self, ttl: int = None):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from search parameters
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = await self.redis.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
                
                # Execute search
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.redis.setex(
                    cache_key,
                    ttl or self.default_ttl,
                    json.dumps(result, default=str)
                )
                
                return result
            return wrapper
        return decorator
    
    def _generate_cache_key(self, func_name: str, args, kwargs) -> str:
        # Create deterministic cache key
        key_data = {
            'function': func_name,
            'args': str(args),
            'kwargs': sorted(kwargs.items())
        }
        return f"search:{hash(str(key_data))}"

# Usage
cache_manager = SearchCacheManager(settings.redis_url)

@cache_manager.cache_search_results(ttl=600)  # 10 minutes
async def cached_candidate_search(search_params: SearchRequest):
    # Perform expensive search operation
    return search_results
```

---

## Caching Strategies

### Multi-Level Caching

**Level 1: Application Cache (LRU)**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_search_filters():
    """Cache frequently accessed search filters in memory"""
    return {
        "companies": get_top_companies(),
        "skills": get_popular_skills(),
        "departments": get_departments()
    }

@lru_cache(maxsize=500)
def calculate_candidate_score(candidate_id: str, search_criteria: str):
    """Cache expensive scoring calculations"""
    # Complex scoring logic here
    return calculated_score
```

**Level 2: Redis Cache (Distributed)**:
```python
class DistributedCache:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_or_set(self, key: str, fetch_func, ttl: int = 300):
        """Get from cache or fetch and set"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        
        # Fetch fresh data
        fresh_value = await fetch_func()
        await self.redis.setex(key, ttl, json.dumps(fresh_value, default=str))
        return fresh_value
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# Usage examples
cache = DistributedCache(redis_client)

# Cache search results
search_results = await cache.get_or_set(
    f"search:candidates:{hash(search_params)}",
    lambda: perform_candidate_search(search_params),
    ttl=600
)

# Cache user permissions
user_permissions = await cache.get_or_set(
    f"user:permissions:{user_id}",
    lambda: fetch_user_permissions(user_id),
    ttl=1800
)
```

**Level 3: Database Query Result Cache**:
```python
from sqlalchemy.orm import scoped_session
from sqlalchemy_cache import cache_region

# Configure SQLAlchemy query result caching
cache_region.configure(
    'dogpile.cache.redis',
    expiration_time=300,
    arguments={
        'host': 'redis-service',
        'port': 6379,
        'db': 1,
        'redis_expiration_time': 300,
        'distributed_lock': True
    }
)

# Cache expensive database queries
@cache_region.cache_on_arguments()
def get_company_candidates(company_name: str, department: str = None):
    """Cache company-based candidate queries"""
    query = session.query(Candidate).join(WorkExperience).filter(
        WorkExperience.company == company_name
    )
    if department:
        query = query.filter(WorkExperience.department == department)
    return query.all()
```

### Cache Invalidation Strategy

```python
class CacheInvalidator:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def invalidate_search_caches(self, candidate_id: str = None):
        """Invalidate search-related caches"""
        patterns = [
            "search:candidates:*",
            "search:similar:*",
            "search:filters:*"
        ]
        
        if candidate_id:
            patterns.extend([
                f"candidate:{candidate_id}:*",
                f"similar:{candidate_id}:*"
            ])
        
        for pattern in patterns:
            await self._invalidate_pattern(pattern)
    
    async def invalidate_on_resume_update(self, resume_id: str, candidate_id: str):
        """Invalidate caches when resume is updated"""
        await self.invalidate_search_caches(candidate_id)
        
        # Invalidate specific resume caches
        await self._invalidate_pattern(f"resume:{resume_id}:*")
        
        # Invalidate skill-based caches
        await self._invalidate_pattern("skills:*")
    
    async def _invalidate_pattern(self, pattern: str):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

---

## API Optimization

### Response Optimization

**Gzip Compression**:
```python
from fastapi.middleware.gzip import GZipMiddleware

# Enable response compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Response Field Selection**:
```python
from pydantic import BaseModel
from typing import Optional, List

class OptimizedSearchResult(BaseModel):
    """Lightweight search result for better performance"""
    candidate_id: str
    full_name: str
    match_score: float
    
    # Optional fields for detailed view
    current_position: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None

@router.post("/candidates/lightweight")
async def search_candidates_lightweight(
    search_request: SearchRequest,
    include_details: bool = Query(False)
) -> List[OptimizedSearchResult]:
    """Optimized endpoint with selective field loading"""
    query = build_search_query(search_request)
    
    if include_details:
        # Load all fields
        results = query.options(joinedload(Candidate.work_experiences)).all()
    else:
        # Load only essential fields
        results = query.options(
            load_only(Candidate.id, Candidate.uuid, Candidate.full_name)
        ).all()
    
    return build_lightweight_response(results, include_details)
```

### Async Optimization

**Concurrent Operations**:
```python
import asyncio
from typing import Dict, Any

async def optimized_search_with_aggregations(
    search_request: SearchRequest,
    db: Session
) -> Dict[str, Any]:
    """Perform search and aggregations concurrently"""
    
    # Execute multiple operations concurrently
    results = await asyncio.gather(
        # Main search
        perform_candidate_search(search_request, db),
        
        # Get search filters concurrently
        get_available_filters_async(db),
        
        # Get search analytics
        get_search_analytics_async(search_request.search_type),
        
        # Get recommended searches
        get_recommended_searches_async(search_request),
        
        return_exceptions=True
    )
    
    # Unpack results
    candidates, filters, analytics, recommendations = results
    
    return {
        "candidates": candidates if not isinstance(candidates, Exception) else [],
        "filters": filters if not isinstance(filters, Exception) else {},
        "analytics": analytics if not isinstance(analytics, Exception) else {},
        "recommendations": recommendations if not isinstance(recommendations, Exception) else []
    }
```

**Background Task Processing**:
```python
from fastapi import BackgroundTasks

@router.post("/resumes/upload")
async def upload_resume(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Optimized upload with background processing"""
    
    # Quick file validation and storage
    file_info = await store_file_quickly(file)
    
    # Queue background processing
    background_tasks.add_task(
        process_resume_async,
        file_info.file_id,
        current_user.id
    )
    
    # Return immediately
    return {
        "file_id": file_info.file_id,
        "status": "processing",
        "estimated_completion": calculate_eta()
    }

async def process_resume_async(file_id: str, user_id: int):
    """Background resume processing"""
    try:
        # Process with Claude AI
        await claude_service.process_resume(file_id)
        
        # Update search indexes
        await update_search_indexes(file_id)
        
        # Invalidate relevant caches
        await cache_invalidator.invalidate_search_caches()
        
        # Send notification (optional)
        await notify_user_processing_complete(user_id, file_id)
        
    except Exception as e:
        logger.error(f"Resume processing failed: {e}")
        await mark_processing_failed(file_id, str(e))
```

---

## Load Testing

### Performance Test Suite

**Basic Load Test**:
```python
# tests/load/test_api_performance.py
import asyncio
import aiohttp
import time
from statistics import mean, median

class LoadTester:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.auth_token = auth_token
        self.results = []
    
    async def test_endpoint_performance(
        self, 
        endpoint: str, 
        method: str = "GET",
        concurrent_requests: int = 50,
        total_requests: int = 1000,
        payload: dict = None
    ):
        """Load test a specific endpoint"""
        
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_request(session):
            async with semaphore:
                start_time = time.time()
                try:
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    async with session.request(
                        method, 
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        json=payload
                    ) as response:
                        await response.text()
                        duration = time.time() - start_time
                        return {
                            "duration": duration,
                            "status": response.status,
                            "success": response.status < 400
                        }
                except Exception as e:
                    return {
                        "duration": time.time() - start_time,
                        "status": 0,
                        "success": False,
                        "error": str(e)
                    }
        
        # Execute load test
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session) for _ in range(total_requests)]
            results = await asyncio.gather(*tasks)
        
        # Analyze results
        return self._analyze_results(results, endpoint)
    
    def _analyze_results(self, results: list, endpoint: str) -> dict:
        """Analyze load test results"""
        durations = [r["duration"] for r in results if r["success"]]
        success_count = sum(1 for r in results if r["success"])
        
        return {
            "endpoint": endpoint,
            "total_requests": len(results),
            "successful_requests": success_count,
            "success_rate": success_count / len(results) * 100,
            "average_response_time": mean(durations) if durations else 0,
            "median_response_time": median(durations) if durations else 0,
            "min_response_time": min(durations) if durations else 0,
            "max_response_time": max(durations) if durations else 0,
            "requests_per_second": len(results) / sum(durations) if durations else 0
        }

# Usage
async def run_performance_tests():
    tester = LoadTester("http://localhost:8000", "your-auth-token")
    
    # Test search endpoint
    search_payload = {
        "query": "Python developer",
        "skills": ["Python", "FastAPI"],
        "limit": 10
    }
    
    search_results = await tester.test_endpoint_performance(
        "/api/v1/search/candidates",
        method="POST",
        concurrent_requests=50,
        total_requests=1000,
        payload=search_payload
    )
    
    print(f"Search Performance: {search_results}")
    
    # Test authentication
    auth_results = await tester.test_endpoint_performance(
        "/api/v1/auth/me",
        concurrent_requests=100,
        total_requests=2000
    )
    
    print(f"Auth Performance: {auth_results}")
```

**Stress Test Configuration**:
```bash
#!/bin/bash
# stress-test.sh

echo "🚀 Starting stress test..."

# Test different load levels
LOAD_LEVELS=(10 50 100 200 500)

for load in "${LOAD_LEVELS[@]}"; do
    echo "Testing with $load concurrent users..."
    
    # Use Apache Bench for HTTP load testing
    ab -n 10000 -c $load -H "Authorization: Bearer $AUTH_TOKEN" \
       -T "application/json" \
       -p search_payload.json \
       http://localhost:8000/api/v1/search/candidates
    
    echo "Waiting for system recovery..."
    sleep 30
done

echo "✅ Stress test completed"
```

### Performance Benchmarks

**Expected Performance Thresholds**:
```yaml
performance_thresholds:
  health_check:
    target_response_time: 50ms
    max_response_time: 100ms
    success_rate: 99.9%
  
  authentication:
    target_response_time: 200ms
    max_response_time: 500ms
    success_rate: 99.5%
  
  search_simple:
    target_response_time: 500ms
    max_response_time: 1000ms
    success_rate: 98%
  
  search_complex:
    target_response_time: 1000ms
    max_response_time: 2000ms
    success_rate: 95%
  
  file_upload:
    target_response_time: 2000ms
    max_response_time: 5000ms
    success_rate: 95%

load_test_scenarios:
  normal_load:
    concurrent_users: 50
    requests_per_second: 100
    duration: 5_minutes
  
  peak_load:
    concurrent_users: 200
    requests_per_second: 500
    duration: 2_minutes
  
  stress_test:
    concurrent_users: 500
    requests_per_second: 1000
    duration: 1_minute
```

---

## Troubleshooting

### Performance Issue Diagnosis

**1. High Response Times**:

```bash
# Check current performance metrics
curl http://localhost:9090/metrics | grep http_request_duration

# Database query analysis
psql $DATABASE_URL -c "
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
WHERE mean_time > 500 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Check for lock contention
psql $DATABASE_URL -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;
"
```

**2. Memory Issues**:

```bash
# Check memory usage
kubectl top pods -n hr-system

# Analyze memory patterns in application
curl http://localhost:9090/metrics | grep process_resident_memory

# Database memory analysis
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins + n_tup_upd + n_tup_del as total_writes,
    n_tup_hot_upd,
    n_live_tup,
    n_dead_tup
FROM pg_stat_user_tables 
ORDER BY total_writes DESC;
"
```

**3. Search Performance Issues**:

```python
# Search performance debugging
async def debug_search_performance(search_request: SearchRequest):
    """Debug slow search queries"""
    
    start_time = time.time()
    debug_info = {}
    
    # Query building time
    query_start = time.time()
    query = build_search_query(search_request)
    debug_info["query_build_time"] = time.time() - query_start
    
    # Database execution time
    db_start = time.time()
    results = query.all()
    debug_info["db_execution_time"] = time.time() - db_start
    
    # Result processing time
    process_start = time.time()
    processed_results = process_search_results(results)
    debug_info["processing_time"] = time.time() - process_start
    
    debug_info["total_time"] = time.time() - start_time
    debug_info["result_count"] = len(results)
    
    # Log performance data
    logger.info(f"Search performance debug: {debug_info}")
    
    return processed_results, debug_info
```

### Common Performance Issues

**Issue: Slow Database Queries**
```sql
-- Solution: Add missing indexes
EXPLAIN ANALYZE SELECT * FROM candidates 
WHERE total_experience_years BETWEEN 5 AND 10 
AND location = 'San Francisco';

-- If table scan detected, add index:
CREATE INDEX CONCURRENTLY idx_candidate_exp_location 
ON candidates (total_experience_years, location);
```

**Issue: High Memory Usage in Search**
```python
# Solution: Implement pagination and limiting
@router.post("/search/candidates")
async def search_candidates_optimized(
    search_request: SearchRequest,
    limit: int = Query(default=50, le=100),  # Enforce max limit
    offset: int = Query(default=0, ge=0)
):
    # Always apply limits to prevent memory issues
    query = build_search_query(search_request)
    total_count = query.count()
    
    # Apply pagination
    results = query.offset(offset).limit(limit).all()
    
    return {
        "results": results,
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total_count
    }
```

**Issue: Cache Miss Rate Too High**
```python
# Solution: Improve cache key strategy
class ImprovedCacheKeyGenerator:
    @staticmethod
    def generate_search_key(search_request: SearchRequest) -> str:
        """Generate stable cache keys for searches"""
        # Normalize search parameters for better cache hits
        normalized_params = {
            "skills": sorted(search_request.skills or []),
            "experience_min": search_request.min_experience_years,
            "experience_max": search_request.max_experience_years,
            "companies": sorted(search_request.companies or []),
            "departments": sorted(search_request.departments or []),
            "location": search_request.locations[0] if search_request.locations else None
        }
        
        # Remove None values
        normalized_params = {k: v for k, v in normalized_params.items() if v is not None}
        
        return f"search:candidates:{hash(str(sorted(normalized_params.items())))}"
```

---

## Monitoring Dashboards

### Grafana Dashboard Configuration

**HR Resume API Dashboard**:
```json
{
  "dashboard": {
    "title": "HR Resume Search API - Performance Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec",
            "min": 0
          }
        ]
      },
      {
        "title": "Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
            "legendFormat": "{{endpoint}} - 95th"
          },
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
            "legendFormat": "{{endpoint}} - 50th"
          }
        ],
        "yAxes": [
          {
            "label": "Seconds",
            "min": 0
          }
        ]
      },
      {
        "title": "Search Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(search_requests_total[5m])",
            "legendFormat": "Search Requests/sec"
          },
          {
            "expr": "histogram_quantile(0.95, rate(search_request_duration_seconds_bucket[5m]))",
            "legendFormat": "Search Response Time (95th)"
          }
        ]
      },
      {
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(database_query_count[5m])",
            "legendFormat": "DB Queries/sec"
          },
          {
            "expr": "histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m]))",
            "legendFormat": "DB Query Time (95th)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "thresholds": "1,5",
        "colorBackground": true
      },
      {
        "title": "Cache Hit Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(search_cache_operations_total{operation=\"hit\"}[5m])) / sum(rate(search_cache_operations_total[5m])) * 100",
            "legendFormat": "Cache Hit Rate %"
          }
        ],
        "thresholds": "70,80",
        "colorBackground": true
      }
    ]
  }
}
```

### Alert Rules

**Prometheus Alert Configuration**:
```yaml
# alerts/hr-api-alerts.yml
groups:
- name: hr-api-performance
  rules:
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API response time detected"
      description: "95th percentile response time is {{ $value }}s"

  - alert: HighErrorRate
    expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100 > 5
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }}%"

  - alert: DatabaseSlowQueries
    expr: rate(database_slow_queries_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Database slow queries detected"
      description: "{{ $value }} slow queries per second"

  - alert: SearchPerformanceDegraded
    expr: histogram_quantile(0.95, rate(search_request_duration_seconds_bucket[5m])) > 1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Search performance degraded"
      description: "Search response time is {{ $value }}s"

  - alert: MemoryUsageHigh
    expr: process_resident_memory_bytes / (1024*1024*1024) > 1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value }}GB"
```

---

## Performance Optimization Checklist

### Database Optimization
- [ ] All search indexes created and optimized
- [ ] Connection pooling configured appropriately
- [ ] Query performance monitored and optimized
- [ ] Database maintenance scheduled
- [ ] Slow query alerts configured

### Application Performance
- [ ] Response compression enabled
- [ ] Caching strategy implemented
- [ ] Background task processing configured
- [ ] Resource limits set appropriately
- [ ] Async operations optimized

### Search Performance
- [ ] Search result caching implemented
- [ ] Pagination enforced
- [ ] Search metrics collection enabled
- [ ] Query optimization applied
- [ ] Search filters cached

### Monitoring & Alerting
- [ ] Prometheus metrics configured
- [ ] Grafana dashboards created
- [ ] Performance alerts configured
- [ ] Load testing scheduled
- [ ] Performance baselines established

---

## Next Steps

1. **API Reference**: See `/docs/api_reference.md` for endpoint documentation
2. **Deployment Guide**: See `/docs/deployment.md` for production deployment
3. **MCP Integration**: See `/docs/mcp_integration.md` for MCP server optimization
4. **Examples**: See `/docs/examples/` for performance testing examples

For advanced performance tuning, consider implementing database read replicas, CDN for static assets, and microservice architecture for high-scale deployments.