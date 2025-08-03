"""
FastAPI Application - Main Entry Point
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
import json
from typing import Any, Dict
from datetime import datetime
import traceback

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import routers
from .routers import auth, search, resumes
from .database import init_db, check_db_connection
from .config import settings

# Configure logging with JSON format for production
if settings.is_production:
    from pythonjsonlogger import jsonlogger
    
    # JSON logger for production (Loki compatible)
    json_handler = logging.StreamHandler()
    json_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    json_handler.setFormatter(json_formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        handlers=[json_handler]
    )
else:
    # Human-readable logging for development
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager with comprehensive startup/shutdown
    """
    # Startup
    logger.info("Starting API Builder application", extra={
        "environment": settings.environment,
        "debug": settings.debug,
        "version": "1.0.0"
    })
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
        
        # Test database connection
        if check_db_connection():
            logger.info("Database connection verified")
        else:
            logger.warning("Database connection test failed")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # TODO: Initialize Redis connection when implemented
    # TODO: Initialize MCP server connection when implemented
    
    # Log startup completion
    logger.info("Application startup completed successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Builder application")
    # TODO: Close database connections
    # TODO: Close Redis connections  
    # TODO: Close MCP server connections
    logger.info("Application shutdown completed")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="HR Resume Search API with MCP Server Integration",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    debug=settings.debug
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middleware for production
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # TODO: Configure with actual allowed hosts
    )

# Configure CORS from environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    Log all HTTP requests with timing and response status
    """
    start_time = time.time()
    
    # Extract request info
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "client_ip": get_remote_address(request),
        "user_agent": request.headers.get("user-agent", ""),
        "content_length": request.headers.get("content-length", 0)
    }
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request with response info
        log_data = {
            **request_info,
            "status_code": response.status_code,
            "process_time": round(process_time * 1000, 2),  # ms
            "response_size": response.headers.get("content-length", 0)
        }
        
        # Use different log levels based on status code
        if response.status_code >= 500:
            logger.error("HTTP Request", extra=log_data)
        elif response.status_code >= 400:
            logger.warning("HTTP Request", extra=log_data)
        else:
            logger.info("HTTP Request", extra=log_data)
            
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-API-Version"] = settings.app_version
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        error_log = {
            **request_info,
            "error": str(e),
            "process_time": round(process_time * 1000, 2),
            "traceback": traceback.format_exc()
        }
        
        logger.error("HTTP Request Error", extra=error_log)
        raise


# Comprehensive error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with detailed logging
    """
    error_detail = {
        "error": "HTTP Exception",
        "status_code": exc.status_code,
        "detail": exc.detail,
        "path": request.url.path,
        "method": request.method,
        "client_ip": get_remote_address(request)
    }
    
    logger.warning("HTTP Exception", extra=error_detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_exception",
                "status_code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors
    """
    error_detail = {
        "error": "Validation Error",
        "path": request.url.path,
        "method": request.method,
        "validation_errors": exc.errors(),
        "client_ip": get_remote_address(request)
    }
    
    logger.warning("Validation Error", extra=error_detail)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions
    """
    error_detail = {
        "error": "Internal Server Error",
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "path": request.url.path,
        "method": request.method,
        "client_ip": get_remote_address(request),
        "traceback": traceback.format_exc() if settings.is_development else None
    }
    
    logger.error("Unhandled Exception", extra=error_detail)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_server_error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "details": str(exc) if settings.is_development else "Contact support for assistance"
            }
        }
    )

# Include routers with rate limiting
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(resumes.router)


@app.get("/", tags=["Root"])
@limiter.limit("100/minute")
async def root(request: Request) -> Dict[str, str]:
    """
    Root endpoint with API information
    """
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if settings.is_development else "Not available in production",
        "endpoints": {
            "health": "/health",
            "readiness": "/readiness",
            "auth": "/api/v1/auth",
            "resumes": "/api/v1/resumes", 
            "search": "/api/v1/search"
        }
    }


@app.get("/health", tags=["Health"])
@limiter.limit("200/minute") 
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint - lightweight check
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/readiness", tags=["Health"])
@limiter.limit("50/minute")
async def readiness_check(request: Request) -> Dict[str, Any]:
    """
    Readiness check endpoint - comprehensive health check
    """
    start_time = time.time()
    checks = {}
    overall_status = "ready"
    
    # Check database connectivity
    try:
        db_start = time.time()
        if check_db_connection():
            checks["database"] = {
                "status": "healthy",
                "response_time_ms": round((time.time() - db_start) * 1000, 2)
            }
        else:
            checks["database"] = {
                "status": "unhealthy", 
                "response_time_ms": round((time.time() - db_start) * 1000, 2)
            }
            overall_status = "not_ready"
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        checks["database"] = {
            "status": "error",
            "error": str(e),
            "response_time_ms": round((time.time() - db_start) * 1000, 2)
        }
        overall_status = "not_ready"
    
    # Check Redis connectivity if configured
    if settings.redis_url:
        try:
            import redis
            redis_start = time.time()
            r = redis.from_url(settings.redis_url)
            r.ping()
            checks["redis"] = {
                "status": "healthy",
                "response_time_ms": round((time.time() - redis_start) * 1000, 2)
            }
        except Exception as e:
            logger.warning(f"Redis check failed: {e}")
            checks["redis"] = {
                "status": "error",
                "error": str(e),
                "response_time_ms": round((time.time() - redis_start) * 1000, 2)
            }
            # Redis is optional, don't fail readiness check
    else:
        checks["redis"] = {"status": "not_configured"}
    
    # Check MCP server connectivity if configured  
    if settings.mcp_server_url:
        try:
            import httpx
            mcp_start = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.mcp_server_url}/health",
                    timeout=5.0
                )
                if response.status_code == 200:
                    checks["mcp_server"] = {
                        "status": "healthy",
                        "response_time_ms": round((time.time() - mcp_start) * 1000, 2)
                    }
                else:
                    checks["mcp_server"] = {
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "response_time_ms": round((time.time() - mcp_start) * 1000, 2)
                    }
        except Exception as e:
            logger.warning(f"MCP server check failed: {e}")
            checks["mcp_server"] = {
                "status": "error",
                "error": str(e),
                "response_time_ms": round((time.time() - mcp_start) * 1000, 2)
            }
    else:
        checks["mcp_server"] = {"status": "not_configured"}
    
    total_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": overall_status,
        "checks": checks,
        "total_check_time_ms": total_time,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics", tags=["Monitoring"])
@limiter.limit("10/minute")
async def metrics_endpoint(request: Request) -> Dict[str, Any]:
    """
    Basic metrics endpoint for monitoring
    """
    try:
        from .database import SessionLocal
        from .models import Resume, Candidate, User
        
        db = SessionLocal()
        try:
            # Get basic counts
            total_users = db.query(User).count()
            total_candidates = db.query(Candidate).count() 
            total_resumes = db.query(Resume).count()
            
            # Resume status breakdown
            resume_stats = db.query(Resume.status, db.func.count(Resume.id)).group_by(Resume.status).all()
            
            return {
                "service": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
                "metrics": {
                    "users_total": total_users,
                    "candidates_total": total_candidates,
                    "resumes_total": total_resumes,
                    "resume_status": {status: count for status, count in resume_stats}
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "error": "Failed to collect metrics",
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )