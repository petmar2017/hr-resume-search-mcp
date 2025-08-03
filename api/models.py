"""
SQLAlchemy Database Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base


class User(Base):
    """
    User model for authentication and authorization
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class APIKey(Base):
    """
    API Key model for service authentication
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="api_keys")
    
    # Permissions
    scopes = Column(JSON, nullable=True)  # List of allowed scopes
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name})>"


class Project(Base):
    """
    Project model for organizing APIs
    """
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="projects")
    
    # Configuration
    config = Column(JSON, nullable=True)  # Project-specific settings
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    endpoints = relationship("Endpoint", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"


class Endpoint(Base):
    """
    API Endpoint model
    """
    __tablename__ = "endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # Endpoint details
    path = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, etc.
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Project relationship
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="endpoints")
    
    # Configuration
    request_schema = Column(JSON, nullable=True)  # Pydantic model as JSON
    response_schema = Column(JSON, nullable=True)  # Pydantic model as JSON
    headers = Column(JSON, nullable=True)  # Required headers
    query_params = Column(JSON, nullable=True)  # Query parameters
    
    # Authentication
    auth_required = Column(Boolean, default=True, nullable=False)
    scopes_required = Column(JSON, nullable=True)  # Required scopes
    
    # Rate limiting
    rate_limit = Column(Integer, nullable=True)  # Requests per minute
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_deprecated = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        return f"<Endpoint(id={self.id}, path={self.path}, method={self.method})>"


class RequestLog(Base):
    """
    Request logging for monitoring and analytics
    """
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Request details
    request_id = Column(String(36), unique=True, index=True, nullable=False)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    query_params = Column(JSON, nullable=True)
    headers = Column(JSON, nullable=True)
    body = Column(JSON, nullable=True)
    
    # Response details
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    response_size_bytes = Column(Integer, nullable=True)
    
    # User details
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Error details
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<RequestLog(id={self.id}, method={self.method}, path={self.path})>"


class Candidate(Base):
    """
    Candidate model for HR system
    """
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # Personal Information
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Professional Links
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    
    # Professional Summary
    headline = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    
    # Current Status
    current_position = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True, index=True)
    total_experience_years = Column(Integer, nullable=True)
    
    # Preferences
    preferred_locations = Column(JSON, nullable=True)  # List of locations
    salary_expectations = Column(JSON, nullable=True)  # Min, max, currency
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    work_experiences = relationship("WorkExperience", back_populates="candidate", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, name={self.full_name}, email={self.email})>"


class Resume(Base):
    """
    Resume model for storing parsed resume data
    """
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # File Information
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, doc, docx
    file_path = Column(String(500), nullable=True)  # Storage path
    file_size_bytes = Column(Integer, nullable=True)
    
    # Candidate Relationship
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    candidate = relationship("Candidate", back_populates="resumes")
    
    # Parsed Data
    parsed_data = Column(JSON, nullable=False)  # Complete structured data
    
    # Extracted Fields for Searching
    skills = Column(JSON, nullable=True)  # List of skills
    education = Column(JSON, nullable=True)  # Education history
    certifications = Column(JSON, nullable=True)  # Certifications
    languages = Column(JSON, nullable=True)  # Language proficiencies
    
    # Metadata
    parsing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    parsing_error = Column(Text, nullable=True)
    parsing_time_ms = Column(Integer, nullable=True)
    
    # Search Optimization
    search_vector = Column(Text, nullable=True)  # Text search vector
    tags = Column(JSON, nullable=True)  # Custom tags
    notes = Column(Text, nullable=True)  # HR notes
    
    # Upload Information
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    parsed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        return f"<Resume(id={self.id}, candidate_id={self.candidate_id}, file={self.file_name})>"


class WorkExperience(Base):
    """
    Work experience model for detailed employment history
    """
    __tablename__ = "work_experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Candidate Relationship
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    candidate = relationship("Candidate", back_populates="work_experiences")
    
    # Company Information
    company = Column(String(255), nullable=False, index=True)
    position = Column(String(255), nullable=False, index=True)
    department = Column(String(255), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    
    # Duration
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    
    # Details
    description = Column(Text, nullable=True)
    responsibilities = Column(JSON, nullable=True)  # List of responsibilities
    achievements = Column(JSON, nullable=True)  # List of achievements
    technologies_used = Column(JSON, nullable=True)  # Technologies/tools used
    
    # Colleagues (for "worked with" searches)
    colleagues = Column(JSON, nullable=True)  # List of colleague names
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        return f"<WorkExperience(id={self.id}, company={self.company}, position={self.position})>"


class SearchHistory(Base):
    """
    Search history for analytics and improving search
    """
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Search Details
    query = Column(Text, nullable=False)
    search_type = Column(String(50), nullable=False)  # similar, department, worked_with, etc.
    filters = Column(JSON, nullable=True)
    
    # Results
    results_count = Column(Integer, nullable=False)
    results = Column(JSON, nullable=True)  # Top results returned
    
    # Performance
    processing_time_ms = Column(Integer, nullable=False)
    
    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamp
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SearchHistory(id={self.id}, query={self.query[:50]})>"