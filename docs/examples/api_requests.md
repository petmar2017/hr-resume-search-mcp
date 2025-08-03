# API Request Examples

**HR Resume Search API - Practical Request/Response Examples**

## Table of Contents

- [Authentication Examples](#authentication-examples)
- [Search Examples](#search-examples)
- [Resume Management Examples](#resume-management-examples)
- [Project Management Examples](#project-management-examples)
- [Error Handling Examples](#error-handling-examples)

---

## Authentication Examples

### Login Request

**POST** `/api/v1/auth/login`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "hr@company.com",
    "password": "secure_password123"
  }'
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "hr@company.com",
    "is_active": true,
    "roles": ["hr_manager"],
    "scopes": ["search:candidates", "upload:resumes", "view:analytics"]
  }
}
```

### Using Authentication Token

```bash
# Set token variable
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Use in subsequent requests
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### Refresh Token

**POST** `/api/v1/auth/refresh`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

---

## Search Examples

### 1. Skills-Based Search

**POST** `/api/v1/search/candidates`

```bash
curl -X POST "http://localhost:8000/api/v1/search/candidates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "skills_match",
    "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
    "min_experience_years": 3,
    "max_experience_years": 10,
    "limit": 10,
    "offset": 0
  }'
```

**Response** (200 OK):
```json
{
  "query": "",
  "search_type": "skills_match",
  "total_results": 23,
  "results": [
    {
      "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
      "resume_id": "987fcdeb-51a2-43d7-9c4f-123456789abc",
      "full_name": "Sarah Chen",
      "current_position": "Senior Software Engineer",
      "current_company": "TechCorp Inc",
      "total_experience_years": 6,
      "match_score": 0.92,
      "match_reasons": [
        "Skills: Python, FastAPI, PostgreSQL",
        "Experience matches requirement"
      ],
      "highlights": {
        "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
        "location": "San Francisco, CA",
        "headline": "Full-stack developer with cloud expertise"
      }
    },
    {
      "candidate_id": "456e7890-e89b-12d3-a456-426614174001",
      "resume_id": "654fcdeb-51a2-43d7-9c4f-123456789def",
      "full_name": "Mike Rodriguez",
      "current_position": "Backend Developer",
      "current_company": "StartupX",
      "total_experience_years": 4,
      "match_score": 0.85,
      "match_reasons": [
        "Skills: Python, AWS",
        "Experience matches requirement"
      ],
      "highlights": {
        "skills": ["Python", "Django", "AWS", "Redis"],
        "location": "Remote",
        "headline": "Backend specialist with startup experience"
      }
    }
  ],
  "processing_time_ms": 287
}
```

### 2. Department-Based Search

**POST** `/api/v1/search/candidates`

```bash
curl -X POST "http://localhost:8000/api/v1/search/candidates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "same_department",
    "departments": ["Engineering", "Data Science"],
    "companies": ["Google", "Meta", "Amazon"],
    "limit": 15
  }'
```

**Response** (200 OK):
```json
{
  "query": "",
  "search_type": "same_department",
  "total_results": 42,
  "results": [
    {
      "candidate_id": "789e1234-e89b-12d3-a456-426614174002",
      "resume_id": "321fcdeb-51a2-43d7-9c4f-123456789ghi",
      "full_name": "Alex Kim",
      "current_position": "Data Scientist",
      "current_company": "Meta",
      "total_experience_years": 5,
      "match_score": 0.88,
      "match_reasons": [
        "Worked in Data Science",
        "Worked at Meta"
      ],
      "highlights": {
        "skills": ["Python", "Machine Learning", "SQL", "Spark"],
        "location": "Menlo Park, CA",
        "headline": "ML engineer with production experience"
      }
    }
  ],
  "processing_time_ms": 156
}
```

### 3. Similar Candidates Search

**POST** `/api/v1/search/similar`

```bash
curl -X POST "http://localhost:8000/api/v1/search/similar" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
    "limit": 5
  }'
```

**Response** (200 OK):
```json
{
  "query": "Similar to Sarah Chen",
  "search_type": "similar_candidates",
  "total_results": 5,
  "results": [
    {
      "candidate_id": "999e1111-e89b-12d3-a456-426614174003",
      "resume_id": "111fcdeb-51a2-43d7-9c4f-123456789jkl",
      "full_name": "David Park",
      "current_position": "Senior Full Stack Developer",
      "current_company": "TechStartup",
      "total_experience_years": 7,
      "match_score": 0.89,
      "match_reasons": [
        "Common skills: Python, FastAPI, AWS",
        "Similar experience: 7 years"
      ],
      "highlights": {
        "skills": ["Python", "React", "FastAPI", "AWS", "MongoDB"],
        "location": "Seattle, WA",
        "headline": "Full-stack engineer with DevOps skills"
      }
    }
  ],
  "processing_time_ms": 203
}
```

### 4. Colleagues Search

**POST** `/api/v1/search/colleagues`

```bash
curl -X POST "http://localhost:8000/api/v1/search/colleagues" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
    "limit": 10
  }'
```

**Response** (200 OK):
```json
{
  "query": "Colleagues of Sarah Chen",
  "search_type": "worked_with",
  "total_results": 7,
  "results": [
    {
      "candidate_id": "222e3333-e89b-12d3-a456-426614174004",
      "resume_id": "444fcdeb-51a2-43d7-9c4f-123456789mno",
      "full_name": "Lisa Wang",
      "current_position": "Engineering Manager",
      "current_company": "DataFlow Inc",
      "total_experience_years": 8,
      "match_score": 0.75,
      "match_reasons": [
        "Worked together at TechCorp Inc",
        "Overlap: 18 months",
        "Same department: Engineering"
      ],
      "highlights": {
        "company": "TechCorp Inc",
        "department": "Engineering",
        "overlap_months": 18,
        "positions": {
          "original": "Senior Software Engineer",
          "colleague": "Tech Lead"
        }
      }
    }
  ],
  "processing_time_ms": 145
}
```

### 5. Smart Natural Language Search

**POST** `/api/v1/search/smart`

```bash
curl -X POST "http://localhost:8000/api/v1/search/smart" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find senior Python developers who have worked at startups and know machine learning",
    "limit": 10,
    "include_reasoning": true
  }'
```

**Response** (200 OK):
```json
{
  "interpreted_query": {
    "original_query": "Find senior Python developers who have worked at startups and know machine learning",
    "detected_intent": "skills_match",
    "extracted_criteria": {
      "skills": ["python", "machine learning"],
      "min_experience_years": 5
    }
  },
  "results": [
    {
      "candidate_id": "555e6666-e89b-12d3-a456-426614174005",
      "resume_id": "777fcdeb-51a2-43d7-9c4f-123456789pqr",
      "full_name": "Emma Thompson",
      "current_position": "Senior ML Engineer",
      "current_company": "AI Startup Inc",
      "total_experience_years": 7,
      "match_score": 0.94,
      "match_reasons": [
        "Skills: Python, Machine Learning",
        "Experience matches requirement"
      ],
      "highlights": {
        "skills": ["Python", "TensorFlow", "PyTorch", "Scikit-learn"],
        "location": "Austin, TX",
        "headline": "ML engineer with startup and enterprise experience"
      }
    }
  ],
  "reasoning": "I interpreted your query as looking for skills match. I detected these skills: python, machine learning. I found you're looking for candidates with at least 5 years of experience. I found 12 matching candidates.",
  "suggested_queries": [
    "Show me senior python developers",
    "Find candidates who worked at top tech companies",
    "Show me candidates with leadership experience"
  ],
  "processing_time_ms": 892,
  "success": true
}
```

### 6. Search Filters

**GET** `/api/v1/search/filters`

```bash
curl -X GET "http://localhost:8000/api/v1/search/filters" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "companies": [
    {"name": "Google", "count": 45},
    {"name": "Meta", "count": 32},
    {"name": "Amazon", "count": 67},
    {"name": "Microsoft", "count": 28}
  ],
  "departments": [
    {"name": "Engineering", "count": 156},
    {"name": "Data Science", "count": 43},
    {"name": "Product", "count": 28},
    {"name": "Design", "count": 19}
  ],
  "locations": [
    {"name": "San Francisco, CA", "count": 89},
    {"name": "Seattle, WA", "count": 54},
    {"name": "New York, NY", "count": 67},
    {"name": "Remote", "count": 123}
  ],
  "skills": [
    {"name": "Python", "count": 234},
    {"name": "JavaScript", "count": 189},
    {"name": "React", "count": 156},
    {"name": "AWS", "count": 167},
    {"name": "SQL", "count": 201}
  ],
  "experience_range": {
    "min": 0,
    "max": 25,
    "average": 6.8
  },
  "education_levels": [
    {"value": "high_school", "label": "High School"},
    {"value": "bachelors", "label": "Bachelor's Degree"},
    {"value": "masters", "label": "Master's Degree"},
    {"value": "phd", "label": "PhD"},
    {"value": "other", "label": "Other"}
  ],
  "search_types": [
    {"value": "similar_candidates", "label": "Similar Candidates"},
    {"value": "same_department", "label": "Same Department/Desk"},
    {"value": "worked_with", "label": "Worked Together"},
    {"value": "skills_match", "label": "Skills Match"},
    {"value": "experience_match", "label": "Experience Match"}
  ],
  "statistics": {
    "total_candidates": 1547,
    "total_resumes": 1423,
    "last_updated": "2025-08-03T10:30:00.000Z"
  }
}
```

---

## Resume Management Examples

### 1. Upload Resume

**POST** `/api/v1/resumes/upload`

```bash
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/resume.pdf" \
  -F "candidate_name=John Doe" \
  -F "email=john.doe@email.com"
```

**Response** (200 OK):
```json
{
  "message": "Resume uploaded successfully",
  "resume_id": "abc12345-def6-7890-abcd-123456789xyz",
  "candidate_id": "candidate_987654321",
  "status": "processing",
  "estimated_processing_time": "2-5 minutes",
  "file_info": {
    "filename": "resume.pdf",
    "size_bytes": 245760,
    "content_type": "application/pdf"
  }
}
```

### 2. Check Resume Processing Status

**GET** `/api/v1/resumes/{resume_id}/status`

```bash
curl -X GET "http://localhost:8000/api/v1/resumes/abc12345-def6-7890-abcd-123456789xyz/status" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "resume_id": "abc12345-def6-7890-abcd-123456789xyz",
  "status": "completed",
  "progress": 100,
  "processing_stages": {
    "file_upload": "completed",
    "text_extraction": "completed",
    "claude_parsing": "completed",
    "data_validation": "completed",
    "database_storage": "completed"
  },
  "processed_at": "2025-08-03T10:35:00.000Z",
  "processing_time_seconds": 87,
  "extracted_data": {
    "candidate_name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "+1-555-0123",
    "skills_count": 12,
    "experience_years": 5,
    "education_count": 2,
    "work_experience_count": 3
  }
}
```

### 3. Get Resume Details

**GET** `/api/v1/resumes/{resume_id}`

```bash
curl -X GET "http://localhost:8000/api/v1/resumes/abc12345-def6-7890-abcd-123456789xyz" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "resume_id": "abc12345-def6-7890-abcd-123456789xyz",
  "candidate_id": "candidate_987654321",
  "filename": "resume.pdf",
  "upload_date": "2025-08-03T10:30:00.000Z",
  "parsing_status": "completed",
  "parsed_data": {
    "personal_info": {
      "name": "John Doe",
      "email": "john.doe@email.com",
      "phone": "+1-555-0123",
      "location": "San Francisco, CA",
      "linkedin": "https://linkedin.com/in/johndoe"
    },
    "skills": [
      "Python", "JavaScript", "React", "Node.js", "PostgreSQL",
      "AWS", "Docker", "Git", "Agile", "REST APIs", "GraphQL", "Redis"
    ],
    "experience": [
      {
        "company": "TechCorp Inc",
        "position": "Software Engineer",
        "start_date": "2020-01-15",
        "end_date": "2023-06-30",
        "duration_months": 42,
        "description": "Developed web applications using React and Node.js, managed AWS infrastructure"
      },
      {
        "company": "StartupX",
        "position": "Junior Developer",
        "start_date": "2018-07-01",
        "end_date": "2019-12-31",
        "duration_months": 18,
        "description": "Built backend APIs using Python and Flask, worked with PostgreSQL databases"
      }
    ],
    "education": [
      {
        "institution": "UC Berkeley",
        "degree": "Bachelor of Science",
        "field": "Computer Science",
        "graduation_year": 2018,
        "gpa": 3.7
      }
    ],
    "certifications": [
      {
        "name": "AWS Certified Developer",
        "issuer": "Amazon Web Services",
        "date": "2022-03-15",
        "credential_id": "AWS-DEV-12345"
      }
    ]
  },
  "processing_metadata": {
    "claude_model": "claude-3-5-sonnet-20241022",
    "processing_time_ms": 87234,
    "confidence_score": 0.94,
    "validation_errors": []
  }
}
```

---

## Project Management Examples

### 1. Create New Project

**POST** `/api/v1/projects`

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mobile App Backend",
    "description": "REST API for iOS and Android mobile application",
    "database_type": "postgresql",
    "authentication": true,
    "features": ["user_management", "file_upload", "search", "analytics"]
  }'
```

**Response** (201 Created):
```json
{
  "project_id": "proj_123456789",
  "name": "Mobile App Backend",
  "description": "REST API for iOS and Android mobile application",
  "database_type": "postgresql",
  "authentication": true,
  "features": ["user_management", "file_upload", "search", "analytics"],
  "created_at": "2025-08-03T10:30:00.000Z",
  "status": "active",
  "endpoints_count": 0,
  "owner": {
    "user_id": 1,
    "email": "developer@company.com"
  }
}
```

### 2. Create Project Endpoint

**POST** `/api/v1/endpoints`

```bash
curl -X POST "http://localhost:8000/api/v1/endpoints" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123456789",
    "path": "/api/v1/users",
    "method": "GET",
    "description": "Get list of users",
    "request_schema": {
      "type": "object",
      "properties": {
        "limit": {"type": "integer", "default": 10},
        "offset": {"type": "integer", "default": 0}
      }
    },
    "response_schema": {
      "type": "object",
      "properties": {
        "users": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": {"type": "integer"},
              "email": {"type": "string"},
              "name": {"type": "string"}
            }
          }
        },
        "total": {"type": "integer"}
      }
    }
  }'
