"""
Prometheus Metrics Service for HR Resume Search
Collects performance and quality metrics for monitoring
"""

import time
import logging
from typing import Dict, Any, Optional, List
from functools import wraps
from contextlib import contextmanager
from datetime import datetime, timedelta

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    start_http_server, generate_latest, CONTENT_TYPE_LATEST
)
from fastapi import Request, Response
from sqlalchemy.orm import Session

from ..config import get_settings

logger = logging.getLogger(__name__)

class MetricsService:
    """Prometheus metrics collection service"""
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_metrics()
        self._server_started = False
    
    def _setup_metrics(self):
        """Initialize all Prometheus metrics"""
        
        # === API Performance Metrics ===
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'Time spent processing API requests',
            ['method', 'endpoint'],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        )
        
        self.api_request_size = Histogram(
            'api_request_size_bytes',
            'Size of API requests in bytes',
            ['method', 'endpoint']
        )
        
        self.api_response_size = Histogram(
            'api_response_size_bytes',
            'Size of API responses in bytes',
            ['method', 'endpoint']
        )
        
        # === Database Performance Metrics ===
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Time spent executing database queries',
            ['query_type', 'table'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        )
        
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total number of database queries',
            ['query_type', 'table', 'status']
        )
        
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Number of active database connections'
        )
        
        self.db_connection_pool_size = Gauge(
            'db_connection_pool_size',
            'Database connection pool size'
        )
        
        # === Search Performance Metrics ===
        self.search_requests_total = Counter(
            'search_requests_total',
            'Total number of search requests',
            ['search_type', 'user_type']
        )
        
        self.search_duration = Histogram(
            'search_duration_seconds',
            'Time spent processing search requests',
            ['search_type'],
            buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.search_results_count = Histogram(
            'search_results_count',
            'Number of results returned by searches',
            ['search_type'],
            buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500, 1000]
        )
        
        self.search_cache_hits = Counter(
            'search_cache_hits_total',
            'Number of search cache hits',
            ['cache_type']
        )
        
        self.search_cache_misses = Counter(
            'search_cache_misses_total',
            'Number of search cache misses',
            ['cache_type']
        )
        
        # === Search Quality Metrics ===
        self.search_match_scores = Histogram(
            'search_match_scores',
            'Distribution of search match scores',
            ['search_type'],
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        self.search_zero_results = Counter(
            'search_zero_results_total',
            'Number of searches returning zero results',
            ['search_type']
        )
        
        self.search_user_interactions = Counter(
            'search_user_interactions_total',
            'User interactions with search results',
            ['interaction_type', 'result_position']
        )
        
        # === Resume Processing Metrics ===
        self.resume_parsing_duration = Histogram(
            'resume_parsing_duration_seconds',
            'Time spent parsing resumes',
            ['file_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.resume_parsing_total = Counter(
            'resume_parsing_total',
            'Total number of resume parsing attempts',
            ['status', 'file_type']
        )
        
        self.resume_file_size = Histogram(
            'resume_file_size_bytes',
            'Size of uploaded resume files',
            ['file_type'],
            buckets=[1024, 10240, 102400, 1048576, 10485760]  # 1KB to 10MB
        )
        
        self.resume_processing_errors = Counter(
            'resume_processing_errors_total',
            'Number of resume processing errors',
            ['error_type', 'file_type']
        )
        
        # === System Health Metrics ===
        self.system_uptime = Gauge(
            'system_uptime_seconds',
            'System uptime in seconds'
        )
        
        self.active_users = Gauge(
            'active_users_count',
            'Number of active users',
            ['time_window']
        )
        
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['type']
        )
        
        # === Cache Performance Metrics ===
        self.cache_operations = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'cache_type', 'status']
        )
        
        self.cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate percentage',
            ['cache_type']
        )
        
        self.cache_size = Gauge(
            'cache_size_entries',
            'Number of entries in cache',
            ['cache_type']
        )
        
        # === Application Info ===
        self.app_info = Info(
            'application_info',
            'Application information'
        )
        
        # Set application info
        self.app_info.info({
            'name': self.settings.app_name,
            'version': self.settings.app_version,
            'environment': self.settings.environment
        })
        
        logger.info("✅ Prometheus metrics initialized")
    
    def start_metrics_server(self, port: int = 9090):
        """Start Prometheus metrics HTTP server"""
        if not self._server_started:
            try:
                start_http_server(port)
                self._server_started = True
                logger.info(f"✅ Prometheus metrics server started on port {port}")
            except Exception as e:
                logger.error(f"❌ Failed to start metrics server: {e}")
    
    def get_metrics(self) -> str:
        """Get current metrics in Prometheus format"""
        return generate_latest()
    
    # === Decorators for automatic metrics collection ===
    
    def track_api_request(self, func):
        """Decorator to track API request metrics"""
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            method = request.method
            path = request.url.path
            start_time = time.time()
            
            # Track request size
            if hasattr(request, 'body'):
                request_body = await request.body()
                self.api_request_size.labels(method=method, endpoint=path).observe(len(request_body))
            
            try:
                response = await func(request, *args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                
                # Track response metrics
                self.api_requests_total.labels(
                    method=method, 
                    endpoint=path, 
                    status_code=status_code
                ).inc()
                
                # Track response size
                if hasattr(response, 'body'):
                    self.api_response_size.labels(method=method, endpoint=path).observe(len(response.body))
                
                return response
                
            except Exception as e:
                self.api_requests_total.labels(
                    method=method, 
                    endpoint=path, 
                    status_code=500
                ).inc()
                raise
            finally:
                # Track duration
                duration = time.time() - start_time
                self.api_request_duration.labels(method=method, endpoint=path).observe(duration)
        
        return wrapper
    
    @contextmanager
    def track_db_query(self, query_type: str, table: str):
        """Context manager to track database query metrics"""
        start_time = time.time()
        try:
            yield
            # Success
            self.db_queries_total.labels(
                query_type=query_type, 
                table=table, 
                status='success'
            ).inc()
        except Exception as e:
            # Error
            self.db_queries_total.labels(
                query_type=query_type, 
                table=table, 
                status='error'
            ).inc()
            raise
        finally:
            # Duration
            duration = time.time() - start_time
            self.db_query_duration.labels(query_type=query_type, table=table).observe(duration)
    
    @contextmanager
    def track_search_request(self, search_type: str, user_type: str = 'user'):
        """Context manager to track search request metrics"""
        start_time = time.time()
        try:
            yield
            self.search_requests_total.labels(search_type=search_type, user_type=user_type).inc()
        finally:
            duration = time.time() - start_time
            self.search_duration.labels(search_type=search_type).observe(duration)
    
    @contextmanager
    def track_resume_parsing(self, file_type: str):
        """Context manager to track resume parsing metrics"""
        start_time = time.time()
        try:
            yield
            self.resume_parsing_total.labels(status='success', file_type=file_type).inc()
        except Exception as e:
            self.resume_parsing_total.labels(status='error', file_type=file_type).inc()
            # Track specific error types
            error_type = type(e).__name__
            self.resume_processing_errors.labels(error_type=error_type, file_type=file_type).inc()
            raise
        finally:
            duration = time.time() - start_time
            self.resume_parsing_duration.labels(file_type=file_type).observe(duration)
    
    # === Manual metric recording methods ===
    
    def record_search_results(self, search_type: str, result_count: int, match_scores: List[float]):
        """Record search result metrics"""
        self.search_results_count.labels(search_type=search_type).observe(result_count)
        
        if result_count == 0:
            self.search_zero_results.labels(search_type=search_type).inc()
        
        # Record match score distribution
        for score in match_scores:
            self.search_match_scores.labels(search_type=search_type).observe(score)
    
    def record_cache_operation(self, operation: str, cache_type: str, success: bool):
        """Record cache operation metrics"""
        status = 'success' if success else 'error'
        self.cache_operations.labels(
            operation=operation, 
            cache_type=cache_type, 
            status=status
        ).inc()
        
        # Update hit/miss counters for get operations
        if operation == 'get':
            if success:
                self.search_cache_hits.labels(cache_type=cache_type).inc()
            else:
                self.search_cache_misses.labels(cache_type=cache_type).inc()
    
    def record_user_interaction(self, interaction_type: str, result_position: int):
        """Record user interaction with search results"""
        self.search_user_interactions.labels(
            interaction_type=interaction_type,
            result_position=str(result_position)
        ).inc()
    
    def record_file_upload(self, file_type: str, file_size: int):
        """Record file upload metrics"""
        self.resume_file_size.labels(file_type=file_type).observe(file_size)
    
    def update_system_metrics(self, db_session: Optional[Session] = None):
        """Update system health metrics"""
        try:
            # Update uptime (would need to track start time)
            # self.system_uptime.set(time.time() - start_time)
            
            # Update database connection metrics
            if db_session and hasattr(db_session, 'bind'):
                pool = db_session.bind.pool
                if hasattr(pool, 'size'):
                    self.db_connection_pool_size.set(pool.size())
                if hasattr(pool, 'checkedout'):
                    self.db_connections_active.set(pool.checkedout())
            
            # Update memory usage (basic implementation)
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            self.memory_usage.labels(type='rss').set(memory_info.rss)
            self.memory_usage.labels(type='vms').set(memory_info.vms)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def update_cache_metrics(self, cache_stats: Dict[str, Any]):
        """Update cache performance metrics"""
        try:
            for cache_type, stats in cache_stats.items():
                if 'hit_rate' in stats:
                    self.cache_hit_rate.labels(cache_type=cache_type).set(stats['hit_rate'])
                if 'size' in stats:
                    self.cache_size.labels(cache_type=cache_type).set(stats['size'])
        except Exception as e:
            logger.error(f"Error updating cache metrics: {e}")
    
    def generate_metrics_summary(self) -> Dict[str, Any]:
        """Generate a summary of current metrics"""
        try:
            from prometheus_client.parser import text_string_to_metric_families
            
            metrics_text = self.get_metrics().decode('utf-8')
            metrics_data = {}
            
            for family in text_string_to_metric_families(metrics_text):
                metrics_data[family.name] = {
                    'type': family.type,
                    'help': family.documentation,
                    'samples': len(family.samples)
                }
            
            return {
                'total_metrics': len(metrics_data),
                'metrics': metrics_data,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {'error': str(e)}

# Global metrics service instance
metrics_service = MetricsService()