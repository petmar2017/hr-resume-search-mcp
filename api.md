# API Documentation - HR Resume Search MCP

## 🌐 Base URL
```
Development: http://localhost:8000/api/v1
Staging: https://staging.hr-resume-api.com/api/v1
Production: https://api.hr-resume.com/api/v1
```

## 🔐 Authentication

All API requests (except health checks and auth endpoints) require JWT authentication.

### Headers
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Token Lifecycle
- Access Token: 30 minutes
- Refresh Token: 7 days
- Token Type: Bearer

## 📚 API Endpoints

### Health & Status

#### GET /
Root endpoint providing basic API information.

**Response:**
```json
{
  "message": "API Builder is running",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "api-builder",
  "version": "1.0.0"
}
```

#### GET /readiness
Readiness check for Kubernetes deployments.

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "mcp_server": "healthy"
  }
}
```

### Authentication

#### POST /api/v1/auth/login
Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded

#### POST /api/v1/auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /api/v1/auth/logout
Invalidate current tokens.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### Resume Management

#### POST /api/v1/resumes/upload
Upload a resume file for processing.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Authentication: Required

**Form Data:**
```
file: <resume_file> (PDF, DOC, or DOCX)
candidate_email: user@example.com (optional)
metadata: {"source": "upload", "recruiter_id": "123"} (optional JSON)
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Resume uploaded successfully",
  "processing_id": "proc_123456",
  "estimated_time": 30
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file format
- `413 Payload Too Large`: File exceeds 10MB limit
- `422 Unprocessable Entity`: File corrupted or unreadable

#### GET /api/v1/resumes/{resume_id}
Get detailed information about a specific resume.

**Parameters:**
- `resume_id` (path): UUID of the resume

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0123",
    "location": "New York, NY"
  },
  "work_experience": [
    {
      "company": "Tech Corp",
      "position": "Senior Developer",
      "department": "Engineering",
      "desk": "Platform Team",
      "start_date": "2020-01-15",
      "end_date": "2023-06-30",
      "description": "Led development of microservices architecture"
    }
  ],
  "skills": [
    {
      "name": "Python",
      "category": "Programming",
      "proficiency": "Expert"
    },
    {
      "name": "FastAPI",
      "category": "Framework",
      "proficiency": "Advanced"
    }
  ],
  "education": [
    {
      "institution": "MIT",
      "degree": "BS Computer Science",
      "graduation_date": "2019-05-15"
    }
  ],
  "parsed_at": "2024-01-20T10:30:00Z",
  "original_format": "pdf",
  "processing_status": "completed"
}
```

#### GET /api/v1/resumes/search
Search resumes with various filters.

**Query Parameters:**
- `q` (string): Search query
- `skills` (array): Filter by skills
- `department` (string): Filter by department
- `desk` (string): Filter by desk
- `company` (string): Filter by company
- `min_experience` (integer): Minimum years of experience
- `location` (string): Location filter
- `page` (integer): Page number (default: 1)
- `limit` (integer): Results per page (default: 20, max: 100)
- `sort` (string): Sort field (relevance, date, experience)
- `order` (string): Sort order (asc, desc)

**Example Request:**
```
GET /api/v1/resumes/search?q=python developer&skills[]=Python&skills[]=FastAPI&department=Engineering&limit=10
```

**Response:**
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "candidate_name": "John Doe",
      "current_position": "Senior Developer",
      "current_company": "Tech Corp",
      "skills_match": 0.95,
      "experience_years": 8,
      "location": "New York, NY",
      "summary": "Experienced Python developer with FastAPI expertise..."
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 45,
    "pages": 5
  },
  "facets": {
    "skills": {
      "Python": 42,
      "JavaScript": 28,
      "FastAPI": 15
    },
    "departments": {
      "Engineering": 30,
      "Product": 10,
      "Data Science": 5
    }
  }
}
```

#### POST /api/v1/resumes/advanced-search
Advanced search with complex filters and AI-powered matching.

**Request:**
```json
{
  "must_have_skills": ["Python", "FastAPI"],
  "nice_to_have_skills": ["Docker", "Kubernetes"],
  "experience_range": {
    "min": 3,
    "max": 10
  },
  "companies": {
    "include": ["Tech Corp", "StartupXYZ"],
    "exclude": ["CompetitorCo"]
  },
  "departments": ["Engineering", "Platform"],
  "education_level": "Bachelor",
  "location_radius": {
    "location": "New York, NY",
    "radius_miles": 50
  },
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "matches": [
    {
      "resume_id": "550e8400-e29b-41d4-a716-446655440000",
      "match_score": 0.92,
      "candidate_summary": {
        "name": "John Doe",
        "current_role": "Senior Developer at Tech Corp",
        "experience_years": 8
      },
      "match_details": {
        "skills_match": 0.95,
        "experience_match": 0.90,
        "education_match": 1.0,
        "location_match": 1.0,
        "department_match": 0.85
      },
      "strengths": [
        "Strong Python and FastAPI experience",
        "Worked in similar department structure",
        "Location within specified radius"
      ],
      "gaps": [
        "Limited Kubernetes experience"
      ]
    }
  ],
  "total_matches": 15,
  "search_id": "search_abc123"
}
```