```

**Response** (201 Created):
```json
{
  "endpoint_id": "endpoint_987654321",
  "project_id": "proj_123456789",
  "path": "/api/v1/users",
  "method": "GET",
  "description": "Get list of users",
  "request_schema": {
    "type": "object",
    "properties": {
      "limit": {"type": "integer", "default": 10},
      "offset": {"type": "integer", "default": 0}
    }
  },
  "response_schema": {
    "type": "object",
    "properties": {
      "users": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {"type": "integer"},
            "email": {"type": "string"},
            "name": {"type": "string"}
          }
        }
      },
      "total": {"type": "integer"}
    }
  },
  "created_at": "2025-08-03T10:35:00.000Z",
  "is_active": true
}
```

---

## Error Handling Examples

### 1. Authentication Error

**Request without token**:
```bash
curl -X GET "http://localhost:8000/api/v1/search/filters"
```

**Response** (401 Unauthorized):
```json
{
  "error": {
    "type": "authentication_error",
    "status_code": 401,
    "message": "Could not validate credentials",
    "timestamp": "2025-08-03T10:30:00.000Z"
  }
}
```

### 2. Invalid Token Error

**Request with expired token**:
```bash
curl -X GET "http://localhost:8000/api/v1/search/filters" \
  -H "Authorization: Bearer expired_token_here"
