#!/usr/bin/env python3
"""
Minimal FastAPI application for testing core infrastructure
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
from typing import Any, Dict
from datetime import datetime

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting minimal API application")
    yield
    logger.info("Shutting down minimal API application")


# Initialize FastAPI application
app = FastAPI(
    title="API Builder - Minimal",
    description="Minimal API for testing infrastructure",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request) -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "API Builder - Minimal is running",
        "version": "1.0.0",
        "environment": "test",
        "endpoints": {
            "health": "/health",
            "readiness": "/readiness",
            "metrics": "/metrics"
        }
    }


@app.get("/health")
@limiter.limit("200/minute") 
async def health_check(request: Request) -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-builder-minimal",
        "version": "1.0.0",
        "environment": "test",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/readiness")
@limiter.limit("50/minute")
async def readiness_check(request: Request) -> Dict[str, Any]:
    """Readiness check endpoint"""
    start_time = time.time()
    
    checks = {
        "application": {"status": "healthy"},
        "database": {"status": "not_configured"},
        "redis": {"status": "not_configured"},
        "mcp_server": {"status": "not_configured"}
    }
    
    overall_status = "ready"
    total_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": overall_status,
        "checks": checks,
        "total_check_time_ms": total_time,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
@limiter.limit("10/minute")
async def metrics_endpoint(request: Request) -> Dict[str, Any]:
    """Basic metrics endpoint"""
    return {
        "service": "api-builder-minimal",
        "version": "1.0.0",
        "environment": "test",
        "metrics": {
            "users_total": 0,
            "candidates_total": 0,
            "resumes_total": 0,
            "resume_status": {}
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "minimal_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )