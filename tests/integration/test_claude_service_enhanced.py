"""
Integration tests for enhanced ClaudeService methods.
Tests the AI-powered search interpretation and keyword extraction capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from api.services.claude_service import ClaudeService

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


class TestClaudeServiceEnhanced:
    """Test enhanced ClaudeService AI capabilities."""
    
    @pytest.fixture
    def claude_service(self):
        """Create ClaudeService instance with mock API key."""
        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-api-key'}):
            service = ClaudeService()
            # Mock the client to avoid real API calls
            service.client = Mock()
            return service
    
    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude API response."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"skills": ["Python", "FastAPI"], "experience_years": {"min": 3, "max": 5}}'
        return mock_response
    
    async def test_interpret_search_query_success(self, claude_service, mock_claude_response):
        """Test successful search query interpretation."""
        # Mock Claude API response
        claude_service.client.messages.create = Mock(return_value=mock_claude_response)
        
        # Test query interpretation
        query = "Find senior Python developers with 3-5 years experience"
        result = await claude_service.interpret_search_query(query)
        
        # Verify API call
        claude_service.client.messages.create.assert_called_once()
        call_args = claude_service.client.messages.create.call_args
        assert call_args[1]['model'] == claude_service.model
        assert call_args[1]['temperature'] == 0.2
        assert query in call_args[1]['messages'][0]['content']
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "skills" in result
        assert "experience_years" in result
        assert result["skills"] == ["Python", "FastAPI"]
        assert result["experience_years"]["min"] == 3
    
    async def test_interpret_search_query_fallback(self, claude_service):
        """Test search query interpretation with API failure fallback."""
        # Mock API failure
        claude_service.client.messages.create = Mock(side_effect=Exception("API Error"))
        
        query = "Find React developers"
        result = await claude_service.interpret_search_query(query)
        
        # Should return fallback structure with query as keyword
        assert isinstance(result, dict)
        assert "keywords" in result
        assert query in result["keywords"]
        assert result["skills"] == []
        assert result["experience_years"]["min"] is None
    
    async def test_interpret_search_query_invalid_json(self, claude_service):
        """Test search query interpretation with invalid JSON response."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Invalid JSON response"
        claude_service.client.messages.create = Mock(return_value=mock_response)
        
        query = "Find Java developers"
        result = await claude_service.interpret_search_query(query)
        
        # Should return fallback structure
        assert isinstance(result, dict)
        assert query in result["keywords"]
    
    async def test_extract_keywords_success(self, claude_service):
        """Test successful keyword extraction."""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '["Python", "Machine Learning", "TensorFlow", "API Development"]'
        claude_service.client.messages.create = Mock(return_value=mock_response)
        
        text = "Experienced Python developer with expertise in Machine Learning and TensorFlow, skilled in API development"
        result = await claude_service.extract_keywords(text)
        
        # Verify API call
        claude_service.client.messages.create.assert_called_once()
        call_args = claude_service.client.messages.create.call_args
        assert text[:1000] in call_args[1]['messages'][0]['content']
        
        # Verify results
        assert isinstance(result, list)
        assert "Python" in result
        assert "Machine Learning" in result
        assert len(result) == 4
    
    async def test_extract_keywords_fallback(self, claude_service):
        """Test keyword extraction with API failure fallback."""
        # Mock API failure
        claude_service.client.messages.create = Mock(side_effect=Exception("API Error"))
        
        text = "Python developer with machine learning experience"
        result = await claude_service.extract_keywords(text)
        
        # Should return fallback word extraction
        assert isinstance(result, list)
        assert len(result) <= 10  # Fallback limits to 10 words
        
        # Check that meaningful words are extracted
        meaningful_words = [word for word in result if len(word) > 3]
        assert len(meaningful_words) > 0
    
    async def test_extract_keywords_invalid_json(self, claude_service):
        """Test keyword extraction with invalid JSON response."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Not a JSON array"
        claude_service.client.messages.create = Mock(return_value=mock_response)
        
        text = "Senior software engineer with Python expertise"
        result = await claude_service.extract_keywords(text)
        
        # Should return fallback extraction
        assert isinstance(result, list)
        assert len(result) <= 10
    
    async def test_extract_keywords_long_text_truncation(self, claude_service):
        """Test keyword extraction with text truncation for long inputs."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '["keyword1", "keyword2"]'
        claude_service.client.messages.create = Mock(return_value=mock_response)
        
        # Create long text (over 1000 characters)
        long_text = "Python developer " * 100  # Over 1000 chars
        result = await claude_service.extract_keywords(long_text)
        
        # Verify text was truncated to 1000 chars in API call
        call_args = claude_service.client.messages.create.call_args
        prompt = call_args[1]['messages'][0]['content']
        # Extract the text portion from the prompt
        text_start = prompt.find('Text: "') + 7
        text_end = prompt.find('"  # Limit text length')
        extracted_text = prompt[text_start:text_end]
        assert len(extracted_text) <= 1000
    
    def test_build_parsing_prompt_compatibility(self, claude_service):
        """Test _build_parsing_prompt compatibility method."""
        sample_text = "John Doe, Software Engineer"
        
        # Test that it's an alias for _create_parsing_prompt
        prompt1 = claude_service._build_parsing_prompt(sample_text)
        prompt2 = claude_service._create_parsing_prompt(sample_text)
        
        assert prompt1 == prompt2
        assert "JSON format" in prompt1
        assert sample_text in prompt1
    
    def test_validate_parsed_resume_old_structure(self, claude_service):
        """Test resume validation with old structure expected by tests."""
        # Old structure format
        old_format_resume = {
            "personal_info": {"name": "John Doe"},
            "experience": [{"company": "TechCorp"}],
            "education": [{"degree": "BS"}],
            "skills": ["Python"]
        }
        
        assert claude_service._validate_parsed_resume(old_format_resume) is True
    
    def test_validate_parsed_resume_new_structure(self, claude_service):
        """Test resume validation with new structure from implementation."""
        # New structure format
        new_format_resume = {
            "name": "John Doe",
            "email": "john@example.com",
            "work_experience": [{"company": "TechCorp"}],
            "education": [{"degree": "BS"}],
            "skills": {"technical": ["Python"]}
        }
        
        assert claude_service._validate_parsed_resume(new_format_resume) is True
    
    def test_validate_parsed_resume_invalid_structure(self, claude_service):
        """Test resume validation with invalid structure."""
        invalid_resume = {
            "invalid": "structure",
            "missing": "required_fields"
        }
        
        assert claude_service._validate_parsed_resume(invalid_resume) is False
    
    def test_validate_parsed_resume_exception_handling(self, claude_service):
        """Test resume validation with exception scenarios."""
        # Test with None
        assert claude_service._validate_parsed_resume(None) is False
        
        # Test with non-dict
        assert claude_service._validate_parsed_resume("not a dict") is False
    
    async def test_concurrent_api_calls(self, claude_service):
        """Test concurrent Claude API calls for performance validation."""
        # Mock responses for concurrent calls
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '["concurrent", "test"]'
        claude_service.client.messages.create = Mock(return_value=mock_response)
        
        # Create multiple concurrent tasks
        tasks = []
        for i in range(5):
            task = claude_service.extract_keywords(f"Test text {i}")
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all calls completed successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result, list)
            assert "concurrent" in result
        
        # Verify API was called 5 times
        assert claude_service.client.messages.create.call_count == 5


