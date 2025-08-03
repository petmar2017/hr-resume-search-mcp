# Integration Examples

**HR Resume Search API - Real-World Integration Patterns**

## Table of Contents

- [React Frontend Integration](#react-frontend-integration)
- [Python Backend Integration](#python-backend-integration)
- [Microservices Integration](#microservices-integration)
- [Webhook & Event Integration](#webhook--event-integration)
- [Monitoring & Analytics](#monitoring--analytics)
- [Third-Party Integrations](#third-party-integrations)

---

## React Frontend Integration

### Complete React Application Example

```jsx
// src/components/CandidateSearch.jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  Alert,
  Autocomplete,
  Pagination
} from '@mui/material';
import { Search, Person, Business, Star } from '@mui/icons-material';

// API Service
class HRResumeAPIService {
  constructor(baseURL = 'http://localhost:8000', authToken = null) {
    this.baseURL = baseURL;
    this.authToken = authToken;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.authToken && { Authorization: `Bearer ${this.authToken}` })
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'API request failed');
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  async searchCandidates(searchParams) {
    return this.request('/api/v1/search/candidates', {
      method: 'POST',
      body: JSON.stringify(searchParams)
    });
  }

  async getSearchFilters() {
    return this.request('/api/v1/search/filters');
  }

  async findSimilarCandidates(candidateId, limit = 5) {
    return this.request('/api/v1/search/similar', {
      method: 'POST',
      body: JSON.stringify({ candidate_id: candidateId, limit })
    });
  }

  async smartSearch(query, options = {}) {
    return this.request('/api/v1/search/smart', {
      method: 'POST',
      body: JSON.stringify({ query, ...options })
    });
  }
}

// Main Search Component
const CandidateSearch = ({ authToken }) => {
  // State management
  const [searchParams, setSearchParams] = useState({
    search_type: 'skills_match',
    skills: [],
    companies: [],
    departments: [],
    locations: [],
    min_experience_years: '',
    max_experience_years: '',
    education_level: '',
    query: '',
    limit: 10,
    offset: 0
  });

  const [searchResults, setSearchResults] = useState([]);
  const [totalResults, setTotalResults] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [similarCandidates, setSimilarCandidates] = useState([]);

  // API service instance
  const apiService = new HRResumeAPIService('http://localhost:8000', authToken);

  // Load available filters on component mount
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const filtersData = await apiService.getSearchFilters();
        setFilters(filtersData);
      } catch (err) {
        console.error('Failed to load filters:', err);
      }
    };

    loadFilters();
  }, []);

  // Search function
  const performSearch = useCallback(async (params = searchParams) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.searchCandidates(params);
      setSearchResults(response.results);
      setTotalResults(response.total_results);
      setCurrentPage(Math.floor(params.offset / params.limit) + 1);
    } catch (err) {
      setError(err.message);
      setSearchResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  // Smart search function
  const performSmartSearch = async (query) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.smartSearch(query, {
        limit: searchParams.limit,
        include_reasoning: true
      });

      setSearchResults(response.candidates);
      setTotalResults(response.candidates.length);
      
      if (response.reasoning) {
        console.log('AI Reasoning:', response.reasoning);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Find similar candidates
  const findSimilar = async (candidateId) => {
    try {
      const response = await apiService.findSimilarCandidates(candidateId, 5);
      setSimilarCandidates(response.candidates);
      setSelectedCandidate(candidateId);
    } catch (err) {
      console.error('Failed to find similar candidates:', err);
    }
  };

  // Handle pagination
  const handlePageChange = (event, page) => {
    const newOffset = (page - 1) * searchParams.limit;
    const newParams = { ...searchParams, offset: newOffset };
    setSearchParams(newParams);
    performSearch(newParams);
  };

  // Handle form submission
  const handleSearch = (event) => {
    event.preventDefault();
    const searchParamsWithReset = { ...searchParams, offset: 0 };
    setSearchParams(searchParamsWithReset);
    performSearch(searchParamsWithReset);
  };

  // Handle smart search
  const handleSmartSearch = (event) => {
    event.preventDefault();
    if (searchParams.query.trim()) {
      performSmartSearch(searchParams.query);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        HR Resume Search
      </Typography>

      {/* Search Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <form onSubmit={handleSearch}>
            <Grid container spacing={3}>
              {/* Smart Search */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <TextField
                    fullWidth
                    label="Smart Search (Natural Language)"
                    placeholder="Find senior Python developers with startup experience"
                    value={searchParams.query}
                    onChange={(e) => setSearchParams(prev => ({ 
                      ...prev, 
                      query: e.target.value 
                    }))}
                  />
                  <Button
                    variant="outlined"
                    onClick={handleSmartSearch}
                    disabled={loading || !searchParams.query.trim()}
                    startIcon={<Search />}
                  >
                    Smart Search
                  </Button>
                </Box>
              </Grid>

              {/* Search Type */}
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Search Type</InputLabel>
                  <Select
                    value={searchParams.search_type}
                    onChange={(e) => setSearchParams(prev => ({
                      ...prev,
                      search_type: e.target.value
                    }))}
                  >
                    <MenuItem value="skills_match">Skills Match</MenuItem>
                    <MenuItem value="same_department">Same Department</MenuItem>
                    <MenuItem value="worked_with">Worked Together</MenuItem>
                    <MenuItem value="similar_candidates">Similar Candidates</MenuItem>
                    <MenuItem value="experience_match">Experience Match</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Skills Selection */}
              <Grid item xs={12} md={6}>
                <Autocomplete
                  multiple
                  options={filters.skills?.map(skill => skill.name) || []}
                  value={searchParams.skills}
                  onChange={(event, newValue) => {
                    setSearchParams(prev => ({ ...prev, skills: newValue }));
                  }}
                  renderInput={(params) => (
                    <TextField {...params} label="Skills" placeholder="Select skills" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={option}
                        {...getTagProps({ index })}
                        key={option}
                      />
                    ))
                  }
                />
              </Grid>

              {/* Companies */}
              <Grid item xs={12} md={6}>
                <Autocomplete
                  multiple
                  options={filters.companies?.map(company => company.name) || []}
                  value={searchParams.companies}
                  onChange={(event, newValue) => {
                    setSearchParams(prev => ({ ...prev, companies: newValue }));
                  }}
                  renderInput={(params) => (
                    <TextField {...params} label="Companies" placeholder="Select companies" />
                  )}
                />
              </Grid>

              {/* Experience Range */}
              <Grid item xs={6} md={3}>
                <TextField
                  fullWidth
                  label="Min Experience (years)"
                  type="number"
                  value={searchParams.min_experience_years}
                  onChange={(e) => setSearchParams(prev => ({
                    ...prev,
                    min_experience_years: e.target.value
                  }))}
                />
              </Grid>

              <Grid item xs={6} md={3}>
                <TextField
                  fullWidth
                  label="Max Experience (years)"
                  type="number"
                  value={searchParams.max_experience_years}
                  onChange={(e) => setSearchParams(prev => ({
                    ...prev,
                    max_experience_years: e.target.value
                  }))}
                />
              </Grid>

              {/* Search Button */}
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <Search />}
                  size="large"
                >
                  {loading ? 'Searching...' : 'Search Candidates'}
                </Button>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results Summary */}
      {totalResults > 0 && (
        <Typography variant="h6" gutterBottom>
          Found {totalResults} candidates
        </Typography>
      )}

      {/* Search Results */}
      <Grid container spacing={3}>
        {searchResults.map((candidate) => (
          <Grid item xs={12} md={6} lg={4} key={candidate.candidate_id}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Person sx={{ mr: 1 }} />
                  <Typography variant="h6" component="div">
                    {candidate.full_name}
                  </Typography>
                  <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
                    <Star sx={{ color: 'gold', fontSize: 16, mr: 0.5 }} />
                    <Typography variant="body2">
                      {(candidate.match_score * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </Box>

                <Typography color="text.secondary" gutterBottom>
                  {candidate.current_position}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Business sx={{ fontSize: 16, mr: 1 }} />
                  <Typography variant="body2">
                    {candidate.current_company}
                  </Typography>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {candidate.total_experience_years} years experience
                </Typography>

                {/* Skills */}
                <Box sx={{ mb: 2 }}>
                  {candidate.highlights?.skills?.slice(0, 4).map((skill) => (
                    <Chip
                      key={skill}
                      label={skill}
                      size="small"
                      variant="outlined"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>

                {/* Match Reasons */}
                {candidate.match_reasons && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="primary" gutterBottom>
                      Match Reasons:
                    </Typography>
                    {candidate.match_reasons.map((reason, index) => (
                      <Typography key={index} variant="body2" sx={{ fontSize: '0.8rem' }}>
                        • {reason}
                      </Typography>
                    ))}
                  </Box>
                )}

                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => findSimilar(candidate.candidate_id)}
                  fullWidth
                >
                  Find Similar
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Similar Candidates Modal/Section */}
      {selectedCandidate && similarCandidates.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Similar Candidates
            </Typography>
            <Grid container spacing={2}>
              {similarCandidates.map((candidate) => (
                <Grid item xs={12} md={6} key={candidate.candidate_id}>
                  <Card variant="outlined">
                    <CardContent sx={{ p: 2 }}>
                      <Typography variant="subtitle1">
                        {candidate.full_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {candidate.current_position} at {candidate.current_company}
                      </Typography>
                      <Typography variant="body2">
                        Similarity: {(candidate.match_score * 100).toFixed(0)}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {totalResults > searchParams.limit && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={Math.ceil(totalResults / searchParams.limit)}
            page={currentPage}
            onChange={handlePageChange}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
};

export default CandidateSearch;
```

### React Hook for API Integration

```jsx
// src/hooks/useHRResumeAPI.js
import { useState, useCallback, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

export const useHRResumeAPI = () => {
  const { authToken } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiRequest = useCallback(async (endpoint, options = {}) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(authToken && { Authorization: `Bearer ${authToken}` })
        },
        ...options
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Request failed');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  const searchCandidates = useCallback((searchParams) => {
    return apiRequest('/api/v1/search/candidates', {
      method: 'POST',
      body: JSON.stringify(searchParams)
    });
  }, [apiRequest]);

  const uploadResume = useCallback(async (file, candidateInfo) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('candidate_name', candidateInfo.name);
    formData.append('email', candidateInfo.email);
    if (candidateInfo.phone) formData.append('phone', candidateInfo.phone);

    return apiRequest('/api/v1/resumes/upload', {
      method: 'POST',
      body: formData,
      headers: {
        ...(authToken && { Authorization: `Bearer ${authToken}` })
      }
    });
  }, [apiRequest, authToken]);

  return {
    loading,
    error,
    searchCandidates,
    uploadResume,
    apiRequest
  };
};
```

---

## Python Backend Integration

### FastAPI Backend Service

```python
# backend_service.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import asyncio
import logging
from datetime import datetime
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class SearchRequest(BaseModel):
    skills: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    location: Optional[str] = None
    search_type: str = "skills_match"
    limit: int = 10

class CandidateProfile(BaseModel):
    candidate_id: str
    name: str
    position: str
    company: str
    skills: List[str]
    experience_years: int
    match_score: float

class SearchResponse(BaseModel):
    candidates: List[CandidateProfile]
    total_results: int
    processing_time_ms: int
    search_id: str

# HR Resume API Client
class HRResumeAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={"X-API-Key": self.api_key}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def search_candidates(self, search_params: dict) -> dict:
        try:
            response = await self.session.post(
                f"{self.base_url}/api/v1/search/candidates",
                json=search_params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HR API request failed: {e}")
            raise HTTPException(status_code=500, detail="Search service unavailable")

# Background job processing
class SearchJobProcessor:
    def __init__(self, redis_client, hr_api_client):
        self.redis = redis_client
        self.hr_api = hr_api_client
    
    async def process_search_job(self, job_id: str, search_params: dict):
        """Process search job in background"""
        try:
            # Update job status
            await self.redis.hset(f"job:{job_id}", "status", "processing")
            
            # Perform search
            async with self.hr_api as client:
                results = await client.search_candidates(search_params)
            
            # Cache results
            await self.redis.hset(f"job:{job_id}", mapping={
                "status": "completed",
                "results": str(results),
                "completed_at": datetime.utcnow().isoformat()
            })
            
            # Set expiration (24 hours)
            await self.redis.expire(f"job:{job_id}", 86400)
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await self.redis.hset(f"job:{job_id}", mapping={
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            })

# FastAPI app
app = FastAPI(title="HR Talent Management API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
async def get_redis_client():
    redis_client = redis.from_url("redis://localhost:6379")
    try:
        yield redis_client
    finally:
        await redis_client.close()

def get_hr_api_client():
    return HRResumeAPIClient(
        base_url="http://localhost:8000",
        api_key="your_api_key_here"
    )

# Endpoints
@app.post("/search", response_model=SearchResponse)
async def search_candidates_endpoint(
    search_request: SearchRequest,
    background_tasks: BackgroundTasks,
    redis_client=Depends(get_redis_client),
    hr_api_client=Depends(get_hr_api_client)
):
    """
    Search for candidates with caching and background processing
    """
    import uuid
    search_id = str(uuid.uuid4())
    
    # Convert to API format
    search_params = {
        "search_type": search_request.search_type,
        "skills": search_request.skills,
        "companies": search_request.companies,
        "departments": search_request.departments,
        "min_experience_years": search_request.min_experience,
        "max_experience_years": search_request.max_experience,
        "limit": search_request.limit
    }
    
    # Remove None values
    search_params = {k: v for k, v in search_params.items() if v is not None}
    
    # Check cache first
    cache_key = f"search:{hash(str(sorted(search_params.items())))}"
    cached_result = await redis_client.get(cache_key)
    
    if cached_result:
        logger.info(f"Cache hit for search: {search_id}")
        import json
        return json.loads(cached_result)
    
    # Perform search
    try:
        async with hr_api_client:
            results = await hr_api_client.search_candidates(search_params)
        
        # Transform response
        candidates = [
            CandidateProfile(
                candidate_id=candidate["candidate_id"],
                name=candidate["full_name"],
                position=candidate["current_position"] or "Unknown",
                company=candidate["current_company"] or "Unknown",
                skills=candidate["highlights"]["skills"][:5],
                experience_years=candidate["total_experience_years"] or 0,
                match_score=candidate["match_score"]
            )
            for candidate in results["results"]
        ]
        
        response = SearchResponse(
            candidates=candidates,
            total_results=results["total_results"],
            processing_time_ms=results["processing_time_ms"],
            search_id=search_id
        )
        
        # Cache result (5 minutes)
        await redis_client.setex(
            cache_key,
            300,
            response.json()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.post("/search/async")
async def async_search_candidates(
    search_request: SearchRequest,
    background_tasks: BackgroundTasks,
    redis_client=Depends(get_redis_client),
    hr_api_client=Depends(get_hr_api_client)
):
    """
    Start asynchronous search job
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Store job in Redis
    await redis_client.hset(f"job:{job_id}", mapping={
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "search_params": str(search_request.dict())
    })
    
    # Start background processing
    processor = SearchJobProcessor(redis_client, hr_api_client)
    background_tasks.add_task(
        processor.process_search_job,
        job_id,
        search_request.dict(exclude_none=True)
    )
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/search/job/{job_id}")
async def get_search_job_status(
    job_id: str,
    redis_client=Depends(get_redis_client)
):
    """
    Get search job status and results
    """
    job_data = await redis_client.hgetall(f"job:{job_id}")
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert bytes to strings
    job_data = {k.decode(): v.decode() for k, v in job_data.items()}
    
    if job_data["status"] == "completed" and "results" in job_data:
        import json
        job_data["results"] = json.loads(job_data["results"])
    
    return job_data

@app.get("/candidates/{candidate_id}/similar")
async def get_similar_candidates(
    candidate_id: str,
    limit: int = 5,
    hr_api_client=Depends(get_hr_api_client)
):
    """
    Find similar candidates
    """
    try:
        async with hr_api_client:
            results = await hr_api_client.session.post(
                f"{hr_api_client.base_url}/api/v1/search/similar",
                json={"candidate_id": candidate_id, "limit": limit}
            )
            results.raise_for_status()
            return results.json()
    except httpx.HTTPError as e:
        logger.error(f"Similar candidates request failed: {e}")
        raise HTTPException(status_code=500, detail="Service unavailable")

@app.get("/analytics/search-trends")
async def get_search_trends(
    redis_client=Depends(get_redis_client)
):
    """
    Get search analytics and trends
    """
    # Implement analytics aggregation
    # This would typically pull from your analytics database
    return {
        "popular_skills": ["Python", "JavaScript", "React", "AWS"],
        "trending_companies": ["Tech Corp", "StartupX", "Innovation Labs"],
        "search_volume": {
            "today": 234,
            "this_week": 1567,
            "this_month": 6789
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## Microservices Integration

### Service Mesh Integration with Docker Compose

```yaml
# docker-compose.microservices.yml
version: '3.8'

services:
  # HR Resume API (Core)
  hr-resume-api:
    build: ./hr-resume-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/hr_resume_db
      - REDIS_URL=redis://redis:6379
      - ENABLE_METRICS=true
    depends_on:
      - postgres
      - redis
    networks:
      - hr-network

  # Talent Management Service
  talent-management:
    build: ./talent-management-service
    ports:
      - "8001:8001"
    environment:
      - HR_API_URL=http://hr-resume-api:8000
      - REDIS_URL=redis://redis:6379
    depends_on:
      - hr-resume-api
      - redis
    networks:
      - hr-network

  # Analytics Service
  analytics-service:
    build: ./analytics-service
    ports:
      - "8002:8002"
    environment:
      - HR_API_URL=http://hr-resume-api:8000
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - hr-resume-api
      - influxdb
    networks:
      - hr-network

  # Notification Service
  notification-service:
    build: ./notification-service
    ports:
      - "8003:8003"
    environment:
      - REDIS_URL=redis://redis:6379
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=587
    depends_on:
      - redis
    networks:
      - hr-network

  # API Gateway
  api-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - hr-resume-api
      - talent-management
      - analytics-service
    networks:
      - hr-network

  # Databases
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=hr_resume_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - hr-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - hr-network

  influxdb:
    image: influxdb:2.7
    environment:
      - INFLUXDB_DB=analytics
      - INFLUXDB_ADMIN_USER=admin
      - INFLUXDB_ADMIN_PASSWORD=password
    volumes:
      - influxdb_data:/var/lib/influxdb2
    networks:
      - hr-network

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - hr-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - hr-network

volumes:
  postgres_data:
  redis_data:
  influxdb_data:
  grafana_data:

networks:
  hr-network:
    driver: bridge
```

### API Gateway Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream hr_api {
        server hr-resume-api:8000;
    }

    upstream talent_service {
        server talent-management:8001;
    }

    upstream analytics_service {
        server analytics-service:8002;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;

    server {
        listen 80;
        server_name api.hr-platform.com;

        # Global rate limiting
        limit_req zone=api_limit burst=20 nodelay;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;

        # HR Resume API
        location /api/v1/ {
            proxy_pass http://hr_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
            # Health check
            location /api/v1/health {
                proxy_pass http://hr_api;
                access_log off;
            }
        }

        # Talent Management
        location /api/talent/ {
            proxy_pass http://talent_service/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Analytics
        location /api/analytics/ {
            proxy_pass http://analytics_service/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Metrics (restricted access)
        location /metrics {
            allow 10.0.0.0/8;
            allow 172.16.0.0/12;
            allow 192.168.0.0/16;
            deny all;
            proxy_pass http://hr_api;
        }
    }
}
```

---

## Webhook & Event Integration

### Event-Driven Architecture with Webhooks

```python
# webhook_service.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import httpx
import hmac
import hashlib
import json
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Event models
class ResumeUploadedEvent(BaseModel):
    event_type: str = "resume.uploaded"
    resume_id: str
    candidate_id: str
    timestamp: datetime
    data: Dict[str, Any]

class CandidateSearchedEvent(BaseModel):
    event_type: str = "candidate.searched"
    search_id: str
    user_id: str
    search_params: Dict[str, Any]
    results_count: int
    timestamp: datetime

class WebhookConfig(BaseModel):
    url: str
    secret: str
    events: List[str]
    active: bool = True

# Webhook service
class WebhookService:
    def __init__(self):
        self.webhooks: Dict[str, WebhookConfig] = {}
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def register_webhook(self, webhook_id: str, config: WebhookConfig):
        """Register a new webhook"""
        self.webhooks[webhook_id] = config
        logger.info(f"Registered webhook: {webhook_id} for events: {config.events}")
    
    def sign_payload(self, payload: str, secret: str) -> str:
        """Create HMAC signature for webhook payload"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def send_webhook(self, webhook_id: str, event: BaseModel):
        """Send webhook event to registered endpoint"""
        if webhook_id not in self.webhooks:
            logger.error(f"Webhook {webhook_id} not found")
            return False
        
        config = self.webhooks[webhook_id]
        
        if not config.active or event.event_type not in config.events:
            return False
        
        payload = event.json()
        signature = self.sign_payload(payload, config.secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event.event_type,
            "X-Webhook-Timestamp": str(int(datetime.utcnow().timestamp()))
        }
        
        try:
            response = await self.client.post(
                config.url,
                content=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook {webhook_id} delivered successfully")
                return True
            else:
                logger.error(f"Webhook {webhook_id} failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook {webhook_id} error: {e}")
            return False
    
    async def broadcast_event(self, event: BaseModel):
        """Broadcast event to all relevant webhooks"""
        tasks = []
        for webhook_id in self.webhooks:
            task = self.send_webhook(webhook_id, event)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for result in results if result is True)
            logger.info(f"Event {event.event_type} delivered to {successful}/{len(tasks)} webhooks")

# Event listeners
app = FastAPI(title="HR Events & Webhooks API")
webhook_service = WebhookService()

@app.post("/webhooks/register")
async def register_webhook(webhook_id: str, config: WebhookConfig):
    """Register a new webhook endpoint"""
    webhook_service.register_webhook(webhook_id, config)
    return {"message": f"Webhook {webhook_id} registered successfully"}

@app.post("/events/resume-uploaded")
async def handle_resume_uploaded(
    event: ResumeUploadedEvent,
    background_tasks: BackgroundTasks
):
    """Handle resume uploaded event"""
    logger.info(f"Resume uploaded event: {event.resume_id}")
    
    # Broadcast to webhooks
    background_tasks.add_task(webhook_service.broadcast_event, event)
    
    # Trigger additional processing
    background_tasks.add_task(process_new_resume, event)
    
    return {"message": "Event processed"}

@app.post("/events/candidate-searched")
async def handle_candidate_searched(
    event: CandidateSearchedEvent,
    background_tasks: BackgroundTasks
):
    """Handle candidate searched event"""
    logger.info(f"Candidate searched event: {event.search_id}")
    
    # Broadcast to webhooks
    background_tasks.add_task(webhook_service.broadcast_event, event)
    
    # Update search analytics
    background_tasks.add_task(update_search_analytics, event)
    
    return {"message": "Event processed"}

# Background processors
async def process_new_resume(event: ResumeUploadedEvent):
    """Process new resume upload"""
    try:
        # Trigger skills extraction
        await trigger_skills_extraction(event.resume_id)
        
        # Send notification to relevant team members
        await send_new_resume_notification(event)
        
        # Update candidate search index
        await update_search_index(event.candidate_id)
        
    except Exception as e:
        logger.error(f"Failed to process resume {event.resume_id}: {e}")

async def update_search_analytics(event: CandidateSearchedEvent):
    """Update search analytics"""
    try:
        # Store search metrics
        await store_search_metrics(event)
        
        # Update trending skills/companies
        await update_trending_data(event.search_params)
        
    except Exception as e:
        logger.error(f"Failed to update analytics for search {event.search_id}: {e}")

async def trigger_skills_extraction(resume_id: str):
    """Trigger AI-powered skills extraction"""
    logger.info(f"Triggering skills extraction for resume: {resume_id}")
    # Implementation would call Claude API or other NLP service

async def send_new_resume_notification(event: ResumeUploadedEvent):
    """Send notification about new resume"""
    notification_data = {
        "type": "new_resume",
        "resume_id": event.resume_id,
        "candidate_name": event.data.get("candidate_name"),
        "timestamp": event.timestamp.isoformat()
    }
    
    # Send to notification service
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://notification-service:8003/notifications/send",
            json=notification_data
        )

async def update_search_index(candidate_id: str):
    """Update search index for candidate"""
    logger.info(f"Updating search index for candidate: {candidate_id}")
    # Implementation would update Elasticsearch or similar

async def store_search_metrics(event: CandidateSearchedEvent):
    """Store search metrics for analytics"""
    logger.info(f"Storing metrics for search: {event.search_id}")
    # Implementation would store in InfluxDB or similar

async def update_trending_data(search_params: Dict[str, Any]):
    """Update trending skills and companies"""
    if "skills" in search_params:
        # Update skill popularity
        pass
    if "companies" in search_params:
        # Update company search frequency
        pass

# Webhook verification endpoint
@app.post("/webhooks/test/{webhook_id}")
async def test_webhook(webhook_id: str):
    """Test webhook delivery"""
    test_event = ResumeUploadedEvent(
        resume_id="test-resume-123",
        candidate_id="test-candidate-456",
        timestamp=datetime.utcnow(),
        data={"test": True}
    )
    
    success = await webhook_service.send_webhook(webhook_id, test_event)
    return {"webhook_id": webhook_id, "delivered": success}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
```

### Webhook Consumer Example

```python
# webhook_consumer.py
from fastapi import FastAPI, Request, HTTPException, Header
import hmac
import hashlib
import json
from typing import Optional

app = FastAPI(title="Webhook Consumer Example")

WEBHOOK_SECRET = "your-webhook-secret-here"

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature[7:]  # Remove 'sha256=' prefix
    
    return hmac.compare_digest(expected_signature, received_signature)

@app.post("/webhooks/hr-events")
async def handle_hr_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    x_webhook_event: Optional[str] = Header(None)
):
    """Handle incoming HR webhook events"""
    
    # Get raw payload
    payload = await request.body()
    
    # Verify signature
    if not x_webhook_signature or not verify_webhook_signature(payload, x_webhook_signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse event data
    try:
        event_data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Handle different event types
    event_type = x_webhook_event or event_data.get("event_type")
    
    if event_type == "resume.uploaded":
        await handle_resume_uploaded(event_data)
    elif event_type == "candidate.searched":
        await handle_candidate_searched(event_data)
    else:
        print(f"Unhandled event type: {event_type}")
    
    return {"status": "processed"}

async def handle_resume_uploaded(event_data: dict):
    """Handle resume uploaded event"""
    resume_id = event_data.get("resume_id")
    candidate_id = event_data.get("candidate_id")
    
    print(f"📄 New resume uploaded: {resume_id} for candidate: {candidate_id}")
    
    # Your business logic here
    # - Send email notification
    # - Update CRM system
    # - Trigger background processing
    # - Update dashboards

async def handle_candidate_searched(event_data: dict):
    """Handle candidate searched event"""
    search_id = event_data.get("search_id")
    results_count = event_data.get("results_count")
    
    print(f"🔍 Search performed: {search_id}, found {results_count} candidates")
    
    # Your business logic here
    # - Log search analytics
    # - Update user activity
    # - Trigger recommendations
    # - Update trending data
```

This comprehensive set of integration examples demonstrates how to build production-ready applications that integrate with the HR Resume Search API across different architectures and use cases.