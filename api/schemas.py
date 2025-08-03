"""
Pydantic Schemas for Request/Response Models
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"


class FileType(str, Enum):
    """Supported file types for resume upload"""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"


class EducationLevel(str, Enum):
    """Education level enumeration"""
    HIGH_SCHOOL = "high_school"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"
    OTHER = "other"


class SearchType(str, Enum):
    """Search type enumeration"""
    SIMILAR_CANDIDATES = "similar_candidates"
    SAME_DEPARTMENT = "same_department"
    WORKED_WITH = "worked_with"
    SKILLS_MATCH = "skills_match"
    EXPERIENCE_MATCH = "experience_match"


# Base Schemas
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema"""
    id: int
    uuid: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None


# Token Schemas
class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


# API Key Schemas
class APIKeyCreate(BaseModel):
    """API key creation schema"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response schema"""
    id: int
    key: str
    name: str
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Resume Schemas
class Education(BaseModel):
    """Education information schema"""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    level: EducationLevel
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    description: Optional[str] = None


class WorkExperience(BaseModel):
    """Work experience schema"""
    company: str
    position: str
    department: Optional[str] = None
    location: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    is_current: bool = False
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    colleagues: Optional[List[str]] = None  # Names of colleagues worked with


class Skill(BaseModel):
    """Skill schema"""
    name: str
    level: Optional[str] = Field(None, description="Proficiency level")
    years_of_experience: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None  # Technical, Soft, Language, etc.


class Certification(BaseModel):
    """Certification schema"""
    name: str
    issuer: str
    issue_date: datetime
    expiry_date: Optional[datetime] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None


class Language(BaseModel):
    """Language proficiency schema"""
    language: str
    proficiency: str  # Native, Fluent, Professional, Basic


class ResumeData(BaseModel):
    """Structured resume data schema"""
    # Personal Information
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    
    # Professional Summary
    summary: Optional[str] = None
    headline: Optional[str] = None
    
    # Experience and Education
    work_experiences: List[WorkExperience] = []
    education: List[Education] = []
    
    # Skills and Qualifications
    skills: List[Skill] = []
    certifications: List[Certification] = []
    languages: List[Language] = []
    
    # Additional Information
    projects: Optional[List[Dict[str, Any]]] = None
    publications: Optional[List[Dict[str, Any]]] = None
    awards: Optional[List[Dict[str, Any]]] = None
    interests: Optional[List[str]] = None
    
    # Metadata
    total_experience_years: Optional[float] = None
    current_position: Optional[str] = None
    current_company: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    salary_expectations: Optional[Dict[str, Any]] = None


class ResumeCreate(BaseModel):
    """Resume creation schema"""
    candidate_id: int
    file_name: str
    file_type: FileType
    file_size: Optional[int] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ResumeUploadRequest(BaseModel):
    """Resume upload request schema"""
    file_name: str
    file_type: FileType
    candidate_name: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ResumeUploadResponse(BaseResponse):
    """Resume upload response schema"""
    resume_id: str
    candidate_id: str
    file_name: str
    status: str  # processing, completed, failed
    parsed_data: Optional[ResumeData] = None
    processing_time_ms: Optional[int] = None


class ResumeResponse(BaseModel):
    """Resume response schema"""
    id: int
    uuid: str
    candidate_id: str
    file_name: str
    file_type: FileType
    parsed_data: ResumeData
    upload_date: datetime
    last_updated: Optional[datetime] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Search Schemas
class SearchRequest(BaseModel):
    """Search request schema"""
    query: str
    search_type: SearchType
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    # Advanced filters
    skills: Optional[List[str]] = None
    min_experience_years: Optional[int] = Field(None, ge=0)
    max_experience_years: Optional[int] = Field(None, ge=0)
    education_level: Optional[EducationLevel] = None
    companies: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    locations: Optional[List[str]] = None


class SearchResult(BaseModel):
    """Individual search result schema"""
    candidate_id: str
    resume_id: str
    full_name: str
    current_position: Optional[str] = None
    current_company: Optional[str] = None
    total_experience_years: Optional[float] = None
    match_score: float = Field(..., ge=0.0, le=1.0)
    match_reasons: List[str] = []
    highlights: Optional[Dict[str, Any]] = None


class SearchResponse(BaseResponse):
    """Search response schema"""
    query: str
    search_type: SearchType
    total_results: int
    results: List[SearchResult]
    facets: Optional[Dict[str, Any]] = None  # Aggregations for filtering
    processing_time_ms: int


# Smart Search Schemas
class SmartSearchRequest(BaseModel):
    """Smart search request using natural language"""
    query: str  # Natural language query
    context: Optional[Dict[str, Any]] = None  # Additional context
    limit: int = Field(default=10, ge=1, le=100)
    include_reasoning: bool = False  # Include AI reasoning in response


class SmartSearchResponse(BaseResponse):
    """Smart search response with AI-powered results"""
    interpreted_query: Dict[str, Any]  # How AI interpreted the query
    results: List[SearchResult]
    reasoning: Optional[str] = None  # AI's reasoning for results
    suggested_queries: Optional[List[str]] = None  # Related search suggestions
    processing_time_ms: int


# Analytics Schemas
class CandidateAnalytics(BaseModel):
    """Candidate analytics schema"""
    total_candidates: int
    by_experience_level: Dict[str, int]
    by_education_level: Dict[str, int]
    top_skills: List[Dict[str, Any]]
    top_companies: List[Dict[str, Any]]
    average_experience_years: float


class SystemStats(BaseModel):
    """System statistics schema"""
    total_resumes: int
    total_searches: int
    average_search_time_ms: float
    storage_used_mb: float
    active_users: int


# Error Schemas
class ErrorDetail(BaseModel):
    """Error detail schema"""
    field: Optional[str] = None
    message: str
    error_code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    message: str
    error_code: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)