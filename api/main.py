"""
FastAPI Application - Main Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Any, Dict
from datetime import datetime

# Import routers
from .routers import auth, search
from .database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    logger.info("Starting API Builder application")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Builder application")


# Initialize FastAPI application
app = FastAPI(
    title="API Builder",
    description="FastAPI-based API Builder with MCP Server Integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure from environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(search.router)


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint
    """
    return {
        "message": "API Builder is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "api-builder",
        "version": "1.0.0"
    }


@app.get("/readiness", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint
    """
    from .database import check_db_connection
    
    checks = {}
    overall_status = "ready"
    
    # Check database connectivity
    try:
        if check_db_connection():
            checks["database"] = "healthy"
        else:
            checks["database"] = "unhealthy"
            overall_status = "not_ready"
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        checks["database"] = "error"
        overall_status = "not_ready"
    
    # TODO: Add redis connectivity check when Redis is implemented
    checks["redis"] = "not_configured"
    
    # TODO: Add MCP server connectivity check when implemented
    checks["mcp_server"] = "not_configured"
    
    return {
        "status": overall_status,
        "checks": checks,
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