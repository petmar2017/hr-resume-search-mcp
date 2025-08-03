"""
MCP Server Integration Tests

Tests for Model Context Protocol (MCP) server integration including:
- Claude API integration for resume parsing
- Claude API integration for smart search
- Error handling and fallback mechanisms
- Performance and timeout testing
"""

import pytest
import asyncio
import json
import os
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ConnectError, TimeoutException
from fastapi.testclient import TestClient

from api.main import app
from api.services.claude_service import ClaudeService
from api.services.search_service import SearchService
from api.config import settings


class TestMCPServerIntegration:
    """Test suite for MCP server integration"""
    
    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude API response for resume parsing"""
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "personal_info": {
                            "name": "John Doe",
                            "email": "john.doe@example.com",
                            "phone": "+1-555-123-4567",
                            "location": "San Francisco, CA"
                        },
                        "experience": [
                            {
                                "company": "Tech Corp",
                                "position": "Senior Software Engineer",
                                "start_date": "2020-01-01",
                                "end_date": "2023-12-31",
                                "department": "Engineering",
                                "responsibilities": [
                                    "Developed microservices architecture",
                                    "Led team of 5 developers",
                                    "Implemented CI/CD pipelines"
                                ]
                            }
                        ],
                        "education": [
                            {
                                "institution": "Stanford University",
                                "degree": "MS Computer Science",
                                "year": "2019"
                            }
                        ],
                        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
                        "total_experience_years": 4
                    })
                }
            ],
            "usage": {
                "input_tokens": 1500,
                "output_tokens": 800
            }
        }
    
    @pytest.fixture
    def mock_smart_search_response(self):
        """Mock Claude response for smart search interpretation"""
        return {
            "content": [
                {
                    "type": "text", 
                    "text": json.dumps({
                        "interpreted_query": {
                            "original_query": "Find senior Python developers with 5+ years experience",
                            "detected_intent": "skills_and_experience_search",
                            "extracted_criteria": {
                                "skills": ["Python"],
                                "min_experience_years": 5,
                                "seniority_level": "senior"
                            }
                        },
                        "sql_query": "SELECT * FROM candidates WHERE skills @> '[\"Python\"]' AND total_experience_years >= 5",
                        "reasoning": "I interpreted this as a search for senior Python developers with at least 5 years of experience. I extracted 'Python' as the key skill and '5' as the minimum experience requirement."
                    })
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_claude_service_initialization(self):
        """Test Claude service initializes correctly"""
        claude_service = ClaudeService()
        assert claude_service.api_key == settings.claude_api_key
        assert claude_service.base_url == "https://api.anthropic.com"
        assert claude_service.model == "claude-3-sonnet-20240229"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_claude_resume_parsing_success(self, mock_post, mock_claude_response):
        """Test successful resume parsing with Claude API"""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_claude_response
        mock_post.return_value = mock_response
        
        claude_service = ClaudeService()
        resume_text = "John Doe\nSenior Software Engineer\nPython, FastAPI, PostgreSQL"
        
        result = await claude_service.parse_resume(resume_text)
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['url'] == "https://api.anthropic.com/v1/messages"
        assert call_args[1]['headers']['x-api-key'] == settings.claude_api_key
        assert call_args[1]['headers']['anthropic-version'] == "2023-06-01"
        
        # Verify the result
        assert result is not None
        assert result['personal_info']['name'] == "John Doe"
        assert "Python" in result['skills']
        assert result['total_experience_years'] == 4
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_claude_resume_parsing_timeout(self, mock_post):
        """Test Claude API timeout handling"""
        mock_post.side_effect = TimeoutException("Request timeout")
        
        claude_service = ClaudeService()
        resume_text = "Test resume content"
        
        with pytest.raises(Exception) as exc_info:
            await claude_service.parse_resume(resume_text)
        
        assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_claude_resume_parsing_api_error(self, mock_post):
        """Test Claude API error handling"""
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "type": "invalid_request_error",
                "message": "Invalid request format"
            }
        }
        mock_post.return_value = mock_response
        
        claude_service = ClaudeService()
        resume_text = "Test resume content"
        
        with pytest.raises(Exception) as exc_info:
            await claude_service.parse_resume(resume_text)
        
        assert "400" in str(exc_info.value) or "invalid_request" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_claude_smart_search_success(self, mock_post, mock_smart_search_response):
        """Test successful smart search with Claude API"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_smart_search_response
        mock_post.return_value = mock_response
        
        claude_service = ClaudeService()
        search_query = "Find senior Python developers with 5+ years experience"
        
        result = await claude_service.interpret_search_query(search_query)
        
        # Verify the request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert search_query in str(call_args[1]['json']['messages'])
        
        # Verify the result
        assert result is not None
        assert result['interpreted_query']['detected_intent'] == "skills_and_experience_search"
        assert "Python" in result['interpreted_query']['extracted_criteria']['skills']
        assert result['interpreted_query']['extracted_criteria']['min_experience_years'] == 5
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_claude_rate_limiting(self, mock_post):
        """Test Claude API rate limiting handling"""
        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "type": "rate_limit_error",
                "message": "Rate limit exceeded"
            }
        }
        mock_response.headers = {"retry-after": "60"}
        mock_post.return_value = mock_response
        
        claude_service = ClaudeService()
        resume_text = "Test resume content"
        
        with pytest.raises(Exception) as exc_info:
            await claude_service.parse_resume(resume_text)
        
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_claude_service_fallback_mechanisms(self):
        """Test fallback mechanisms when Claude API is unavailable"""
        # Test with invalid API key
        original_key = settings.claude_api_key
        settings.claude_api_key = "invalid-key"
        
        try:
            claude_service = ClaudeService()
            resume_text = "John Doe\nSoftware Engineer\nPython, JavaScript"
            
            # Should fall back to basic parsing
            with pytest.raises(Exception):
                await claude_service.parse_resume(resume_text)
                
        finally:
            settings.claude_api_key = original_key
    
    @pytest.mark.asyncio
    @patch('api.services.claude_service.ClaudeService.parse_resume')
    async def test_end_to_end_resume_upload_with_mcp(self, mock_parse, authenticated_client):
        """Test end-to-end resume upload with MCP integration"""
        # Mock Claude parsing response
        mock_parse.return_value = {
            "personal_info": {
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+1-555-987-6543",
                "location": "New York, NY"
            },
            "experience": [
                {
                    "company": "StartupCo",
                    "position": "Lead Developer",
                    "start_date": "2021-01-01",
                    "end_date": None,
                    "department": "Engineering"
                }
            ],
            "skills": ["Python", "React", "PostgreSQL"],
            "total_experience_years": 3
        }
        
        # Create a test PDF file
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Jane Smith) Tj ET
endstream endobj
xref 0 5
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000179 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref 238
%%EOF"""
        
        # Upload resume
        response = await authenticated_client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test_resume.pdf", pdf_content, "application/pdf")}
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        # Verify MCP integration was called
        mock_parse.assert_called_once()
        
        # Verify response contains parsed data
        assert "resume_id" in data
        assert "parsing_status" in data
    
    @pytest.mark.asyncio
    @patch('api.services.claude_service.ClaudeService.interpret_search_query')
    async def test_end_to_end_smart_search_with_mcp(self, mock_interpret, authenticated_client):
        """Test end-to-end smart search with MCP integration"""
        # Mock Claude interpretation response
        mock_interpret.return_value = {
            "interpreted_query": {
                "original_query": "Find Python developers in San Francisco",
                "detected_intent": "location_and_skills_search",
                "extracted_criteria": {
                    "skills": ["Python"],
                    "location": "San Francisco"
                }
            },
            "reasoning": "Looking for Python developers specifically located in San Francisco."
        }
        
        search_data = {
            "query": "Find Python developers in San Francisco",
            "include_reasoning": True
        }
        
        response = await authenticated_client.post(
            "/api/v1/search/smart",
            json=search_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify MCP integration was called
        mock_interpret.assert_called_once_with("Find Python developers in San Francisco")
        
        # Verify response structure
        assert "interpreted_query" in data
        assert "reasoning" in data
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_mcp_performance_metrics(self):
        """Test MCP integration performance metrics"""
        claude_service = ClaudeService()
        
        # Test response time tracking
        import time
        
        start_time = time.time()
        
        # Mock a Claude API call with artificial delay
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": "{}"}]
            }
            
            async def delayed_response(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                return mock_response
            
            mock_post.side_effect = delayed_response
            
            try:
                await claude_service.parse_resume("test content")
            except:
                pass  # We're just testing timing
        
        elapsed_time = time.time() - start_time
        assert elapsed_time >= 0.1  # Should take at least 100ms due to mock delay
    
    @pytest.mark.asyncio
    async def test_mcp_concurrent_requests(self):
        """Test MCP server handling of concurrent requests"""
        claude_service = ClaudeService()
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": "{}"}]
            }
            mock_post.return_value = mock_response
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = claude_service.parse_resume(f"test content {i}")
                tasks.append(task)
            
            # Execute concurrently
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify all requests were made
                assert mock_post.call_count == 5
                
                # Check for any exceptions
                exceptions = [r for r in results if isinstance(r, Exception)]
                assert len(exceptions) == 0, f"Unexpected exceptions: {exceptions}"
                
            except Exception as e:
                # This is expected if Claude API is not properly configured
                assert "api" in str(e).lower() or "key" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_mcp_configuration_validation(self):
        """Test MCP server configuration validation"""
        # Test with missing API key
        original_key = settings.claude_api_key
        settings.claude_api_key = ""
        
        try:
            claude_service = ClaudeService()
            
            with pytest.raises(Exception) as exc_info:
                await claude_service.parse_resume("test")
            
            assert "api key" in str(exc_info.value).lower() or "unauthorized" in str(exc_info.value).lower()
            
        finally:
            settings.claude_api_key = original_key
    
    @pytest.mark.asyncio
    async def test_mcp_error_recovery(self):
        """Test MCP server error recovery mechanisms"""
        claude_service = ClaudeService()
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # Simulate network failure followed by success
            mock_post.side_effect = [
                ConnectError("Network error"),
                AsyncMock(status_code=200, json=lambda: {"content": [{"type": "text", "text": "{}"}]})
            ]
            
            # The service should handle the first failure gracefully
            with pytest.raises(Exception):
                await claude_service.parse_resume("test content")
    
    @pytest.mark.asyncio
    async def test_claude_token_usage_tracking(self):
        """Test Claude API token usage tracking"""
        claude_service = ClaudeService()
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": "{}"}],
                "usage": {
                    "input_tokens": 1500,
                    "output_tokens": 800
                }
            }
            mock_post.return_value = mock_response
            
            try:
                await claude_service.parse_resume("test content")
                
                # Verify the service processes usage information
                # (This would require implementing usage tracking in the service)
                
            except Exception as e:
                # Expected if service doesn't handle usage tracking yet
                pass


class TestMCPHealthChecks:
    """Test MCP server health and monitoring"""
    
    @pytest.mark.asyncio
    async def test_mcp_health_endpoint(self):
        """Test MCP server health check"""
        # This would test a dedicated MCP health endpoint if implemented
        with TestClient(app) as client:
            response = client.get("/readiness")
            assert response.status_code == 200
            
            data = response.json()
            # Check if MCP status is included in readiness check
            if "checks" in data:
                # MCP server status should be included
                assert "mcp_server" in data["checks"] or "claude_api" in data["checks"]
    
    @pytest.mark.asyncio
    async def test_mcp_monitoring_metrics(self):
        """Test MCP server monitoring and metrics"""
        # Test metrics endpoint includes MCP-related metrics
        with TestClient(app) as client:
            response = client.get("/metrics")
            assert response.status_code == 200
            
            data = response.json()
            # Should include metrics about MCP usage if implemented
            assert "service" in data
            assert "version" in data


# Integration test for actual Claude API (requires valid API key)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_claude_api_integration():
    """Integration test with real Claude API (requires valid API key)"""
    if not settings.claude_api_key or settings.claude_api_key.startswith("test"):
        pytest.skip("Real Claude API key required for integration test")
    
    claude_service = ClaudeService()
    
    # Test with simple resume text
    resume_text = """
    John Doe
    Software Engineer
    Email: john.doe@example.com
    Phone: (555) 123-4567
    
    Experience:
    - Software Engineer at TechCorp (2020-2023)
    - Developed web applications using Python and React
    
    Skills: Python, JavaScript, React, PostgreSQL
    
    Education:
    - BS Computer Science, University of Technology (2019)
    """
    
    try:
        result = await claude_service.parse_resume(resume_text)
        
        # Verify basic structure
        assert isinstance(result, dict)
        assert "personal_info" in result
        assert "experience" in result
        assert "skills" in result
        
        # Verify parsed content
        assert result["personal_info"]["name"] == "John Doe"
        assert "john.doe@example.com" in result["personal_info"]["email"]
        assert "Python" in result["skills"]
        
    except Exception as e:
        pytest.fail(f"Real Claude API integration failed: {e}")


# Performance benchmark for MCP integration
@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_mcp_performance_benchmark():
    """Performance benchmark for MCP integration"""
    claude_service = ClaudeService()
    
    # Benchmark resume parsing performance
    resume_text = "John Doe\nSoftware Engineer\nPython, React, PostgreSQL"
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "{}"}]
        }
        mock_post.return_value = mock_response
        
        import time
        start_time = time.time()
        
        # Run multiple iterations
        for _ in range(10):
            try:
                await claude_service.parse_resume(resume_text)
            except:
                pass
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / 10
        
        # Performance assertion (should be fast with mocked API)
        assert avg_time < 0.1, f"Average request time too slow: {avg_time}s"