```

**Response** (401 Unauthorized):
```json
{
  "error": {
    "type": "authentication_error",
    "status_code": 401,
    "message": "Token has expired",
    "timestamp": "2025-08-03T10:30:00.000Z"
  }
}
```

### 3. Validation Error

**Invalid search request**:
```bash
curl -X POST "http://localhost:8000/api/v1/search/candidates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "invalid_type",
    "limit": -5
  }'
```

**Response** (422 Unprocessable Entity):
```json
{
  "error": {
    "type": "validation_error",
    "message": "Request validation failed",
    "details": [
      {
        "type": "value_error",
        "loc": ["body", "search_type"],
        "msg": "value is not a valid enumeration member; permitted: 'skills_match', 'same_department', 'worked_with', 'similar_candidates', 'experience_match'",
        "input": "invalid_type"
      },
      {
        "type": "value_error",
        "loc": ["body", "limit"],
        "msg": "ensure this value is greater than 0",
        "input": -5
      }
    ],
    "timestamp": "2025-08-03T10:30:00.000Z"
  }
}
```

### 4. Rate Limit Error

**Too many requests**:
```bash
# After exceeding rate limit
curl -X POST "http://localhost:8000/api/v1/search/candidates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_type": "skills_match", "skills": ["Python"]}'
```

**Response** (429 Too Many Requests):
```json
{
  "error": {
    "type": "rate_limit_exceeded",
    "status_code": 429,
    "message": "Rate limit exceeded: 100 requests per minute",
    "timestamp": "2025-08-03T10:30:00.000Z",
    "retry_after": 45
  }
}
```

### 5. Resource Not Found

**Non-existent candidate**:
```bash
curl -X POST "http://localhost:8000/api/v1/search/similar" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "non-existent-id-12345",
    "limit": 5
  }'
