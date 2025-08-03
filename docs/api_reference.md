# HR Resume Search API - Complete Reference Guide

**Version**: 1.0.0  
**Base URL**: `http://localhost:8000`  
**Last Updated**: 2025-08-03

## Table of Contents

- [Authentication](#authentication)
- [Core Features](#core-features)
- [API Endpoints](#api-endpoints)
  - [Health & Monitoring](#health--monitoring)
  - [Authentication & Authorization](#authentication--authorization)
  - [Resume Management](#resume-management)
  - [Search & Discovery](#search--discovery)
  - [Project Management](#project-management)
  - [Endpoint Management](#endpoint-management)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Response Formats](#response-formats)

## Core Features

### 🧠 AI-Powered Resume Parsing
- **Claude AI Integration**: Advanced resume text extraction and structured data conversion
- **Multi-Format Support**: PDF, DOC, DOCX file processing
- **Intelligent Parsing**: Skills extraction, experience analysis, company detection

### 🔍 Sophisticated Search Algorithms
- **Multi-Criteria Matching**: Skills (40%), Experience (30%), Company (15%), Department (15%)
- **Similarity Scoring**: Advanced profile matching with weighted algorithms  
- **Colleague Discovery**: Find former colleagues with overlap analysis
- **Natural Language Search**: AI-powered query interpretation

### 🚀 MCP Server Integration
- **Model Context Protocol**: Professional search tools and automations
- **Real-time Processing**: Async resume processing and search operations
- **Extensible Architecture**: Plugin-based tool system

---

## Authentication

All API endpoints require authentication using **JWT Bearer tokens** unless specified otherwise.

### Authentication Header
```bash
Authorization: Bearer <your_jwt_token>
```

### API Key Authentication (Alternative)
```bash
X-API-Key: <your_api_key>
```

---

## API Endpoints

### Health & Monitoring

#### `GET /` - Root Endpoint
**Description**: Basic API information and available endpoints

```bash
curl -X GET "http://localhost:8000/"
```

**Response**:
```json
{
  "message": "HR Resume Search MCP API is running",
  "version": "1.0.0",
  "environment": "development",
  "docs": "/docs",
  "endpoints": {
    "health": "/health",
    "readiness": "/readiness",
    "auth": "/api/v1/auth",
    "resumes": "/api/v1/resumes",
    "search": "/api/v1/search"
  }
}
```

#### `GET /health` - Health Check
**Description**: Lightweight health status check

```bash
curl -X GET "http://localhost:8000/health"
```

**Response**:
```json
{
  "status": "healthy",
  "service": "HR Resume Search MCP API",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

#### `GET /readiness` - Readiness Check
**Description**: Comprehensive system readiness validation

```bash
curl -X GET "http://localhost:8000/readiness"
```

**Response**:
```json
{
  "status": "ready",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.2
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 8.5
    },
    "mcp_server": {
      "status": "healthy",
      "response_time_ms": 45.1
    }
  },
  "total_check_time_ms": 68.8,
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

#### `GET /metrics` - System Metrics
**Description**: Application metrics for monitoring

```bash
curl -X GET "http://localhost:8000/metrics" \
  -H "Authorization: Bearer <token>"
```

**Response**:
```json
{
  "service": "HR Resume Search MCP API",
  "version": "1.0.0",
  "environment": "development",
  "metrics": {
    "users_total": 45,
    "candidates_total": 1234,
    "resumes_total": 987,
    "resume_status": {
      "completed": 850,
      "processing": 45,
      "failed": 92
    }
  },
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

---

### Authentication & Authorization

#### `POST /api/v1/auth/register` - User Registration
**Description**: Register a new user account

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "username": "hr_manager",
    "password": "SecurePass123!",
    "full_name": "Jane HR Manager"
  }'
```

**Response**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@company.com",
  "username": "hr_manager",
  "full_name": "Jane HR Manager",
  "is_active": true,
  "created_at": "2025-08-03T10:30:00.000Z"
}
```

#### `POST /api/v1/auth/login` - User Login
**Description**: Authenticate user and receive JWT tokens

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@company.com&password=SecurePass123!"
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### `POST /api/v1/auth/refresh` - Refresh Access Token
**Description**: Get new access token using refresh token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

#### `GET /api/v1/auth/me` - Current User Info
**Description**: Get current authenticated user information

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <token>"
```

#### `POST /api/v1/auth/api-keys` - Create API Key
**Description**: Generate new API key for programmatic access

```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Integration Key",
    "description": "Key for HR system integration",
    "scopes": ["read:resumes", "write:resumes", "search:candidates"],
    "expires_in_days": 90
  }'
```

---

### Resume Management

#### `POST /api/v1/resumes/upload` - Upload Resume
**Description**: Upload and process resume files with AI-powered parsing

```bash
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"
```

**Response**:
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "john_doe_resume.pdf",
  "file_size": 245760,
  "mime_type": "application/pdf",
  "status": "processing",
  "processing_started_at": "2025-08-03T10:30:00.000Z",
  "estimated_completion": "2025-08-03T10:32:00.000Z"
}
```

#### `GET /api/v1/resumes/{file_id}` - Get Resume Details
**Description**: Retrieve detailed resume information including parsed data

```bash
curl -X GET "http://localhost:8000/api/v1/resumes/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"
```

**Response**:
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate": {
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "full_name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "+1-555-0123",
    "location": "San Francisco, CA",
    "headline": "Senior Software Engineer",
    "summary": "Experienced software engineer with 8+ years...",
    "total_experience_years": 8
  },
  "parsed_data": {
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
    "education": [
      {
        "degree": "B.S. Computer Science",
        "institution": "UC Berkeley",
        "year": 2015
      }
    ],
    "work_experience": [
      {
        "company": "Tech Corp",
        "position": "Senior Software Engineer", 
        "department": "Engineering",
        "start_date": "2020-01-15",
        "end_date": null,
        "is_current": true,
        "description": "Lead development of microservices architecture..."
      }
    ]
  },
  "processing_status": "completed",
  "processed_at": "2025-08-03T10:31:45.000Z",
  "processing_time_ms": 2450
}
```

#### `GET /api/v1/resumes/` - List Resumes
**Description**: List resumes with filtering and pagination

```bash
curl -X GET "http://localhost:8000/api/v1/resumes/?status=completed&limit=10&skip=0" \
  -H "Authorization: Bearer <token>"
```

**Query Parameters**:
- `status`: Filter by processing status (`processing`, `completed`, `failed`)
- `limit`: Number of results (default: 50, max: 100)
- `skip`: Pagination offset (default: 0)

#### `POST /api/v1/resumes/{file_id}/reprocess` - Reprocess Resume
**Description**: Reprocess a resume with updated AI parsing

```bash
curl -X POST "http://localhost:8000/api/v1/resumes/550e8400-e29b-41d4-a716-446655440000/reprocess" \
  -H "Authorization: Bearer <token>"
```

#### `DELETE /api/v1/resumes/{file_id}` - Delete Resume
**Description**: Delete resume and associated data

```bash
curl -X DELETE "http://localhost:8000/api/v1/resumes/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"
```

---

### Search & Discovery

#### `POST /api/v1/search/candidates` - Smart Candidate Search
**Description**: Advanced candidate search with multi-criteria matching

```bash
curl -X POST "http://localhost:8000/api/v1/search/candidates" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Senior Python developer",
    "search_type": "skills_match",
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "min_experience_years": 5,
    "max_experience_years": 15,
    "companies": ["Google", "Meta", "Amazon"],
    "departments": ["Engineering", "Data Science"],
    "locations": ["San Francisco", "New York"],
    "education_level": "bachelors",
    "limit": 20,
    "offset": 0
  }'
```

**Response**:
```json
{
  "success": true,
  "query": "Senior Python developer",
  "search_type": "skills_match",
  "total_results": 45,
  "results": [
    {
      "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
      "resume_id": "550e8400-e29b-41d4-a716-446655440000",
      "full_name": "John Doe",
      "current_position": "Senior Software Engineer",
      "current_company": "Tech Corp",
      "total_experience_years": 8,
      "match_score": 0.92,
      "match_reasons": [
        "Skills: Python, FastAPI, PostgreSQL",
        "Worked at Tech Corp",
        "Worked in Engineering"
      ],
      "highlights": {
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "location": "San Francisco, CA",
        "headline": "Senior Software Engineer"
      }
    }
  ],
  "processing_time_ms": 245
}
```

#### `POST /api/v1/search/similar` - Find Similar Profiles
**Description**: Find candidates with similar profiles to a reference candidate

```bash
curl -X POST "http://localhost:8000/api/v1/search/similar?candidate_id=123e4567-e89b-12d3-a456-426614174000&limit=10" \
  -H "Authorization: Bearer <token>"
```

**Response**:
```json
{
  "success": true,
  "query": "Similar to John Doe",
  "search_type": "similar_candidates",
  "total_results": 8,
  "results": [
    {
      "candidate_id": "456e7890-e89b-12d3-a456-426614174001",
      "full_name": "Jane Smith",
      "current_position": "Senior Software Engineer",
      "total_experience_years": 7,
      "match_score": 0.85,
      "match_reasons": [
        "Common skills: Python, FastAPI, Docker",
        "Similar experience: 7 years",
        "Same department: Engineering"
      ]
    }
  ],
  "processing_time_ms": 156
}
```

#### `POST /api/v1/search/colleagues` - Find Former Colleagues
**Description**: Discover former colleagues with workplace overlap analysis

```bash
curl -X POST "http://localhost:8000/api/v1/search/colleagues?candidate_id=123e4567-e89b-12d3-a456-426614174000&limit=15" \
  -H "Authorization: Bearer <token>"
```

**Response**:
```json
{
  "success": true,
  "query": "Colleagues of John Doe",
  "search_type": "worked_with",
  "total_results": 12,
  "results": [
    {
      "candidate_id": "789e0123-e89b-12d3-a456-426614174002",
      "full_name": "Mike Johnson",
      "current_position": "Engineering Manager",
      "match_score": 0.78,
      "match_reasons": [
        "Worked together at Tech Corp",
        "Overlap: 18 months",
        "Same department: Engineering"
      ],
      "highlights": {
        "company": "Tech Corp",
        "department": "Engineering",
        "overlap_months": 18,
        "positions": {
          "original": "Senior Software Engineer",
          "colleague": "Engineering Manager"
        }
      }
    }
  ],
  "processing_time_ms": 189
}
```

#### `GET /api/v1/search/filters` - Get Search Filters
**Description**: Retrieve available search filters with counts and statistics

```bash
curl -X GET "http://localhost:8000/api/v1/search/filters" \
  -H "Authorization: Bearer <token>"
```

**Response**:
```json
{
  "companies": [
    {"name": "Google", "count": 45},
    {"name": "Meta", "count": 38},
    {"name": "Amazon", "count": 52}
  ],
  "departments": [
    {"name": "Engineering", "count": 234},
    {"name": "Data Science", "count": 67},
    {"name": "Product", "count": 89}
  ],
  "locations": [
    {"name": "San Francisco, CA", "count": 145},
    {"name": "New York, NY", "count": 123},
    {"name": "Seattle, WA", "count": 98}
  ],
  "skills": [
    {"name": "Python", "count": 189},
    {"name": "JavaScript", "count": 167},
    {"name": "SQL", "count": 201}
  ],
  "experience_range": {
    "min": 0,
    "max": 25,
    "average": 6.7
  },
  "statistics": {
    "total_candidates": 1234,
    "total_resumes": 987,
    "last_updated": "2025-08-03T10:30:00.000Z"
  }
}
```

#### `POST /api/v1/search/smart` - AI-Powered Natural Language Search
**Description**: Natural language search with AI query interpretation

```bash
curl -X POST "http://localhost:8000/api/v1/search/smart" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find me Python developers with 5+ years who worked at startups",
    "limit": 15,
    "include_reasoning": true
  }'
```

**Response**:
```json
{
  "success": true,
  "interpreted_query": {
    "original_query": "Find me Python developers with 5+ years who worked at startups",
    "detected_intent": "skills_match",
    "extracted_criteria": {
      "skills": ["python"],
      "min_experience_years": 5
    }
  },
  "results": [
    {
      "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
      "full_name": "Sarah Chen",
      "match_score": 0.89,
      "match_reasons": ["Skills: Python", "Experience: 6 years"]
    }
  ],
  "reasoning": "I interpreted your query as looking for skills match. I detected these skills: python. I found you're looking for candidates with at least 5 years of experience. I found 23 matching candidates.",
  "suggested_queries": [
    "Show me senior Python developers",
    "Find candidates who worked at top tech companies",
    "Show me candidates with leadership experience"
  ],
  "processing_time_ms": 312
}
```

#### Enhanced Search Endpoints (New)

#### `GET /api/v1/search/skills` - Search by Skills
**Description**: Search candidates by specific skills with match scoring

```bash
curl -X GET "http://localhost:8000/api/v1/search/skills?skills=Python,FastAPI,Docker&min_score=0.3&limit=50" \
  -H "Authorization: Bearer <token>"
```

#### `GET /api/v1/search/department` - Search by Department
**Description**: Find candidates by department and seniority level

```bash
curl -X GET "http://localhost:8000/api/v1/search/department?department=Engineering&seniority=senior&limit=50" \
  -H "Authorization: Bearer <token>"
```

#### `GET /api/v1/search/colleagues` - Enhanced Colleagues Search
**Description**: Find colleagues with advanced filtering options

```bash
curl -X GET "http://localhost:8000/api/v1/search/colleagues?candidate_id=123&include_potential=true&min_overlap_months=3" \
  -H "Authorization: Bearer <token>"
```

#### `GET /api/v1/search/similar/{candidate_id}` - Enhanced Similar Search
**Description**: Find similar candidates with improved algorithm

```bash
curl -X GET "http://localhost:8000/api/v1/search/similar/123?limit=10" \
  -H "Authorization: Bearer <token>"
```

---

### Project Management

#### `POST /api/v1/projects/` - Create Project
**Description**: Create a new API development project

```bash
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HR Integration Project",
    "slug": "hr-integration",
    "description": "Integration APIs for HR management system"
  }'
```

#### `GET /api/v1/projects/` - List Projects
**Description**: List all projects for the current user

```bash
curl -X GET "http://localhost:8000/api/v1/projects/" \
  -H "Authorization: Bearer <token>"
```

#### `GET /api/v1/projects/{project_id}` - Get Project
**Description**: Get specific project details

```bash
curl -X GET "http://localhost:8000/api/v1/projects/1" \
  -H "Authorization: Bearer <token>"
```

#### `POST /api/v1/projects/{project_id}/endpoints` - Create Project Endpoint
**Description**: Create an endpoint within a specific project

```bash
curl -X POST "http://localhost:8000/api/v1/projects/1/endpoints" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/api/v1/employees",
    "method": "GET",
    "name": "List Employees",
    "description": "Retrieve list of employees",
    "auth_required": true,
    "rate_limit": "100/minute"
  }'
```

---

### Endpoint Management

#### `POST /api/v1/endpoints/` - Create Global Endpoint
**Description**: Create a global endpoint not tied to a specific project

```bash
curl -X POST "http://localhost:8000/api/v1/endpoints/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/api/v1/global-resource",
    "method": "POST",
    "name": "Global Resource",
    "description": "System-wide resource endpoint",
    "auth_required": true,
    "rate_limit": "50/minute"
  }'
```

#### `GET /api/v1/endpoints/` - List All Endpoints
**Description**: List all endpoints in the system

```bash
curl -X GET "http://localhost:8000/api/v1/endpoints/" \
  -H "Authorization: Bearer <token>"
```

#### `GET /api/v1/endpoints/{endpoint_id}` - Get Specific Endpoint
**Description**: Retrieve details of a specific endpoint

```bash
curl -X GET "http://localhost:8000/api/v1/endpoints/1" \
  -H "Authorization: Bearer <token>"
```

#### `PUT /api/v1/endpoints/{endpoint_id}` - Update Endpoint
**Description**: Update an existing endpoint

```bash
curl -X PUT "http://localhost:8000/api/v1/endpoints/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/api/v1/updated-resource",
    "method": "PUT",
    "name": "Updated Resource",
    "description": "Updated endpoint description",
    "auth_required": false,
    "rate_limit": "200/minute"
  }'
```

#### `DELETE /api/v1/endpoints/{endpoint_id}` - Delete Endpoint
**Description**: Delete an endpoint

```bash
curl -X DELETE "http://localhost:8000/api/v1/endpoints/1" \
  -H "Authorization: Bearer <token>"
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "type": "validation_error",
    "status_code": 422,
    "message": "Request validation failed",
    "details": [
      {
        "loc": ["body", "email"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ],
    "timestamp": "2025-08-03T10:30:00.000Z"
  }
}
```

### HTTP Status Codes

| Code | Type | Description |
|------|------|-------------|
| `200` | Success | Request completed successfully |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource conflict (duplicate) |
| `422` | Unprocessable Entity | Validation error |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Service temporarily unavailable |

### Error Types

- `authentication_error`: Invalid or missing authentication
- `authorization_error`: Insufficient permissions
- `validation_error`: Request validation failed
- `not_found_error`: Resource not found
- `conflict_error`: Resource already exists
- `rate_limit_error`: Too many requests
- `processing_error`: Resume processing failed
- `internal_server_error`: Unexpected server error

---

## Rate Limiting

### Rate Limit Tiers

| Tier | Endpoints | Limit | Window |
|------|-----------|-------|--------|
| **Health** | `/health`, `/readiness` | 200/min | 1 minute |
| **Authentication** | `/auth/*` | 30/min | 1 minute |
| **Resume Upload** | `/resumes/upload` | 10/min | 1 minute |
| **Search Operations** | `/search/*` | 60/min | 1 minute |
| **General API** | All others | 100/min | 1 minute |
| **Administrative** | `/metrics` | 10/min | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641024000
X-RateLimit-Window: 60
```

### Rate Limit Error Response

```json
{
  "error": {
    "type": "rate_limit_error",
    "status_code": 429,
    "message": "Rate limit exceeded",
    "details": {
      "limit": 100,
      "window": "60 seconds",
      "retry_after": 45
    },
    "timestamp": "2025-08-03T10:30:00.000Z"
  }
}
```

---

## Response Formats

### Success Response Format

```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "completed"
  },
  "metadata": {
    "processing_time_ms": 245,
    "api_version": "1.0.0",
    "timestamp": "2025-08-03T10:30:00.000Z"
  }
}
```

### Pagination Format

```json
{
  "results": [...],
  "pagination": {
    "total": 1234,
    "limit": 50,
    "offset": 0,
    "has_next": true,
    "has_prev": false,
    "next_offset": 50,
    "prev_offset": null
  }
}
```

### Search Response Format

```json
{
  "success": true,
  "query": "search query",
  "search_type": "skills_match",
  "total_results": 45,
  "results": [...],
  "processing_time_ms": 245,
  "filters_applied": {
    "skills": ["Python", "FastAPI"],
    "experience_range": [5, 15]
  }
}
```

---

## Next Steps

1. **Integration Guide**: See `/docs/mcp_integration.md` for MCP server setup
2. **Deployment Guide**: See `/docs/deployment.md` for production deployment
3. **Performance Guide**: See `/docs/performance.md` for optimization tips
4. **Examples**: See `/docs/examples/` for practical integration examples

For support and questions, please refer to the project documentation or contact the development team.