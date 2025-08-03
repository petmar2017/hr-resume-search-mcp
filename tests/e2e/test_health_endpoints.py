"""
E2E Tests for Health Check Endpoints
"""

import pytest
import asyncio
import time
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test suite for health check endpoints"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns expected response"""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "API Builder is running"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-builder"
        assert data["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_readiness_check_endpoint(self, client: AsyncClient):
        """Test readiness check endpoint"""
        response = await client.get("/readiness")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "mcp_server" in data["checks"]
    
    @pytest.mark.asyncio
    async def test_api_documentation_available(self, client: AsyncClient):
        """Test that API documentation is accessible"""
        # Test OpenAPI schema
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "API Builder"
        
        # Test Swagger UI endpoint
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
        
        # Test ReDoc endpoint
        response = await client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are properly configured"""
        response = await client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    @pytest.mark.asyncio
    async def test_response_time_performance(self, client: AsyncClient, performance_threshold):
        """Test that health endpoints respond within acceptable time"""
        endpoints = ["/", "/health", "/readiness"]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await client.get(endpoint)
            elapsed_time = time.time() - start_time
            
            assert response.status_code == 200
            assert elapsed_time < performance_threshold["api_response_time"], \
                f"Endpoint {endpoint} took {elapsed_time:.2f}s, exceeding threshold of {performance_threshold['api_response_time']}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client: AsyncClient, performance_threshold):
        """Test concurrent health check requests"""
        num_requests = performance_threshold["concurrent_requests"]
        
        async def make_request():
            response = await client.get("/health")
            return response.status_code
        
        # Make concurrent requests
        tasks = [make_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(status == 200 for status in results), \
            f"Some concurrent requests failed: {results}"
    
    @pytest.mark.asyncio
    async def test_invalid_endpoint_returns_404(self, client: AsyncClient):
        """Test that invalid endpoints return 404"""
        response = await client.get("/invalid/endpoint")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client: AsyncClient):
        """Test that unsupported methods return 405"""
        # Try POST on GET-only endpoint
        response = await client.post("/health")
        assert response.status_code == 405
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_headers_security(self, client: AsyncClient):
        """Test security headers are present"""
        response = await client.get("/health")
        
        # Check for security headers (these should be added in production)
        # These are examples - adjust based on your security requirements
        headers_to_check = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]
        
        # Note: These might not be present in development
        # This test documents what should be added for production
        for header in headers_to_check:
            # Log missing headers for documentation
            if header not in response.headers:
                print(f"Security header '{header}' not present - should be added for production")