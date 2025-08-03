"""
Integration tests for enhanced FileService methods.
Tests the async file processing capabilities and comprehensive file handling.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, mock_open
from pathlib import Path
from api.services.file_service import FileService

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


class TestFileServiceEnhanced:
    """Test enhanced FileService async capabilities."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        return FileService()
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing."""
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000125 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n198\n%%EOF"
    
    @pytest.fixture
    def sample_docx_content(self):
        """Sample DOCX content for testing."""
        return b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # DOCX file signature
    
    async def test_process_uploaded_file_pdf_success(self, file_service, sample_pdf_content):
        """Test successful PDF file processing workflow."""
        filename = "test_resume.pdf"
        
        # Mock the file operations
        with patch.object(file_service, 'validate_file_type', return_value=True):
            with patch.object(file_service, 'validate_file_size', return_value=True):
                with patch.object(file_service, 'save_file', return_value="/uploads/test_resume.pdf") as mock_save:
                    with patch.object(file_service, 'extract_text_from_pdf', return_value="Extracted PDF text") as mock_extract:
                        
                        result = await file_service.process_uploaded_file(filename, sample_pdf_content)
                        
                        # Verify the result structure
                        assert "file_path" in result
                        assert "extracted_text" in result
                        assert "file_size" in result
                        assert "file_type" in result
                        assert "processing_time" in result
                        assert "success" in result
                        
                        # Verify the values
                        assert result["file_path"] == "/uploads/test_resume.pdf"
                        assert result["extracted_text"] == "Extracted PDF text"
                        assert result["file_size"] == len(sample_pdf_content)
                        assert result["file_type"] == "pdf"
                        assert result["success"] is True
                        assert result["processing_time"] > 0
                        
                        # Verify method calls
                        mock_save.assert_called_once_with(filename, sample_pdf_content)
                        mock_extract.assert_called_once_with("/uploads/test_resume.pdf")
    
    async def test_process_uploaded_file_docx_success(self, file_service, sample_docx_content):
        """Test successful DOCX file processing workflow."""
        filename = "test_resume.docx"
        
        # Mock the file operations
        with patch.object(file_service, 'validate_file_type', return_value=True):
            with patch.object(file_service, 'validate_file_size', return_value=True):
                with patch.object(file_service, 'save_file', return_value="/uploads/test_resume.docx") as mock_save:
                    with patch.object(file_service, 'extract_text_from_docx', return_value="Extracted DOCX text") as mock_extract:
                        
                        result = await file_service.process_uploaded_file(filename, sample_docx_content)
                        
                        # Verify the result structure
                        assert result["file_path"] == "/uploads/test_resume.docx"
                        assert result["extracted_text"] == "Extracted DOCX text"
                        assert result["file_type"] == "docx"
                        assert result["success"] is True
                        
                        # Verify method calls
                        mock_save.assert_called_once_with(filename, sample_docx_content)
                        mock_extract.assert_called_once_with("/uploads/test_resume.docx")
    
    async def test_process_uploaded_file_invalid_type(self, file_service):
        """Test file processing with invalid file type."""
        filename = "test_file.txt"
        content = b"Invalid file content"
        
        # Mock validation to return False for file type
        with patch.object(file_service, 'validate_file_type', return_value=False):
            
            result = await file_service.process_uploaded_file(filename, content)
            
            # Should return error result
            assert result["success"] is False
            assert "error" in result
            assert "Invalid file type" in result["error"]
            assert result["file_type"] == "txt"
    
    async def test_process_uploaded_file_invalid_size(self, file_service, sample_pdf_content):
        """Test file processing with invalid file size."""
        filename = "test_resume.pdf"
        
        # Mock validation to return False for file size
        with patch.object(file_service, 'validate_file_type', return_value=True):
            with patch.object(file_service, 'validate_file_size', return_value=False):
                
                result = await file_service.process_uploaded_file(filename, sample_pdf_content)
                
                # Should return error result
                assert result["success"] is False
                assert "error" in result
                assert "File size exceeds limit" in result["error"]
    
    async def test_process_uploaded_file_save_error(self, file_service, sample_pdf_content):
        """Test file processing with file save error."""
        filename = "test_resume.pdf"
        
        # Mock validation to succeed but save to fail
        with patch.object(file_service, 'validate_file_type', return_value=True):
            with patch.object(file_service, 'validate_file_size', return_value=True):
                with patch.object(file_service, 'save_file', side_effect=Exception("Save error")):
                    
                    result = await file_service.process_uploaded_file(filename, sample_pdf_content)
                    
                    # Should return error result
                    assert result["success"] is False
                    assert "error" in result
                    assert "Save error" in result["error"]
    
    async def test_process_uploaded_file_extract_error(self, file_service, sample_pdf_content):
        """Test file processing with text extraction error."""
        filename = "test_resume.pdf"
        
        # Mock validation and save to succeed but extraction to fail
        with patch.object(file_service, 'validate_file_type', return_value=True):
            with patch.object(file_service, 'validate_file_size', return_value=True):
                with patch.object(file_service, 'save_file', return_value="/uploads/test_resume.pdf"):
                    with patch.object(file_service, 'extract_text_from_pdf', side_effect=Exception("Extraction error")):
                        
                        result = await file_service.process_uploaded_file(filename, sample_pdf_content)
                        
                        # Should return error result
                        assert result["success"] is False
                        assert "error" in result
                        assert "Extraction error" in result["error"]
    
    async def test_save_file_success(self, file_service, sample_pdf_content):
        """Test successful file saving."""
        filename = "test_resume.pdf"
        
        # Mock file system operations
        with patch('aiofiles.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                with patch('pathlib.Path.exists', return_value=False):
                    with patch.object(file_service, 'generate_unique_filename', return_value="unique_resume.pdf"):
                        
                        file_path = await file_service.save_file(filename, sample_pdf_content)
                        
                        # Should return a file path
                        assert isinstance(file_path, str)
                        assert file_path.endswith("unique_resume.pdf")
                        
                        # Verify file was opened for writing
                        mock_file.assert_called_once()
    
    async def test_save_file_with_directory_creation(self, file_service, sample_pdf_content):
        """Test file saving with directory creation."""
        filename = "test_resume.pdf"
        
        # Mock file system operations
        with patch('aiofiles.open', mock_open()) as mock_file:
            with patch('os.makedirs') as mock_makedirs:
                with patch('pathlib.Path.exists', return_value=False):
                    with patch.object(file_service, 'generate_unique_filename', return_value="unique_resume.pdf"):
                        
                        await file_service.save_file(filename, sample_pdf_content)
                        
                        # Verify directory creation was called
                        mock_makedirs.assert_called_once()
    
    async def test_extract_text_from_pdf_success(self, file_service):
        """Test successful PDF text extraction."""
        file_path = "/path/to/test.pdf"
        
        # Mock PyPDF2
        with patch('PyPDF2.PdfReader') as mock_pdf_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "Sample PDF text content"
            
            mock_reader = Mock()
            mock_reader.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader
            
            text = await file_service.extract_text_from_pdf(file_path)
            
            assert text == "Sample PDF text content"
            mock_pdf_reader.assert_called_once_with(file_path)
    
    async def test_extract_text_from_pdf_multiple_pages(self, file_service):
        """Test PDF text extraction from multiple pages."""
        file_path = "/path/to/test.pdf"
        
        # Mock PyPDF2 with multiple pages
        with patch('PyPDF2.PdfReader') as mock_pdf_reader:
            mock_page1 = Mock()
            mock_page1.extract_text.return_value = "Page 1 content"
            mock_page2 = Mock()
            mock_page2.extract_text.return_value = "Page 2 content"
            
            mock_reader = Mock()
            mock_reader.pages = [mock_page1, mock_page2]
            mock_pdf_reader.return_value = mock_reader
            
            text = await file_service.extract_text_from_pdf(file_path)
            
            assert "Page 1 content" in text
            assert "Page 2 content" in text
    
    async def test_extract_text_from_docx_success(self, file_service):
        """Test successful DOCX text extraction."""
        file_path = "/path/to/test.docx"
        
        # Mock python-docx
        with patch('docx.Document') as mock_docx:
            mock_paragraph1 = Mock()
            mock_paragraph1.text = "First paragraph"
            mock_paragraph2 = Mock()
            mock_paragraph2.text = "Second paragraph"
            
            mock_doc = Mock()
            mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
            mock_docx.return_value = mock_doc
            
            text = await file_service.extract_text_from_docx(file_path)
            
            assert "First paragraph" in text
            assert "Second paragraph" in text
            mock_docx.assert_called_once_with(file_path)
    
    async def test_extract_text_from_doc_success(self, file_service):
        """Test successful DOC text extraction using antiword."""
        file_path = "/path/to/test.doc"
        
        # Mock subprocess for antiword
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "DOC file content"
            mock_run.return_value.returncode = 0
            
            text = await file_service.extract_text_from_doc(file_path)
            
            assert text == "DOC file content"
            mock_run.assert_called_once()
    
    async def test_extract_text_from_doc_fallback(self, file_service):
        """Test DOC text extraction fallback when antiword fails."""
        file_path = "/path/to/test.doc"
        
        # Mock subprocess to fail
        with patch('subprocess.run', side_effect=Exception("antiword not found")):
            
            text = await file_service.extract_text_from_doc(file_path)
            
            # Should return error message
            assert "Error extracting text from DOC file" in text
    
    def test_get_file_type(self, file_service):
        """Test file type detection."""
        assert file_service.get_file_type("resume.pdf") == "pdf"
        assert file_service.get_file_type("resume.docx") == "docx"
        assert file_service.get_file_type("resume.doc") == "doc"
        assert file_service.get_file_type("resume.txt") == "txt"
        assert file_service.get_file_type("resume") == ""
    
    async def test_concurrent_file_processing(self, file_service, sample_pdf_content, sample_docx_content):
        """Test concurrent file processing for performance validation."""
        # Mock all file operations
        with patch.object(file_service, 'validate_file_type', return_value=True):
            with patch.object(file_service, 'validate_file_size', return_value=True):
                with patch.object(file_service, 'save_file', side_effect=lambda f, c: f"/uploads/{f}"):
                    with patch.object(file_service, 'extract_text_from_pdf', return_value="PDF text"):
                        with patch.object(file_service, 'extract_text_from_docx', return_value="DOCX text"):
                            
                            # Create multiple concurrent tasks
                            tasks = []
                            for i in range(3):
                                task1 = file_service.process_uploaded_file(f"resume{i}.pdf", sample_pdf_content)
                                task2 = file_service.process_uploaded_file(f"resume{i}.docx", sample_docx_content)
                                tasks.extend([task1, task2])
                            
                            # Execute concurrently
                            results = await asyncio.gather(*tasks)
                            
                            # Verify all processing completed successfully
                            assert len(results) == 6
                            for result in results:
                                assert result["success"] is True
                                assert "processing_time" in result
                                assert result["processing_time"] > 0
    
    async def test_large_file_processing_simulation(self, file_service):
        """Test processing simulation for large files."""
        filename = "large_resume.pdf"
        large_content = b"Large file content" * 1000  # Simulate larger file
        
        # Mock file operations with realistic timing
        async def mock_save_with_delay(f, c):
            await asyncio.sleep(0.1)  # Simulate file I/O delay
            return f"/uploads/{f}"
        
        async def mock_extract_with_delay(path):
            await asyncio.sleep(0.2)  # Simulate text extraction delay
            return "Large file extracted text"
        
        with patch.object(file_service, 'validate_file_type', return_value=True):
            with patch.object(file_service, 'validate_file_size', return_value=True):
                with patch.object(file_service, 'save_file', side_effect=mock_save_with_delay):
                    with patch.object(file_service, 'extract_text_from_pdf', side_effect=mock_extract_with_delay):
                        
                        import time
                        start_time = time.time()
                        result = await file_service.process_uploaded_file(filename, large_content)
                        end_time = time.time()
                        
                        # Verify processing completed
                        assert result["success"] is True
                        assert result["file_size"] == len(large_content)
                        
                        # Verify timing was recorded
                        processing_time = end_time - start_time
                        assert processing_time >= 0.3  # At least the simulated delays
                        assert result["processing_time"] > 0


class TestFileServiceValidation:
    """Test FileService validation methods."""
    
    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        return FileService()
    
    def test_validate_file_type_supported_types(self, file_service):
        """Test file type validation for supported types."""
        supported_files = [
            "resume.pdf",
            "resume.PDF",  # Case insensitive
            "resume.docx",
            "resume.DOCX",
            "resume.doc",
            "resume.DOC"
        ]
        
        for filename in supported_files:
            assert file_service.validate_file_type(filename) is True
    
    def test_validate_file_type_unsupported_types(self, file_service):
        """Test file type validation for unsupported types."""
        unsupported_files = [
            "resume.txt",
            "resume.rtf",
            "resume.odt",
            "resume.html",
            "resume.jpg",
            "resume.png",
            "resume",  # No extension
            ".pdf",   # No filename
            "",       # Empty string
        ]
        
        for filename in unsupported_files:
            assert file_service.validate_file_type(filename) is False
    
    def test_validate_file_size_within_limits(self, file_service):
        """Test file size validation within acceptable limits."""
        # Test various sizes within limit
        valid_sizes = [
            1024,        # 1KB
            102400,      # 100KB
            1048576,     # 1MB
            5242880,     # 5MB (assuming 10MB limit)
        ]
        
        for size in valid_sizes:
            assert file_service.validate_file_size(size) is True
    
    def test_validate_file_size_exceeds_limits(self, file_service):
        """Test file size validation exceeding limits."""
        # Test sizes that should fail
        invalid_sizes = [
            0,              # Zero size
            -1,             # Negative size
            10485761,       # Just over 10MB (assuming 10MB limit)
            104857600,      # 100MB
        ]
        
        for size in invalid_sizes:
            assert file_service.validate_file_size(size) is False
    
    def test_generate_unique_filename_uniqueness(self, file_service):
        """Test that generated filenames are unique."""
        original_filename = "resume.pdf"
        
        # Generate multiple filenames
        filenames = set()
        for _ in range(10):
            unique_filename = file_service.generate_unique_filename(original_filename)
            filenames.add(unique_filename)
        
        # All should be unique
        assert len(filenames) == 10
        
        # All should have the same extension
        for filename in filenames:
            assert filename.endswith(".pdf")
            assert len(filename) > len(original_filename)
