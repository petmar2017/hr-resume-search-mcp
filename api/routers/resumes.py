"""Resume management router for handling file uploads and processing."""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..database import get_db
from ..models import Resume, Candidate, User
from ..schemas import ResumeCreate, ResumeResponse, ResumeUploadResponse
from ..auth import get_current_active_user
from ..services.claude_service import ClaudeService
from ..services.file_service import FileService
from ..config import settings

router = APIRouter(
    prefix="/api/v1/resumes",
    tags=["resumes"],
    responses={404: {"description": "Not found"}},
)

# Initialize services
claude_service = ClaudeService()
file_service = FileService()

# Configure upload settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
UPLOAD_DIR = Path(settings.upload_dir or "uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a resume file for processing.
    
    Accepts PDF, DOC, and DOCX files up to 10MB.
    The file will be parsed using Claude AI to extract structured data.
    """
    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{file_extension}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Extract text from file
    try:
        extracted_text = await file_service.extract_text(file_path, file_extension)
    except Exception as e:
        # Clean up file on extraction failure
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from file: {str(e)}"
        )
    
    # Create database entry
    resume = Resume(
        file_id=file_id,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_extension[1:],  # Remove the dot
        raw_text=extracted_text,
        status="pending",
        uploaded_by_id=current_user.id,
        upload_timestamp=datetime.utcnow()
    )
    
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    # Queue for Claude processing (async)
    # TODO: Implement Celery task for background processing
    # For now, we'll process synchronously
    try:
        parsed_data = await claude_service.parse_resume(extracted_text)
        
        # Update resume with parsed data
        resume.parsed_data = parsed_data
        resume.status = "completed"
        resume.parsed_timestamp = datetime.utcnow()
        
        # Create or update candidate if email is found
        if parsed_data.get("email"):
            candidate = db.query(Candidate).filter(
                Candidate.email == parsed_data["email"]
            ).first()
            
            if not candidate:
                candidate = Candidate(
                    email=parsed_data.get("email"),
                    name=parsed_data.get("name"),
                    phone=parsed_data.get("phone"),
                    location=parsed_data.get("location"),
                    linkedin_url=parsed_data.get("linkedin_url"),
                    github_url=parsed_data.get("github_url")
                )
                db.add(candidate)
            
            resume.candidate = candidate
        
        db.commit()
        db.refresh(resume)
        
    except Exception as e:
        # Log error but don't fail the upload
        resume.status = "failed"
        resume.error_message = str(e)
        db.commit()
        print(f"Failed to parse resume {file_id}: {e}")
    
    return ResumeUploadResponse(
        file_id=resume.file_id,
        filename=resume.original_filename,
        status=resume.status,
        message="Resume uploaded successfully. Processing in progress.",
        upload_timestamp=resume.upload_timestamp
    )


@router.get("/{file_id}", response_model=ResumeResponse)
async def get_resume(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get resume details by file ID."""
    resume = db.query(Resume).filter(Resume.file_id == file_id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check permissions (user can only see their own resumes unless admin)
    if not current_user.is_superuser and resume.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this resume"
        )
    
    return resume


@router.get("/", response_model=List[ResumeResponse])
async def list_resumes(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List resumes with optional filtering."""
    query = db.query(Resume)
    
    # Non-admin users can only see their own resumes
    if not current_user.is_superuser:
        query = query.filter(Resume.uploaded_by_id == current_user.id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Resume.status == status)
    
    resumes = query.offset(skip).limit(limit).all()
    return resumes


@router.delete("/{file_id}")
async def delete_resume(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a resume and its associated file."""
    resume = db.query(Resume).filter(Resume.file_id == file_id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check permissions
    if not current_user.is_superuser and resume.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this resume"
        )
    
    # Delete file from disk
    try:
        file_path = Path(resume.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Failed to delete file {resume.file_path}: {e}")
    
    # Delete from database
    db.delete(resume)
    db.commit()
    
    return {"message": "Resume deleted successfully"}


@router.post("/{file_id}/reprocess")
async def reprocess_resume(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Reprocess a resume with Claude AI."""
    resume = db.query(Resume).filter(Resume.file_id == file_id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check permissions
    if not current_user.is_superuser and resume.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reprocess this resume"
        )
    
    # Reset status
    resume.status = "processing"
    resume.error_message = None
    db.commit()
    
    try:
        # Re-extract text if needed
        if not resume.raw_text:
            file_path = Path(resume.file_path)
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resume file not found on disk"
                )
            
            extracted_text = await file_service.extract_text(
                file_path, 
                f".{resume.file_type}"
            )
            resume.raw_text = extracted_text
        
        # Parse with Claude
        parsed_data = await claude_service.parse_resume(resume.raw_text)
        
        # Update resume
        resume.parsed_data = parsed_data
        resume.status = "completed"
        resume.parsed_timestamp = datetime.utcnow()
        
        db.commit()
        db.refresh(resume)
        
        return {
            "message": "Resume reprocessed successfully",
            "status": resume.status,
            "parsed_data": resume.parsed_data
        }
        
    except Exception as e:
        resume.status = "failed"
        resume.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess resume: {str(e)}"
        )