#### GET /api/v1/resumes/similar/{resume_id}
Find candidates similar to a specific resume.

**Parameters:**
- `resume_id` (path): UUID of the reference resume
- `limit` (query): Number of results (default: 10)
- `threshold` (query): Similarity threshold 0-1 (default: 0.7)

**Response:**
```json
{
  "reference_resume": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "candidate_name": "John Doe"
  },
  "similar_candidates": [
    {
      "resume_id": "660e8400-e29b-41d4-a716-446655440001",
      "candidate_name": "Jane Smith",
      "similarity_score": 0.89,
      "common_attributes": {
        "skills": ["Python", "FastAPI", "Docker"],
        "department": "Engineering",
        "experience_level": "Senior"
      },
      "differentiators": {
        "unique_skills": ["Rust", "GraphQL"],
        "additional_experience": "Team Lead experience"
      }
    }
  ]
}
```

#### GET /api/v1/resumes/network/{resume_id}
Discover professional network and connections.

**Parameters:**
- `resume_id` (path): UUID of the resume
- `depth` (query): Network depth 1-3 (default: 2)
- `relationship_type` (query): Type of relationship (colleague, same_department, same_company)

**Response:**
```json
{
  "candidate": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe"
  },
  "network": {
    "direct_connections": [
      {
        "resume_id": "660e8400-e29b-41d4-a716-446655440001",
        "name": "Jane Smith",
        "relationship": "colleague",
        "company": "Tech Corp",
        "department": "Engineering",
        "overlap_period": {
          "start": "2020-01-15",
          "end": "2023-06-30"
        }
      }
    ],
    "indirect_connections": [
      {
        "resume_id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Bob Johnson",
        "relationship": "same_department",
        "connection_path": ["John Doe", "Jane Smith", "Bob Johnson"],
        "common_companies": ["Tech Corp"]
      }
    ],
    "network_stats": {
      "total_connections": 45,
      "direct_connections": 12,
      "companies_represented": 8,
      "departments_covered": 5
    }
  }
}
```

### Statistics & Analytics

#### GET /api/v1/stats/overview
Get system-wide statistics.

**Response:**
```json
{
  "total_resumes": 1542,
  "resumes_processed_today": 23,
  "active_searches": 156,
  "top_skills": [
    {"skill": "Python", "count": 892},
    {"skill": "JavaScript", "count": 743}
  ],
  "top_companies": [
    {"company": "Tech Corp", "count": 45},
    {"company": "StartupXYZ", "count": 38}
  ],
  "processing_stats": {
    "average_processing_time": 28.5,
    "success_rate": 0.97,
    "queue_length": 5
  }
}
```

## 📝 Request/Response Schemas

### Error Response Schema
All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "timestamp": "2024-01-20T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Pagination Schema
```json
{
  "page": 1,
  "limit": 20,
  "total": 100,
  "pages": 5,
  "has_next": true,
  "has_prev": false
}
```

### Resume Schema
```json
{
  "id": "string (UUID)",
  "candidate": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "linkedin": "string (URL)",
    "github": "string (URL)"
  },
  "work_experience": [
    {
      "company": "string",
      "position": "string",
      "department": "string",
      "desk": "string",
      "start_date": "string (ISO 8601)",
      "end_date": "string (ISO 8601) or null",
      "is_current": "boolean",
      "description": "string",
      "achievements": ["string"]
    }
  ],
  "skills": [
    {
      "name": "string",
      "category": "string",
      "proficiency": "string (Beginner|Intermediate|Advanced|Expert)",
      "years_experience": "number"
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field_of_study": "string",
      "graduation_date": "string (ISO 8601)",
      "gpa": "number (optional)"
    }
  ],
  "certifications": [
    {
      "name": "string",
      "issuer": "string",
      "issue_date": "string (ISO 8601)",
      "expiry_date": "string (ISO 8601) or null"
    }
  ],
  "languages": [
    {
      "language": "string",
      "proficiency": "string (Basic|Conversational|Professional|Native)"
    }
  ],
  "metadata": {
    "original_format": "string (pdf|doc|docx)",
    "parsed_at": "string (ISO 8601)",
    "last_updated": "string (ISO 8601)",
    "processing_version": "string",
    "confidence_score": "number (0-1)"
  }
}
```

