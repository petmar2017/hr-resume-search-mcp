"""
FastAPI Middleware for Prometheus Metrics Collection
Automatically tracks API request metrics
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from ..services.metrics_service import metrics_service

logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect Prometheus metrics"""
    
    def __init__(self, app, collect_body_size: bool = True):
        super().__init__(app)
        self.collect_body_size = collect_body_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics"""
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Skip metrics collection for metrics endpoint itself
        if path == "/metrics" or path.startswith("/metrics/"):
            return await call_next(request)
        
        # Collect request size if enabled
        request_size = 0
        if self.collect_body_size and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request_size = len(body)
                metrics_service.api_request_size.labels(
                    method=method, 
                    endpoint=path
                ).observe(request_size)
                
                # Re-create request with body for downstream processing
                from starlette.requests import Request as StarletteRequest
                
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request = StarletteRequest(request.scope, receive)
            except Exception as e:
                logger.warning(f"Could not collect request size: {e}")
        
        # Process request
        status_code = 500  # Default to error
        response_size = 0
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Collect response size if possible
            if self.collect_body_size and hasattr(response, 'body'):
                try:
                    if hasattr(response, 'body'):
                        response_body = response.body
                        if response_body:
                            response_size = len(response_body)
                            metrics_service.api_response_size.labels(
                                method=method, 
                                endpoint=path
                            ).observe(response_size)
                except Exception as e:
                    logger.warning(f"Could not collect response size: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            status_code = 500
            raise
        
        finally:
            # Always collect timing and count metrics
            duration = time.time() - start_time
            
            # Record request count
            metrics_service.api_requests_total.labels(
                method=method,
                endpoint=path,
                status_code=status_code
            ).inc()
            
            # Record request duration
            metrics_service.api_request_duration.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            # Log slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                logger.warning(
                    f"Slow request: {method} {path} took {duration:.3f}s "
                    f"(status: {status_code}, req_size: {request_size}, resp_size: {response_size})"
                )

class DatabaseMetricsMiddleware:
    """Database query metrics collection"""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def track_query(self, query_type: str, table: str):
        """Return context manager for tracking database queries"""
        return metrics_service.track_db_query(query_type, table)

class SearchMetricsCollector:
    """Helper class for collecting search-specific metrics"""
    
    @staticmethod
    def track_search_request(search_type: str, user_type: str = "user"):
        """Track search request metrics"""
        return metrics_service.track_search_request(search_type, user_type)
    
    @staticmethod
    def record_search_results(search_type: str, results: list, match_scores: list = None):
        """Record search result metrics"""
        result_count = len(results)
        if match_scores is None:
            match_scores = [getattr(result, 'match_score', 0.0) for result in results]
        
        metrics_service.record_search_results(search_type, result_count, match_scores)
    
    @staticmethod
    def record_cache_hit(cache_type: str):
        """Record cache hit"""
        metrics_service.record_cache_operation("get", cache_type, True)
    
    @staticmethod
    def record_cache_miss(cache_type: str):
        """Record cache miss"""
        metrics_service.record_cache_operation("get", cache_type, False)
    
    @staticmethod
    def record_user_interaction(interaction_type: str, position: int):
        """Record user interaction with search results"""
        metrics_service.record_user_interaction(interaction_type, position)

class ResumeMetricsCollector:
    """Helper class for collecting resume processing metrics"""
    
    @staticmethod
    def track_parsing(file_type: str):
        """Track resume parsing"""
        return metrics_service.track_resume_parsing(file_type)
    
    @staticmethod
    def record_file_upload(file_type: str, file_size: int):
        """Record file upload metrics"""
        metrics_service.record_file_upload(file_type, file_size)

# Helper functions for easy integration
def get_db_metrics_tracker(db_session):
    """Get database metrics tracker for a session"""
    return DatabaseMetricsMiddleware(db_session)

def get_search_metrics_collector():
    """Get search metrics collector"""
    return SearchMetricsCollector()

def get_resume_metrics_collector():
    """Get resume metrics collector"""
    return ResumeMetricsCollector()

def create_metrics_endpoint():
    """Create FastAPI endpoint for Prometheus metrics"""
    from fastapi import APIRouter
    from fastapi.responses import Response
    
    router = APIRouter()
    
    @router.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        from prometheus_client import CONTENT_TYPE_LATEST
        
        metrics_data = metrics_service.get_metrics()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    
    @router.get("/metrics/summary")
    async def metrics_summary():
        """Human-readable metrics summary"""
        return metrics_service.generate_metrics_summary()
    
    return router