```

**Response** (404 Not Found):
```json
{
  "error": {
    "type": "http_exception",
    "status_code": 404,
    "message": "Candidate not found",
    "timestamp": "2025-08-03T10:30:00.000Z"
  }
}
```

### 6. Server Error

**Internal server error**:
```bash
# During system maintenance or database issues
curl -X POST "http://localhost:8000/api/v1/search/candidates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_type": "skills_match", "skills": ["Python"]}'
```

**Response** (500 Internal Server Error):
```json
{
  "error": {
    "type": "internal_server_error",
    "message": "An unexpected error occurred",
    "timestamp": "2025-08-03T10:30:00.000Z",
    "details": "Contact support for assistance"
  }
}
```

---

## Batch Operations Examples

### Multiple Searches in Parallel

```bash
#!/bin/bash

TOKEN="your_auth_token_here"

# Function to perform search
search_candidates() {
    local query="$1"
    local skills="$2"
    
    curl -s -X POST "http://localhost:8000/api/v1/search/candidates" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"search_type\": \"skills_match\",
        \"skills\": $skills,
        \"limit\": 5
      }"
}

# Parallel searches
search_candidates "Python developers" '["Python", "FastAPI"]' &
search_candidates "Frontend developers" '["React", "TypeScript"]' &
search_candidates "Data scientists" '["Python", "Machine Learning"]' &

