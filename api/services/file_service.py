"""File service for handling document processing and text extraction."""

import os
from pathlib import Path
from typing import Optional
import pypdf
import docx
import magic


class FileService:
    """Service for file operations and text extraction."""
    
    def __init__(self):
        """Initialize file service."""
        self.mime = magic.Magic(mime=True)
    
    async def extract_text(self, file_path: Path, file_extension: str) -> str:
        """
        Extract text from various file formats.
        
        Args:
            file_path: Path to the file
            file_extension: File extension (e.g., '.pdf', '.docx')
            
        Returns:
            Extracted text content
        """
        file_extension = file_extension.lower()
        
        if file_extension == ".pdf":
            return self._extract_pdf_text(file_path)
        elif file_extension in [".doc", ".docx"]:
            return self._extract_docx_text(file_path)
        else:
            # Try to read as plain text
            return self._extract_plain_text(file_path)
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
        
        return text.strip()
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            doc = docx.Document(file_path)
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + "\t"
                    text += "\n"
                    
        except Exception as e:
            raise Exception(f"Failed to extract text from DOCX: {str(e)}")
        
        return text.strip()
    
    def _extract_plain_text(self, file_path: Path) -> str:
        """
        Extract text from plain text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            File content
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Failed to read text file: {str(e)}")
    
    def validate_file(self, file_path: Path, expected_type: Optional[str] = None) -> bool:
        """
        Validate file type and integrity.
        
        Args:
            file_path: Path to file
            expected_type: Expected MIME type
            
        Returns:
            True if file is valid
        """
        if not file_path.exists():
            return False
        
        if expected_type:
            detected_type = self.mime.from_file(str(file_path))
            return detected_type == expected_type
        
        return True
    
    def get_file_metadata(self, file_path: Path) -> dict:
        """
        Get file metadata.
        
        Args:
            file_path: Path to file
            
        Returns:
            File metadata dictionary
        """
        if not file_path.exists():
            return {}
        
        stats = file_path.stat()
        
        return {
            "size": stats.st_size,
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "mime_type": self.mime.from_file(str(file_path)),
            "extension": file_path.suffix
        }
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace unsafe characters
        unsafe_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        for char in unsafe_chars:
            filename = filename.replace(char, "_")
        
        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 100:
            name = name[:100]
        
        return name + ext