class TestClaudeServiceIntegration:
    """Integration tests with real API structure (mocked responses)."""
    
    @pytest.fixture
    def claude_service_real_structure(self):
        """Create ClaudeService with realistic API response structure."""
        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-api-key'}):
            service = ClaudeService()
            return service
    
    @patch('api.services.claude_service.Anthropic')
    async def test_real_api_structure_integration(self, mock_anthropic_class, claude_service_real_structure):
        """Test integration with realistic API response structure."""
        # Mock the Anthropic client instance
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Create realistic response structure
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''
        {
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience_years": {"min": 5, "max": null},
            "companies": ["TechCorp"],
            "departments": ["Engineering"],
            "positions": ["Senior Developer"],
            "education": ["Computer Science"],
            "locations": ["San Francisco"],
            "keywords": ["API", "Backend", "Microservices"]
        }
        '''
        mock_client.messages.create.return_value = mock_response
        
        # Reinitialize service to use mocked client
        service = ClaudeService()
        
        # Test query interpretation
        result = await service.interpret_search_query("Find senior Python developers in San Francisco")
        
        # Verify structure
        assert "skills" in result
        assert "Python" in result["skills"]
        assert result["experience_years"]["min"] == 5
        assert "TechCorp" in result["companies"]
    
    async def test_performance_metrics_collection(self, claude_service_real_structure):
        """Test performance metrics collection for Claude API calls."""
        # Mock client with timing simulation
        mock_client = Mock()
        
        async def mock_create(*args, **kwargs):
            # Simulate API call timing
            await asyncio.sleep(0.1)  # 100ms simulated response time
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = '["performance", "test"]'
            return mock_response
        
        mock_client.messages.create = mock_create
        claude_service_real_structure.client = mock_client
        
        # Time the API call
        import time
        start_time = time.time()
        result = await claude_service_real_structure.extract_keywords("performance test")
        end_time = time.time()
        
        # Verify timing and results
        duration = end_time - start_time
        assert duration >= 0.1  # At least the simulated delay
        assert "performance" in result