# Wait for all background jobs to complete
wait

echo "All searches completed!"
```

### Pagination Example

```bash
#!/bin/bash

TOKEN="your_auth_token_here"
LIMIT=10
OFFSET=0
TOTAL_COLLECTED=0

while true; do
    echo "Fetching candidates from offset $OFFSET..."
    
    RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/search/candidates" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"search_type\": \"skills_match\",
        \"skills\": [\"Python\"],
        \"limit\": $LIMIT,
        \"offset\": $OFFSET
      }")
    
    # Extract total_results and current batch size
    TOTAL_RESULTS=$(echo "$RESPONSE" | jq -r '.total_results')
    BATCH_SIZE=$(echo "$RESPONSE" | jq -r '.results | length')
    
    echo "Got $BATCH_SIZE candidates (Total available: $TOTAL_RESULTS)"
    
    # Process candidates in this batch
    echo "$RESPONSE" | jq -r '.results[] | "\(.full_name) - \(.current_position) at \(.current_company)"'
    
    TOTAL_COLLECTED=$((TOTAL_COLLECTED + BATCH_SIZE))
    OFFSET=$((OFFSET + LIMIT))
    
    # Break if we've collected all results or no results in this batch
    if [ "$BATCH_SIZE" -lt "$LIMIT" ] || [ "$TOTAL_COLLECTED" -ge "$TOTAL_RESULTS" ]; then
        break
    fi
    
    # Small delay to avoid rate limiting
    sleep 1
