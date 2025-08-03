"""
Integration Tests for Resume Upload Flow
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import tempfile
import os
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import UserFactory, CandidateFactory, ResumeFactory
from api.models import Resume, Candidate
from api.services.claude_service import ClaudeService
from api.services.file_service import FileService


class TestResumeUploadFlow:
    """Integration tests for complete resume upload and processing flow"""
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing"""
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nSample resume content\n%%EOF"
    
    @pytest.fixture
    def sample_docx_content(self):
        """Sample DOCX content for testing"""
        return b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00"  # DOCX signature
    
    @pytest.fixture
    def mock_claude_response(self):
        """Mock response from Claude API"""
        return {
            "personal_info": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "location": "New York, NY"
            },
            "experience": [
                {
                    "company": "Tech Corp",
                    "position": "Senior Developer",
                    "duration": "2020-2023",
                    "department": "Engineering",
                    "responsibilities": [
                        "Led development of microservices",
                        "Managed team of 5 developers"
                    ],
                    "technologies": ["Python", "FastAPI", "PostgreSQL"]
                }
            ],
            "education": [
                {
                    "institution": "MIT",
                    "degree": "BS Computer Science",
                    "year": "2019"
                }
            ],
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "colleagues": ["Jane Smith", "Bob Johnson"]
        }
    
    @pytest.mark.asyncio
    async def test_successful_pdf_upload_and_processing(
        self, 
        authenticated_client: AsyncClient, 
        db_session: AsyncSession,
        sample_pdf_content,
        mock_claude_response
    ):
        """Test complete PDF upload and processing workflow"""
        
        # Mock file processing and Claude API
        with patch('api.services.file_service.FileService.extract_text_from_pdf') as mock_extract:
            with patch('api.services.claude_service.ClaudeService.parse_resume') as mock_parse:
                mock_extract.return_value = "Sample extracted text from PDF"
                mock_parse.return_value = mock_claude_response
                
                # Create multipart form data
                files = {
                    "file": ("resume.pdf", sample_pdf_content, "application/pdf")
                }
                
                # Upload resume
                response = await authenticated_client.post(
                    "/api/v1/resumes/upload",
                    files=files
                )
                
                assert response.status_code == 201
                data = response.json()
                
                # Verify response structure
                assert "id" in data
                assert "filename" in data
                assert "candidate_id" in data
                assert "parsed_data" in data
                assert data["status"] == "completed"
                
                # Verify parsed data structure
                parsed = data["parsed_data"]
                assert parsed["personal_info"]["name"] == "John Doe"
                assert parsed["personal_info"]["email"] == "john.doe@example.com"
                assert len(parsed["experience"]) == 1
                assert len(parsed["skills"]) == 4
                
                # Verify candidate was created
                assert data["candidate_id"] is not None
                
                # Verify file was processed
                mock_extract.assert_called_once()
                mock_parse.assert_called_once_with("Sample extracted text from PDF")
    
    @pytest.mark.asyncio
    async def test_successful_docx_upload_and_processing(
        self, 
        authenticated_client: AsyncClient,
        sample_docx_content,
        mock_claude_response
    ):
        """Test complete DOCX upload and processing workflow"""
        
        with patch('api.services.file_service.FileService.extract_text_from_docx') as mock_extract:
            with patch('api.services.claude_service.ClaudeService.parse_resume') as mock_parse:
                mock_extract.return_value = "Sample extracted text from DOCX"
                mock_parse.return_value = mock_claude_response
                
                files = {
                    "file": ("resume.docx", sample_docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                }
                
                response = await authenticated_client.post(
                    "/api/v1/resumes/upload",
                    files=files
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["status"] == "completed"
                
                mock_extract.assert_called_once()
                mock_parse.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, authenticated_client: AsyncClient):
        """Test upload of invalid file type"""
        
        files = {
            "file": ("resume.txt", b"Plain text resume", "text/plain")
        }
        
        response = await authenticated_client.post(
            "/api/v1/resumes/upload",
            files=files
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "file type" in data["detail"].lower() or "format" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, authenticated_client: AsyncClient):
        """Test upload of file exceeding size limit"""
        
        # Create file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        files = {
            "file": ("large_resume.pdf", large_content, "application/pdf")
        }
        
        response = await authenticated_client.post(
            "/api/v1/resumes/upload",
            files=files
        )
        
        assert response.status_code == 413  # Payload Too Large
        data = response.json()
        assert "size" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_with_claude_api_failure(
        self, 
        authenticated_client: AsyncClient,
        sample_pdf_content
    ):
        """Test upload when Claude API fails"""
        
        with patch('api.services.file_service.FileService.extract_text_from_pdf') as mock_extract:
            with patch('api.services.claude_service.ClaudeService.parse_resume') as mock_parse:
                mock_extract.return_value = "Sample extracted text"
                mock_parse.side_effect = Exception("Claude API error")
                
                files = {
                    "file": ("resume.pdf", sample_pdf_content, "application/pdf")
                }
                
                response = await authenticated_client.post(
                    "/api/v1/resumes/upload",
                    files=files
                )
                
                # Should still create resume record but with failed status
                assert response.status_code == 201
                data = response.json()
                assert data["status"] == "failed"
                assert "parsing_error" in data
                assert data["parsed_data"] is None
    
    @pytest.mark.asyncio
    async def test_upload_with_file_extraction_failure(
        self, 
        authenticated_client: AsyncClient,
        sample_pdf_content
    ):
        """Test upload when file text extraction fails"""
        
        with patch('api.services.file_service.FileService.extract_text_from_pdf') as mock_extract:
            mock_extract.side_effect = Exception("PDF extraction error")
            
            files = {
                "file": ("resume.pdf", sample_pdf_content, "application/pdf")
            }
            
            response = await authenticated_client.post(
                "/api/v1/resumes/upload",
                files=files
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "extraction" in data["detail"].lower() or "processing" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_duplicate_candidate_detection(
        self, 
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_pdf_content,
        mock_claude_response
    ):
        """Test handling of duplicate candidate detection during upload"""
        
        # Create existing candidate
        existing_candidate = CandidateFactory(
            email="john.doe@example.com",
            full_name="John Doe"
        )
        db_session.add(existing_candidate)
        await db_session.commit()
        
        with patch('api.services.file_service.FileService.extract_text_from_pdf') as mock_extract:
            with patch('api.services.claude_service.ClaudeService.parse_resume') as mock_parse:
                mock_extract.return_value = "Sample extracted text"
                mock_parse.return_value = mock_claude_response
                
                files = {
                    "file": ("resume.pdf", sample_pdf_content, "application/pdf")
                }
                
                response = await authenticated_client.post(
                    "/api/v1/resumes/upload",
                    files=files
                )
                
                assert response.status_code == 201
                data = response.json()
                
                # Should use existing candidate
                assert data["candidate_id"] == existing_candidate.id
                assert "duplicate_detected" in data
                assert data["duplicate_detected"] is True
    
    @pytest.mark.asyncio
    async def test_upload_without_authentication(self, client: AsyncClient, sample_pdf_content):
        """Test upload without authentication"""
        
        files = {
            "file": ("resume.pdf", sample_pdf_content, "application/pdf")
        }
        
        response = await client.post(
            "/api/v1/resumes/upload",
            files=files
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "unauthorized" in data["detail"].lower() or "authentication" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_with_rate_limiting(
        self, 
        authenticated_client: AsyncClient,
        sample_pdf_content
    ):
        """Test rate limiting on upload endpoint"""
        
        with patch('api.services.file_service.FileService.extract_text_from_pdf'):
            with patch('api.services.claude_service.ClaudeService.parse_resume'):
                
                files = {
                    "file": ("resume.pdf", sample_pdf_content, "application/pdf")
                }
                
                # Make multiple requests quickly
                responses = []
                for i in range(10):  # Assuming rate limit is lower
                    response = await authenticated_client.post(
                        "/api/v1/resumes/upload",
                        files={
                            "file": (f"resume_{i}.pdf", sample_pdf_content, "application/pdf")
                        }
                    )
                    responses.append(response)
                
                # Some requests should be rate limited
                status_codes = [r.status_code for r in responses]
                assert 429 in status_codes  # Too Many Requests
    
    @pytest.mark.asyncio
    async def test_get_upload_status(
        self, 
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test getting upload status"""
        
        # Create a resume in database
        user = UserFactory()
        candidate = CandidateFactory()
        resume = ResumeFactory(candidate_id=candidate, uploaded_by_id=user, parsing_status="processing")
        
        db_session.add_all([user, candidate, resume])
        await db_session.commit()
        
        response = await authenticated_client.get(f"/api/v1/resumes/{resume.id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == resume.id
        assert data["status"] == "processing"
        assert "progress" in data
    
    @pytest.mark.asyncio
    async def test_upload_with_custom_metadata(
        self, 
        authenticated_client: AsyncClient,
        sample_pdf_content,
        mock_claude_response
    ):
        """Test upload with custom metadata"""
        
        with patch('api.services.file_service.FileService.extract_text_from_pdf') as mock_extract:
            with patch('api.services.claude_service.ClaudeService.parse_resume') as mock_parse:
                mock_extract.return_value = "Sample extracted text"
                mock_parse.return_value = mock_claude_response
                
                files = {
                    "file": ("resume.pdf", sample_pdf_content, "application/pdf")
                }
                
                # Add custom metadata
                data = {
                    "tags": '["senior", "python-developer"]',
                    "notes": "Excellent candidate for senior role",
                    "source": "LinkedIn"
                }
                
                response = await authenticated_client.post(
                    "/api/v1/resumes/upload",
                    files=files,
                    data=data
                )
                
                assert response.status_code == 201
                result = response.json()
                
                assert result["tags"] == ["senior", "python-developer"]
                assert result["notes"] == "Excellent candidate for senior role"
                assert result["source"] == "LinkedIn"
    
    @pytest.mark.asyncio
    async def test_concurrent_uploads_same_user(
        self, 
        authenticated_client: AsyncClient,
        sample_pdf_content
    ):
        """Test concurrent uploads from same user"""
        
        with patch('api.services.file_service.FileService.extract_text_from_pdf'):
            with patch('api.services.claude_service.ClaudeService.parse_resume'):
                
                # Create multiple upload tasks
                import asyncio
                
                async def upload_file(index):
                    files = {
                        "file": (f"resume_{index}.pdf", sample_pdf_content, "application/pdf")
                    }
                    return await authenticated_client.post(
                        "/api/v1/resumes/upload",
                        files=files
                    )
                
                # Run uploads concurrently
                tasks = [upload_file(i) for i in range(5)]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check that all uploads succeeded or were handled gracefully
                success_count = 0
                for response in responses:
                    if not isinstance(response, Exception) and response.status_code in [201, 429]:
                        if response.status_code == 201:
                            success_count += 1
                
                # At least some uploads should succeed
                assert success_count > 0
    
    @pytest.mark.asyncio
    async def test_upload_performance_tracking(
        self, 
        authenticated_client: AsyncClient,
        sample_pdf_content,
        mock_claude_response
    ):
        """Test that upload performance is tracked"""
        
        with patch('api.services.file_service.FileService.extract_text_from_pdf') as mock_extract:
            with patch('api.services.claude_service.ClaudeService.parse_resume') as mock_parse:
                # Simulate processing time
                import asyncio
                
                async def slow_parse(*args):
                    await asyncio.sleep(0.1)  # 100ms
                    return mock_claude_response
                
                mock_extract.return_value = "Sample extracted text"
                mock_parse.side_effect = slow_parse
                
                files = {
                    "file": ("resume.pdf", sample_pdf_content, "application/pdf")
                }
                
                start_time = asyncio.get_event_loop().time()
                response = await authenticated_client.post(
                    "/api/v1/resumes/upload",
                    files=files
                )
                end_time = asyncio.get_event_loop().time()
                
                assert response.status_code == 201
                data = response.json()
                
                # Verify performance metrics are included
                assert "processing_time_ms" in data
                assert data["processing_time_ms"] > 0
                
                # Verify actual processing time
                actual_time_ms = (end_time - start_time) * 1000
                assert actual_time_ms >= 100  # At least the sleep time