## 🔒 Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Authentication endpoints**: 5 requests per minute
- **Upload endpoint**: 10 requests per minute
- **Search endpoints**: 30 requests per minute
- **Other endpoints**: 60 requests per minute

Rate limit information is included in response headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642680000
```

## 🚨 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| AUTH_INVALID_CREDENTIALS | 401 | Invalid email or password |
| AUTH_TOKEN_EXPIRED | 401 | JWT token has expired |
| AUTH_TOKEN_INVALID | 401 | Invalid JWT token |
| AUTH_INSUFFICIENT_PERMISSIONS | 403 | User lacks required permissions |
| RESOURCE_NOT_FOUND | 404 | Requested resource not found |
| VALIDATION_ERROR | 422 | Request validation failed |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| FILE_TOO_LARGE | 413 | Uploaded file exceeds size limit |
| FILE_FORMAT_INVALID | 400 | Unsupported file format |
| PROCESSING_FAILED | 500 | Resume processing failed |
| DATABASE_ERROR | 500 | Database operation failed |
| EXTERNAL_SERVICE_ERROR | 502 | External service (Claude API) error |

## 🔄 Webhooks

Configure webhooks to receive notifications about resume processing events.

### Webhook Events
- `resume.processing.started`: Processing has begun
- `resume.processing.completed`: Processing finished successfully
- `resume.processing.failed`: Processing failed
- `resume.updated`: Resume data was updated
- `search.completed`: Search operation completed

### Webhook Payload
```json
{
  "event": "resume.processing.completed",
  "timestamp": "2024-01-20T10:30:00Z",
  "data": {
    "resume_id": "550e8400-e29b-41d4-a716-446655440000",
    "processing_id": "proc_123456",
    "status": "completed",
    "duration_seconds": 25
  }
}
```

## 🧪 Testing the API

### Using cURL
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Upload resume
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"

# Search resumes
curl -X GET "http://localhost:8000/api/v1/resumes/search?q=python&skills[]=Python" \
  -H "Authorization: Bearer <token>"
```

### Using Python
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "test@example.com", "password": "password123"}
)
token = response.json()["access_token"]

# Upload resume
with open("resume.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/resumes/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": f}
    )

# Search resumes
response = requests.get(
    "http://localhost:8000/api/v1/resumes/search",
    headers={"Authorization": f"Bearer {token}"},
    params={"q": "python developer", "skills": ["Python", "FastAPI"]}
)
```

## 📊 MCP Integration

The API integrates with MCP (Model Context Protocol) server for intelligent search capabilities.

### MCP Tools Available

#### similar_candidates
Find candidates with similar backgrounds and experience.

```json
{
  "tool": "similar_candidates",
  "parameters": {
    "reference_id": "550e8400-e29b-41d4-a716-446655440000",
    "threshold": 0.7,
    "limit": 10
  }
}
```

#### department_colleagues
Find candidates from the same department or desk.

```json
{
  "tool": "department_colleagues",
  "parameters": {
    "department": "Engineering",
    "desk": "Platform Team",
    "company": "Tech Corp",
    "date_range": {
      "start": "2020-01-01",
      "end": "2023-12-31"
    }
  }
}
```

#### professional_network
Discover professional connections and networks.

```json
{
  "tool": "professional_network",
  "parameters": {
    "candidate_id": "550e8400-e29b-41d4-a716-446655440000",
    "depth": 2,
    "min_overlap_months": 6
  }
}
```

#### skills_matching
Advanced skills-based matching with weighting.

```json
{
  "tool": "skills_matching",
  "parameters": {
    "required_skills": ["Python", "FastAPI"],
    "preferred_skills": ["Docker", "Kubernetes"],
    "weights": {
      "required": 0.7,
      "preferred": 0.3
    }
  }
}
```

## 🔐 Security Considerations

1. **Authentication**: All endpoints except health checks require JWT authentication
2. **Input Validation**: All inputs are validated and sanitized
3. **SQL Injection**: Protected through parameterized queries and ORM
4. **File Upload**: Files are scanned and validated before processing
5. **Rate Limiting**: Prevents abuse and ensures fair usage
6. **CORS**: Configured for allowed origins only
7. **Secrets**: All sensitive data stored in environment variables
8. **HTTPS**: Required for production deployments
9. **Audit Logging**: All API access is logged for security monitoring