done

echo "Collected $TOTAL_COLLECTED candidates total"
```

---

## Python Integration Example

```python
import requests
import asyncio
import aiohttp
from typing import List, Dict, Any

class HRResumeAPIClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
        self.auth_token = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate and store token"""
        async with self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data["access_token"]
                return data
            else:
                raise Exception(f"Authentication failed: {response.status}")
    
    async def search_candidates(
        self, 
        search_type: str = "skills_match",
        skills: List[str] = None,
        query: str = "",
        min_experience: int = None,
        companies: List[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for candidates"""
        payload = {
            "search_type": search_type,
            "query": query,
            "limit": limit
        }
        
        if skills:
            payload["skills"] = skills
        if min_experience:
            payload["min_experience_years"] = min_experience
        if companies:
            payload["companies"] = companies
        
        async with self.session.post(
            f"{self.base_url}/api/v1/search/candidates",
            json=payload,
            headers=self._get_headers()
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Search failed: {response.status} - {error_text}")
    
    async def find_similar_candidates(self, candidate_id: str, limit: int = 5) -> Dict[str, Any]:
        """Find similar candidates"""
        async with self.session.post(
            f"{self.base_url}/api/v1/search/similar",
            json={"candidate_id": candidate_id, "limit": limit},
            headers=self._get_headers()
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Similar search failed: {response.status} - {error_text}")

# Usage example
async def main():
    async with HRResumeAPIClient("http://localhost:8000") as client:
        # Login
        auth_data = await client.login("hr@company.com", "password")
        print(f"Logged in as: {auth_data['user']['email']}")
        
        # Search for Python developers
        results = await client.search_candidates(
            skills=["Python", "FastAPI", "PostgreSQL"],
            min_experience=3,
            limit=5
        )
        
        print(f"Found {results['total_results']} candidates:")
        for candidate in results['results']:
            print(f"- {candidate['full_name']}: {candidate['match_score']:.2f}")
            
            # Find similar candidates for the first result
            if candidate == results['results'][0]:
                similar = await client.find_similar_candidates(
                    candidate['candidate_id'], 
                    limit=3
                )
                print(f"  Similar candidates: {len(similar['results'])}")
                for sim in similar['results']:
                    print(f"    - {sim['full_name']}: {sim['match_score']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Performance Testing Examples

### Load Testing Script

```bash
#!/bin/bash

# Load testing with Apache Bench (ab)
TOKEN="your_auth_token_here"

# Create payload file
cat > search_payload.json << EOF
{
  "search_type": "skills_match",
  "skills": ["Python", "JavaScript"],
  "limit": 10
}
EOF

echo "Starting load test..."

# Test with different concurrency levels
for concurrency in 1 5 10 20 50; do
    echo "Testing with $concurrency concurrent requests..."
    
    ab -n 100 -c $concurrency \
       -H "Authorization: Bearer $TOKEN" \
       -H "Content-Type: application/json" \
       -p search_payload.json \
       -T "application/json" \
       http://localhost:8000/api/v1/search/candidates
    
    echo "Waiting 10 seconds before next test..."
    sleep 10
done

echo "Load testing completed!"
rm search_payload.json
```

This comprehensive set of examples covers all major API functionality with practical request/response patterns, error handling, and integration examples. Users can copy and modify these examples for their specific use cases.