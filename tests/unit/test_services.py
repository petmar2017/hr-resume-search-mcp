"""
Unit Tests for Service Classes (Claude and File Services)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, mock_open
import asyncio
import json
import tempfile
import os
from pathlib import Path
import aiofiles
from typing import Dict, Any

# Import services to test
from api.services.claude_service import ClaudeService
from api.services.file_service import FileService
from api.services.search_service import SearchService
from api.config import get_settings


class TestClaudeService:
    """Test ClaudeService functionality"""
    
    @pytest.fixture
    def claude_service(self):
        """Create ClaudeService instance for testing"""
        return ClaudeService()
    
    @pytest.fixture
    def sample_resume_text(self):
        """Sample resume text for testing"""
        return """
        John Doe
        Software Engineer
        john.doe@example.com
        (555) 123-4567
        
        Experience:
        Senior Developer at Tech Corp (2020-2023)
        - Led development of microservices architecture
        - Managed team of 5 developers
        - Technologies: Python, FastAPI, PostgreSQL
        
        Junior Developer at StartupCo (2018-2020)
        - Built REST APIs
        - Worked with React frontend team
        
        Education:
        BS Computer Science, MIT (2018)
        
        Skills: Python, JavaScript, PostgreSQL, Docker, AWS
        """
    
    @pytest.fixture
    def expected_parsed_resume(self):
        """Expected parsed resume structure"""
        return {
            "personal_info": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "(555) 123-4567",
                "location": None
            },
            "experience": [
                {
                    "company": "Tech Corp",
                    "position": "Senior Developer",
                    "duration": "2020-2023",
                    "department": "Engineering",
                    "responsibilities": [
                        "Led development of microservices architecture",
                        "Managed team of 5 developers"
                    ],
                    "technologies": ["Python", "FastAPI", "PostgreSQL"]
                },
                {
                    "company": "StartupCo",
                    "position": "Junior Developer",
                    "duration": "2018-2020",
                    "responsibilities": [
                        "Built REST APIs",
                        "Worked with React frontend team"
                    ]
                }
            ],
            "education": [
                {
                    "institution": "MIT",
                    "degree": "BS Computer Science",
                    "year": "2018"
                }
            ],
            "skills": ["Python", "JavaScript", "PostgreSQL", "Docker", "AWS"]
        }
    
    @pytest.mark.asyncio
    async def test_parse_resume_success(self, claude_service, sample_resume_text, expected_parsed_resume):
        """Test successful resume parsing"""
        with patch('api.services.claude_service.anthropic.AsyncAnthropic') as mock_anthropic:
            # Mock Claude API response
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            
            mock_response = AsyncMock()
            mock_response.content = [Mock(text=json.dumps(expected_parsed_resume))]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            
            result = await claude_service.parse_resume(sample_resume_text)
            
            assert result == expected_parsed_resume
            mock_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_resume_invalid_json(self, claude_service, sample_resume_text):
        """Test resume parsing with invalid JSON response"""
        with patch('api.services.claude_service.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            
            # Mock invalid JSON response
            mock_response = AsyncMock()
            mock_response.content = [Mock(text="Invalid JSON response")]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            
            with pytest.raises(ValueError, match="Failed to parse Claude response"):
                await claude_service.parse_resume(sample_resume_text)
    
    @pytest.mark.asyncio
    async def test_parse_resume_api_error(self, claude_service, sample_resume_text):
        """Test resume parsing with API error"""
        with patch('api.services.claude_service.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            
            # Mock API error
            mock_client.messages.create = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(Exception, match="API Error"):
                await claude_service.parse_resume(sample_resume_text)
    
    @pytest.mark.asyncio
    async def test_parse_resume_empty_text(self, claude_service):
        """Test resume parsing with empty text"""
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            await claude_service.parse_resume("")
    
    def test_build_parsing_prompt(self, claude_service, sample_resume_text):
        """Test prompt building for resume parsing"""
        prompt = claude_service._build_parsing_prompt(sample_resume_text)
        
        assert "JSON format" in prompt
        assert "personal_info" in prompt
        assert "experience" in prompt
        assert "education" in prompt
        assert "skills" in prompt
        assert sample_resume_text in prompt
    
    def test_validate_parsed_resume(self, claude_service, expected_parsed_resume):
        """Test parsed resume validation"""
        # Valid resume should pass
        assert claude_service._validate_parsed_resume(expected_parsed_resume) is True
        
        # Missing required fields should fail
        invalid_resume = {"personal_info": {}}
        assert claude_service._validate_parsed_resume(invalid_resume) is False
        
        # Invalid structure should fail
        assert claude_service._validate_parsed_resume({"invalid": "structure"}) is False
    
    @pytest.mark.asyncio
    async def test_extract_keywords(self, claude_service):
        """Test keyword extraction from text"""
        text = "Python developer with FastAPI and PostgreSQL experience"
        
        with patch('api.services.claude_service.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            
            mock_response = AsyncMock()
            mock_response.content = [Mock(text='["Python", "FastAPI", "PostgreSQL", "developer"]')]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            
            keywords = await claude_service.extract_keywords(text)
            
            assert "Python" in keywords
            assert "FastAPI" in keywords
            assert "PostgreSQL" in keywords
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, claude_service, sample_resume_text):
        """Test retry mechanism for failed API calls"""
        with patch('api.services.claude_service.anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            
            # First two calls fail, third succeeds
            mock_client.messages.create = AsyncMock(
                side_effect=[
                    Exception("Temporary error"),
                    Exception("Another temporary error"),
                    AsyncMock(content=[Mock(text='{"result": "success"}')])
                ]
            )
            
            with patch.object(claude_service, '_retry_delay', 0.01):  # Fast retry for testing
                result = await claude_service.parse_resume_with_retry(sample_resume_text, max_retries=3)
                
                assert result == {"result": "success"}
                assert mock_client.messages.create.call_count == 3


class TestFileService:
    """Test FileService functionality"""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing"""
        return FileService()
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing"""
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000125 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n198\n%%EOF"
    
    @pytest.fixture
    def sample_docx_content(self):
        """Sample DOCX content for testing"""
        return b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # DOCX file signature
    
    def test_validate_file_type(self, file_service):
        """Test file type validation"""
        # Valid file types
        assert file_service.validate_file_type("resume.pdf") is True
        assert file_service.validate_file_type("resume.docx") is True
        assert file_service.validate_file_type("resume.doc") is True
        
        # Invalid file types
        assert file_service.validate_file_type("resume.txt") is False
        assert file_service.validate_file_type("resume.jpg") is False
        assert file_service.validate_file_type("resume") is False
    
    def test_validate_file_size(self, file_service):
        """Test file size validation"""
        settings = get_settings()
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        
        # Valid file size
        assert file_service.validate_file_size(max_size - 1000) is True
        assert file_service.validate_file_size(1024) is True
        
        # Invalid file size
        assert file_service.validate_file_size(max_size + 1) is False
        assert file_service.validate_file_size(0) is False
    
    @pytest.mark.asyncio
    async def test_save_file_success(self, file_service, sample_pdf_content):
        """Test successful file saving"""
        filename = "test_resume.pdf"
        
        with patch('aiofiles.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                with patch('pathlib.Path.exists', return_value=False):
                    file_path = await file_service.save_file(filename, sample_pdf_content)
                    
                    assert file_path.endswith(filename)
                    mock_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_text_from_pdf(self, file_service, sample_pdf_content):
        """Test text extraction from PDF"""
        with patch('PyPDF2.PdfReader') as mock_pdf_reader:
            # Mock PDF reader
            mock_page = Mock()
            mock_page.extract_text.return_value = "Sample PDF text content"
            
            mock_reader = Mock()
            mock_reader.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(sample_pdf_content)
                temp_file_path = temp_file.name
            
            try:
                text = await file_service.extract_text_from_pdf(temp_file_path)
                assert text == "Sample PDF text content"
            finally:
                os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_docx(self, file_service):
        """Test text extraction from DOCX"""
        with patch('docx.Document') as mock_docx:
            # Mock DOCX document
            mock_paragraph = Mock()
            mock_paragraph.text = "Sample DOCX paragraph"
            
            mock_doc = Mock()
            mock_doc.paragraphs = [mock_paragraph]
            mock_docx.return_value = mock_doc
            
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            try:
                text = await file_service.extract_text_from_docx(temp_file_path)
                assert text == "Sample DOCX paragraph"
            finally:
                os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_process_uploaded_file(self, file_service, sample_pdf_content):
        """Test complete file processing workflow"""
        filename = "test_resume.pdf"
        
        with patch.object(file_service, 'save_file') as mock_save:
            with patch.object(file_service, 'extract_text_from_pdf') as mock_extract:
                mock_save.return_value = "/path/to/saved/file.pdf"
                mock_extract.return_value = "Extracted resume text"
                
                result = await file_service.process_uploaded_file(filename, sample_pdf_content)
                
                assert result["file_path"] == "/path/to/saved/file.pdf"
                assert result["extracted_text"] == "Extracted resume text"
                assert result["file_size"] == len(sample_pdf_content)
                assert result["file_type"] == "pdf"
    
    def test_generate_unique_filename(self, file_service):
        """Test unique filename generation"""
        original_filename = "resume.pdf"
        
        filename1 = file_service.generate_unique_filename(original_filename)
        filename2 = file_service.generate_unique_filename(original_filename)
        
        # Should be different each time
        assert filename1 != filename2
        
        # Should preserve extension
        assert filename1.endswith(".pdf")
        assert filename2.endswith(".pdf")
        
        # Should contain timestamp
        assert len(filename1) > len(original_filename)
    
    @pytest.mark.asyncio
    async def test_delete_file(self, file_service):
        """Test file deletion"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        # File should exist
        assert os.path.exists(temp_file_path)
        
        # Delete file
        await file_service.delete_file(temp_file_path)
        
        # File should be deleted
        assert not os.path.exists(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files(self, file_service):
        """Test cleanup of old files"""
        with patch('os.listdir') as mock_listdir:
            with patch('os.path.getmtime') as mock_getmtime:
                with patch('os.unlink') as mock_unlink:
                    # Mock old files
                    mock_listdir.return_value = ['old_file.pdf', 'new_file.pdf']
                    mock_getmtime.side_effect = [
                        1000000,  # Old timestamp
                        9999999   # New timestamp
                    ]
                    
                    await file_service.cleanup_old_files(days_old=30)
                    
                    # Only old file should be deleted
                    mock_unlink.assert_called_once()


class TestSearchService:
    """Test SearchService functionality"""
    
    @pytest.fixture
    def search_service(self):
        """Create SearchService instance for testing"""
        return SearchService()
    
    @pytest.fixture
    def sample_candidates(self):
        """Sample candidate data for testing"""
        return [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Senior Developer",
                        "department": "Engineering"
                    }
                ]
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "skills": ["JavaScript", "React", "Node.js"],
                "experience": [
                    {
                        "company": "StartupCo",
                        "position": "Frontend Developer",
                        "department": "Engineering"
                    }
                ]
            }
        ]
    
    @pytest.mark.asyncio
    async def test_search_by_skills(self, search_service, sample_candidates):
        """Test search by skills"""
        with patch.object(search_service, '_query_database') as mock_query:
            mock_query.return_value = [sample_candidates[0]]  # John Doe
            
            results = await search_service.search_by_skills(["Python", "FastAPI"])
            
            assert len(results) == 1
            assert results[0]["name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_search_by_department(self, search_service, sample_candidates):
        """Test search by department"""
        with patch.object(search_service, '_query_database') as mock_query:
            mock_query.return_value = sample_candidates  # Both in Engineering
            
            results = await search_service.search_by_department("Engineering")
            
            assert len(results) == 2
            mock_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar_candidates(self, search_service, sample_candidates):
        """Test similar candidate search"""
        candidate_id = 1
        
        with patch.object(search_service, '_get_candidate_by_id') as mock_get:
            with patch.object(search_service, '_find_similar_by_skills') as mock_similar:
                mock_get.return_value = sample_candidates[0]
                mock_similar.return_value = [sample_candidates[1]]
                
                results = await search_service.search_similar_candidates(candidate_id)
                
                assert len(results) == 1
                assert results[0]["name"] == "Jane Smith"
    
    def test_calculate_similarity_score(self, search_service):
        """Test similarity score calculation"""
        candidate1 = {
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience": [{"department": "Engineering"}]
        }
        candidate2 = {
            "skills": ["Python", "Django", "MySQL"],
            "experience": [{"department": "Engineering"}]
        }
        
        score = search_service._calculate_similarity_score(candidate1, candidate2)
        
        # Should be between 0 and 1
        assert 0 <= score <= 1
        
        # Should be > 0 since they share skills and department
        assert score > 0
    
    def test_extract_search_keywords(self, search_service):
        """Test keyword extraction from search query"""
        query = "Python developer with FastAPI experience"
        keywords = search_service._extract_search_keywords(query)
        
        assert "Python" in keywords
        assert "FastAPI" in keywords
        assert "developer" in keywords
    
    @pytest.mark.asyncio
    async def test_advanced_search_with_filters(self, search_service):
        """Test advanced search with multiple filters"""
        filters = {
            "skills": ["Python"],
            "department": "Engineering",
            "experience_years": 5,
            "location": "New York"
        }
        
        with patch.object(search_service, '_query_database') as mock_query:
            mock_query.return_value = []
            
            results = await search_service.advanced_search(filters)
            
            assert isinstance(results, list)
            mock_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_pagination(self, search_service, sample_candidates):
        """Test search result pagination"""
        with patch.object(search_service, '_query_database') as mock_query:
            mock_query.return_value = sample_candidates
            
            results = await search_service.search_with_pagination(
                query="Python",
                page=1,
                page_size=1
            )
            
            assert "results" in results
            assert "total" in results
            assert "page" in results
            assert "page_size" in results
            assert len(results["results"]) <= 1
    
    def test_validate_search_parameters(self, search_service):
        """Test search parameter validation"""
        # Valid parameters
        assert search_service._validate_search_parameters({
            "skills": ["Python"],
            "page": 1,
            "page_size": 10
        }) is True
        
        # Invalid parameters
        assert search_service._validate_search_parameters({
            "page": 0  # Invalid page number
        }) is False
        
        assert search_service._validate_search_parameters({
            "page_size": 1000  # Too large page size
        }) is False