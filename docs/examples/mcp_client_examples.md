# MCP Client Examples

**HR Resume Search API - Model Context Protocol Client Examples**

## Table of Contents

- [Python MCP Client](#python-mcp-client)
- [JavaScript MCP Client](#javascript-mcp-client)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Advanced Usage Patterns](#advanced-usage-patterns)
- [Error Handling & Resilience](#error-handling--resilience)
- [Production Deployment](#production-deployment)

---

## Python MCP Client

### Basic MCP Client Implementation

```python
# mcp_client_example.py
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# MCP Client Implementation
class HRResumeMCPClient:
    """
    MCP Client for HR Resume Search API
    Provides high-level interface for Claude and other AI agents
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000", api_key: str = None):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.session = None
        self.auth_token = None
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    # MCP Tool: Authentication
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        MCP Tool: Authenticate user and obtain access token
        """
        try:
            payload = {"email": email, "password": password}
            async with self.session.post(
                f"{self.api_base_url}/api/v1/auth/login",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data["access_token"]
                    self.logger.info(f"Successfully authenticated user: {email}")
                    return {
                        "success": True,
                        "access_token": data["access_token"],
                        "user": data["user"],
                        "expires_in": data["expires_in"]
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Authentication failed: {response.status} - {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return {"success": False, "error": str(e)}
    
    # MCP Tool: Intelligent Candidate Search
    async def search_candidates(
        self,
        query: str = "",
        skills: List[str] = None,
        search_type: str = "skills_match",
        min_experience_years: int = None,
        max_experience_years: int = None,
        companies: List[str] = None,
        departments: List[str] = None,
        locations: List[str] = None,
        education_level: str = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        MCP Tool: Search for candidates with intelligent matching
        
        Args:
            query: Natural language search query
            skills: List of required skills
            search_type: Type of search (skills_match, same_department, etc.)
            min_experience_years: Minimum years of experience
            max_experience_years: Maximum years of experience
            companies: List of target companies
            departments: List of target departments
            locations: List of preferred locations
            education_level: Required education level
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Search results with candidates and match scores
        """
        try:
            payload = {
                "query": query,
                "search_type": search_type,
                "limit": limit,
                "offset": offset
            }
            
            # Add optional filters
            if skills:
                payload["skills"] = skills
            if min_experience_years:
                payload["min_experience_years"] = min_experience_years
            if max_experience_years:
                payload["max_experience_years"] = max_experience_years
            if companies:
                payload["companies"] = companies
            if departments:
                payload["departments"] = departments
            if locations:
                payload["locations"] = locations
            if education_level:
                payload["education_level"] = education_level
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/search/candidates",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"Search completed: {data['total_results']} results in {data['processing_time_ms']}ms")
                    return {
                        "success": True,
                        "total_results": data["total_results"],
                        "candidates": data["results"],
                        "processing_time_ms": data["processing_time_ms"],
                        "search_params": payload
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Search failed: {response.status} - {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return {"success": False, "error": str(e)}
    
    # MCP Tool: Find Similar Candidates
    async def find_similar_candidates(
        self,
        reference_candidate_id: str,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        MCP Tool: Find candidates similar to a reference candidate
        
        Args:
            reference_candidate_id: UUID of the reference candidate
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of similar candidates to return
        
        Returns:
            List of similar candidates with similarity scores
        """
        try:
            payload = {
                "candidate_id": reference_candidate_id,
                "limit": limit
            }
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/search/similar",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filter by similarity threshold
                    filtered_candidates = [
                        candidate for candidate in data["results"]
                        if candidate["match_score"] >= similarity_threshold
                    ]
                    
                    self.logger.info(f"Found {len(filtered_candidates)} similar candidates (threshold: {similarity_threshold})")
                    return {
                        "success": True,
                        "reference_candidate_id": reference_candidate_id,
                        "similarity_threshold": similarity_threshold,
                        "candidates": filtered_candidates,
                        "total_found": len(filtered_candidates),
                        "processing_time_ms": data["processing_time_ms"]
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Similar search failed: {response.status} - {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Similar search error: {e}")
            return {"success": False, "error": str(e)}
    
    # MCP Tool: Find Colleagues
    async def find_colleagues(
        self,
        candidate_id: str,
        min_overlap_months: int = 3,
        include_potential: bool = True,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        MCP Tool: Find former colleagues of a candidate
        
        Args:
            candidate_id: UUID of the candidate
            min_overlap_months: Minimum overlap period in months
            include_potential: Include potential colleagues from same companies
            limit: Maximum number of colleagues to return
        
        Returns:
            List of colleagues with overlap information
        """
        try:
            payload = {
                "candidate_id": candidate_id,
                "limit": limit
            }
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/search/colleagues",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filter by minimum overlap
                    filtered_colleagues = []
                    for colleague in data["results"]:
                        overlap_months = colleague["highlights"].get("overlap_months", 0)
                        if overlap_months >= min_overlap_months:
                            filtered_colleagues.append(colleague)
                    
                    self.logger.info(f"Found {len(filtered_colleagues)} colleagues (min overlap: {min_overlap_months} months)")
                    return {
                        "success": True,
                        "candidate_id": candidate_id,
                        "colleagues": filtered_colleagues,
                        "total_found": len(filtered_colleagues),
                        "min_overlap_months": min_overlap_months,
                        "processing_time_ms": data["processing_time_ms"]
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Colleagues search failed: {response.status} - {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Colleagues search error: {e}")
            return {"success": False, "error": str(e)}
    
    # MCP Tool: Smart Natural Language Search
    async def smart_search(
        self,
        natural_query: str,
        limit: int = 10,
        include_reasoning: bool = True
    ) -> Dict[str, Any]:
        """
        MCP Tool: Intelligent search using natural language processing
        
        Args:
            natural_query: Natural language description of desired candidates
            limit: Maximum number of results
            include_reasoning: Include AI reasoning in response
        
        Returns:
            Search results with AI interpretation and reasoning
        """
        try:
            payload = {
                "query": natural_query,
                "limit": limit,
                "include_reasoning": include_reasoning
            }
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/search/smart",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"Smart search completed: {len(data['results'])} results")
                    return {
                        "success": True,
                        "original_query": natural_query,
                        "interpreted_query": data["interpreted_query"],
                        "candidates": data["results"],
                        "reasoning": data.get("reasoning"),
                        "suggested_queries": data.get("suggested_queries", []),
                        "processing_time_ms": data["processing_time_ms"]
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Smart search failed: {response.status} - {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Smart search error: {e}")
            return {"success": False, "error": str(e)}
    
    # MCP Tool: Get Search Filters
    async def get_available_filters(self) -> Dict[str, Any]:
        """
        MCP Tool: Get available search filters and statistics
        
        Returns:
            Available companies, skills, departments, and system statistics
        """
        try:
            async with self.session.get(
                f"{self.api_base_url}/api/v1/search/filters",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info("Retrieved search filters and statistics")
                    return {
                        "success": True,
                        "companies": data["companies"],
                        "departments": data["departments"],
                        "skills": data["skills"],
                        "locations": data["locations"],
                        "experience_range": data["experience_range"],
                        "education_levels": data["education_levels"],
                        "search_types": data["search_types"],
                        "statistics": data["statistics"]
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Failed to get filters: {response.status} - {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Get filters error: {e}")
            return {"success": False, "error": str(e)}
    
    # MCP Tool: Resume Upload
    async def upload_resume(
        self,
        file_path: str,
        candidate_name: str,
        email: str,
        phone: str = None
    ) -> Dict[str, Any]:
        """
        MCP Tool: Upload and process a resume file
        
        Args:
            file_path: Path to the resume file
            candidate_name: Name of the candidate
            email: Email address
            phone: Phone number (optional)
        
        Returns:
            Upload status and processing information
        """
        try:
            import aiofiles
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('candidate_name', candidate_name)
            data.add_field('email', email)
            if phone:
                data.add_field('phone', phone)
            
            # Add file
            async with aiofiles.open(file_path, 'rb') as file:
                file_content = await file.read()
                data.add_field('file', file_content, filename=file_path.split('/')[-1])
            
            # Remove Content-Type header to allow aiohttp to set it with boundary
            headers = self._get_headers()
            headers.pop('Content-Type', None)
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/resumes/upload",
                data=data,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"Resume uploaded successfully: {data['resume_id']}")
                    return {
                        "success": True,
                        "resume_id": data["resume_id"],
                        "candidate_id": data["candidate_id"],
                        "status": data["status"],
                        "estimated_processing_time": data.get("estimated_processing_time"),
                        "file_info": data.get("file_info")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Upload failed: {response.status} - {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            return {"success": False, "error": str(e)}
    
    # MCP Tool: Check Resume Processing Status
    async def check_resume_status(self, resume_id: str) -> Dict[str, Any]:
        """
        MCP Tool: Check the processing status of an uploaded resume
        
        Args:
            resume_id: UUID of the resume
        
        Returns:
            Processing status and extracted data summary
        """
        try:
            async with self.session.get(
                f"{self.api_base_url}/api/v1/resumes/{resume_id}/status",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"Resume status: {data['status']} ({data['progress']}%)")
                    return {
                        "success": True,
                        "resume_id": resume_id,
                        "status": data["status"],
                        "progress": data["progress"],
                        "processing_stages": data["processing_stages"],
                        "processed_at": data.get("processed_at"),
                        "processing_time_seconds": data.get("processing_time_seconds"),
                        "extracted_data": data.get("extracted_data")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Status check failed: {response.status} - {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Status check error: {e}")
            return {"success": False, "error": str(e)}
    
    # MCP Tool: Get API Health Status
    async def get_api_status(self) -> Dict[str, Any]:
        """
        MCP Tool: Check API health and system status
        
        Returns:
            System health information and statistics
        """
        try:
            async with self.session.get(
                f"{self.api_base_url}/readiness",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"API Status: {data['status']}")
                    return {
                        "success": True,
                        "status": data["status"],
                        "checks": data["checks"],
                        "total_check_time_ms": data["total_check_time_ms"],
                        "timestamp": data["timestamp"]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Health check failed: {response.status}"
                    }
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return {"success": False, "error": str(e)}


# Example Usage Script
async def main():
    """Example usage of the HR Resume MCP Client"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    async with HRResumeMCPClient() as client:
        print("🔍 HR Resume Search MCP Client Demo")
        print("=" * 50)
        
        # 1. Check API status
        print("\n1. Checking API status...")
        status = await client.get_api_status()
        if status["success"]:
            print(f"✅ API Status: {status['status']}")
            print(f"   Database: {status['checks']['database']['status']}")
        else:
            print(f"❌ API Error: {status['error']}")
            return
        
        # 2. Authenticate (optional - you can also use API key)
        print("\n2. Authenticating...")
        auth_result = await client.authenticate_user("hr@company.com", "password")
        if auth_result["success"]:
            print(f"✅ Authenticated as: {auth_result['user']['email']}")
        else:
            print(f"⚠️  Authentication failed: {auth_result['error']}")
            print("   Continuing with API key authentication...")
        
        # 3. Get available filters
        print("\n3. Getting available search filters...")
        filters = await client.get_available_filters()
        if filters["success"]:
            print(f"✅ Found {len(filters['companies'])} companies, {len(filters['skills'])} skills")
            print(f"   Top skills: {', '.join([s['name'] for s in filters['skills'][:5]])}")
        
        # 4. Search for Python developers
        print("\n4. Searching for Python developers...")
        search_result = await client.search_candidates(
            skills=["Python", "FastAPI", "PostgreSQL"],
            min_experience_years=3,
            limit=5
        )
        
        if search_result["success"]:
            print(f"✅ Found {search_result['total_results']} candidates")
            for i, candidate in enumerate(search_result['candidates'][:3], 1):
                print(f"   {i}. {candidate['full_name']} - Score: {candidate['match_score']:.2f}")
                print(f"      {candidate['current_position']} at {candidate['current_company']}")
        
        # 5. Find similar candidates (if we have results)
        if search_result["success"] and search_result['candidates']:
            first_candidate = search_result['candidates'][0]
            print(f"\n5. Finding candidates similar to {first_candidate['full_name']}...")
            
            similar_result = await client.find_similar_candidates(
                first_candidate['candidate_id'],
                similarity_threshold=0.7,
                limit=3
            )
            
            if similar_result["success"]:
                print(f"✅ Found {similar_result['total_found']} similar candidates")
                for candidate in similar_result['candidates']:
                    print(f"   - {candidate['full_name']}: {candidate['match_score']:.2f}")
        
        # 6. Find colleagues
        if search_result["success"] and search_result['candidates']:
            first_candidate = search_result['candidates'][0]
            print(f"\n6. Finding colleagues of {first_candidate['full_name']}...")
            
            colleagues_result = await client.find_colleagues(
                first_candidate['candidate_id'],
                min_overlap_months=3,
                limit=3
            )
            
            if colleagues_result["success"]:
                print(f"✅ Found {colleagues_result['total_found']} colleagues")
                for colleague in colleagues_result['colleagues']:
                    overlap = colleague['highlights']['overlap_months']
                    company = colleague['highlights']['company']
                    print(f"   - {colleague['full_name']} at {company} ({overlap} months overlap)")
        
        # 7. Smart natural language search
        print("\n7. Testing smart natural language search...")
        smart_result = await client.smart_search(
            "Find senior data scientists with machine learning experience who have worked at tech companies",
            limit=3,
            include_reasoning=True
        )
        
        if smart_result["success"]:
            print(f"✅ Smart search found {len(smart_result['candidates'])} candidates")
            print(f"   AI Reasoning: {smart_result['reasoning']}")
            for candidate in smart_result['candidates']:
                print(f"   - {candidate['full_name']}: {candidate['match_score']:.2f}")
        
        print("\n🎉 MCP Client demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## JavaScript MCP Client

### Node.js MCP Client Implementation

```javascript
// mcp_client_node.js
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs').promises;

class HRResumeMCPClient {
    constructor(baseUrl = 'http://localhost:8000', apiKey = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
        this.authToken = null;
        this.client = axios.create({
            baseURL: this.baseUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Request interceptor for authentication
        this.client.interceptors.request.use(config => {
            if (this.authToken) {
                config.headers.Authorization = `Bearer ${this.authToken}`;
            } else if (this.apiKey) {
                config.headers['X-API-Key'] = this.apiKey;
            }
            return config;
        });
        
        // Response interceptor for error handling
        this.client.interceptors.response.use(
            response => response,
            error => {
                console.error(`API Error: ${error.response?.status} - ${error.response?.data?.error?.message || error.message}`);
                return Promise.reject(error);
            }
        );
    }
    
    // MCP Tool: Authentication
    async authenticateUser(email, password) {
        try {
            const response = await this.client.post('/api/v1/auth/login', {
                email,
                password
            });
            
            this.authToken = response.data.access_token;
            console.log(`✅ Authenticated as: ${email}`);
            
            return {
                success: true,
                access_token: response.data.access_token,
                user: response.data.user,
                expires_in: response.data.expires_in
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
    
    // MCP Tool: Intelligent Candidate Search
    async searchCandidates({
        query = '',
        skills = null,
        searchType = 'skills_match',
        minExperienceYears = null,
        maxExperienceYears = null,
        companies = null,
        departments = null,
        locations = null,
        educationLevel = null,
        limit = 10,
        offset = 0
    } = {}) {
        try {
            const payload = {
                query,
                search_type: searchType,
                limit,
                offset
            };
            
            // Add optional filters
            if (skills) payload.skills = skills;
            if (minExperienceYears) payload.min_experience_years = minExperienceYears;
            if (maxExperienceYears) payload.max_experience_years = maxExperienceYears;
            if (companies) payload.companies = companies;
            if (departments) payload.departments = departments;
            if (locations) payload.locations = locations;
            if (educationLevel) payload.education_level = educationLevel;
            
            const response = await this.client.post('/api/v1/search/candidates', payload);
            
            console.log(`🔍 Search completed: ${response.data.total_results} results in ${response.data.processing_time_ms}ms`);
            
            return {
                success: true,
                totalResults: response.data.total_results,
                candidates: response.data.results,
                processingTimeMs: response.data.processing_time_ms,
                searchParams: payload
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
    
    // MCP Tool: Find Similar Candidates
    async findSimilarCandidates(referenceCandidateId, { similarityThreshold = 0.7, limit = 10 } = {}) {
        try {
            const response = await this.client.post('/api/v1/search/similar', {
                candidate_id: referenceCandidateId,
                limit
            });
            
            // Filter by similarity threshold
            const filteredCandidates = response.data.results.filter(
                candidate => candidate.match_score >= similarityThreshold
            );
            
            console.log(`👥 Found ${filteredCandidates.length} similar candidates (threshold: ${similarityThreshold})`);
            
            return {
                success: true,
                referenceCandidateId,
                similarityThreshold,
                candidates: filteredCandidates,
                totalFound: filteredCandidates.length,
                processingTimeMs: response.data.processing_time_ms
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
    
    // MCP Tool: Find Colleagues
    async findColleagues(candidateId, { minOverlapMonths = 3, limit = 10 } = {}) {
        try {
            const response = await this.client.post('/api/v1/search/colleagues', {
                candidate_id: candidateId,
                limit
            });
            
            // Filter by minimum overlap
            const filteredColleagues = response.data.results.filter(
                colleague => (colleague.highlights?.overlap_months || 0) >= minOverlapMonths
            );
            
            console.log(`🤝 Found ${filteredColleagues.length} colleagues (min overlap: ${minOverlapMonths} months)`);
            
            return {
                success: true,
                candidateId,
                colleagues: filteredColleagues,
                totalFound: filteredColleagues.length,
                minOverlapMonths,
                processingTimeMs: response.data.processing_time_ms
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
    
    // MCP Tool: Smart Natural Language Search
    async smartSearch(naturalQuery, { limit = 10, includeReasoning = true } = {}) {
        try {
            const response = await this.client.post('/api/v1/search/smart', {
                query: naturalQuery,
                limit,
                include_reasoning: includeReasoning
            });
            
            console.log(`🧠 Smart search completed: ${response.data.results.length} results`);
            
            return {
                success: true,
                originalQuery: naturalQuery,
                interpretedQuery: response.data.interpreted_query,
                candidates: response.data.results,
                reasoning: response.data.reasoning,
                suggestedQueries: response.data.suggested_queries || [],
                processingTimeMs: response.data.processing_time_ms
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
    
    // MCP Tool: Get Available Filters
    async getAvailableFilters() {
        try {
            const response = await this.client.get('/api/v1/search/filters');
            
            console.log('📊 Retrieved search filters and statistics');
            
            return {
                success: true,
                companies: response.data.companies,
                departments: response.data.departments,
                skills: response.data.skills,
                locations: response.data.locations,
                experienceRange: response.data.experience_range,
                educationLevels: response.data.education_levels,
                searchTypes: response.data.search_types,
                statistics: response.data.statistics
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
    
    // MCP Tool: Upload Resume
    async uploadResume(filePath, candidateName, email, phone = null) {
        try {
            const formData = new FormData();
            
            // Add form fields
            formData.append('candidate_name', candidateName);
            formData.append('email', email);
            if (phone) formData.append('phone', phone);
            
            // Add file
            const fileBuffer = await fs.readFile(filePath);
            const fileName = filePath.split('/').pop();
            formData.append('file', fileBuffer, fileName);
            
            const response = await this.client.post('/api/v1/resumes/upload', formData, {
                headers: {
                    ...formData.getHeaders(),
                    Authorization: this.authToken ? `Bearer ${this.authToken}` : undefined,
                    'X-API-Key': this.apiKey || undefined
                }
            });
            
            console.log(`📄 Resume uploaded successfully: ${response.data.resume_id}`);
            
            return {
                success: true,
                resumeId: response.data.resume_id,
                candidateId: response.data.candidate_id,
                status: response.data.status,
                estimatedProcessingTime: response.data.estimated_processing_time,
                fileInfo: response.data.file_info
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
    
    // MCP Tool: Check Resume Processing Status
    async checkResumeStatus(resumeId) {
        try {
            const response = await this.client.get(`/api/v1/resumes/${resumeId}/status`);
            
            console.log(`📋 Resume status: ${response.data.status} (${response.data.progress}%)`);
            
            return {
                success: true,
                resumeId,
                status: response.data.status,
                progress: response.data.progress,
                processingStages: response.data.processing_stages,
                processedAt: response.data.processed_at,
                processingTimeSeconds: response.data.processing_time_seconds,
                extractedData: response.data.extracted_data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
    
    // MCP Tool: Get API Health Status
    async getApiStatus() {
        try {
            const response = await this.client.get('/readiness');
            
            console.log(`💚 API Status: ${response.data.status}`);
            
            return {
                success: true,
                status: response.data.status,
                checks: response.data.checks,
                totalCheckTimeMs: response.data.total_check_time_ms,
                timestamp: response.data.timestamp
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error?.message || error.message
            };
        }
    }
}

// Example Usage
async function demoMCPClient() {
    console.log('🔍 HR Resume Search MCP Client Demo (Node.js)');
    console.log('='.repeat(50));
    
    const client = new HRResumeMCPClient();
    
    try {
        // 1. Check API status
        console.log('\n1. Checking API status...');
        const status = await client.getApiStatus();
        if (!status.success) {
            console.error('❌ API is not available');
            return;
        }
        
        // 2. Authenticate
        console.log('\n2. Authenticating...');
        const authResult = await client.authenticateUser('hr@company.com', 'password');
        if (!authResult.success) {
            console.log('⚠️ Authentication failed, continuing with API key...');
        }
        
        // 3. Get filters
        console.log('\n3. Getting available filters...');
        const filters = await client.getAvailableFilters();
        if (filters.success) {
            console.log(`✅ Found ${filters.companies.length} companies, ${filters.skills.length} skills`);
        }
        
        // 4. Search for candidates
        console.log('\n4. Searching for JavaScript developers...');
        const searchResult = await client.searchCandidates({
            skills: ['JavaScript', 'React', 'Node.js'],
            minExperienceYears: 2,
            limit: 5
        });
        
        if (searchResult.success) {
            console.log(`✅ Found ${searchResult.totalResults} candidates`);
            searchResult.candidates.slice(0, 3).forEach((candidate, i) => {
                console.log(`   ${i + 1}. ${candidate.full_name} - Score: ${candidate.match_score.toFixed(2)}`);
                console.log(`      ${candidate.current_position} at ${candidate.current_company}`);
            });
        }
        
        // 5. Smart search
        console.log('\n5. Testing smart natural language search...');
        const smartResult = await client.smartSearch(
            'Find experienced frontend developers who have worked at startups',
            { limit: 3, includeReasoning: true }
        );
        
        if (smartResult.success) {
            console.log(`🧠 Smart search found ${smartResult.candidates.length} candidates`);
            console.log(`   AI Reasoning: ${smartResult.reasoning}`);
        }
        
        console.log('\n🎉 MCP Client demo completed successfully!');
        
    } catch (error) {
        console.error('Demo failed:', error.message);
    }
}

// Export for use as module
module.exports = HRResumeMCPClient;

// Run demo if executed directly
if (require.main === module) {
    demoMCPClient().catch(console.error);
}
```

---

## Claude Desktop Integration

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["/path/to/mcp_server/server.py"],
      "env": {
        "API_BASE_URL": "http://localhost:8000",
        "API_KEY": "your_api_key_here",
        "CLAUDE_API_KEY": "your_claude_api_key"
      }
    }
  }
}
```

### Claude Conversation Examples

#### Example 1: Finding Senior Developers

```
User: I need to find senior Python developers who have worked at tech companies and have experience with cloud platforms

Claude: I'll help you find senior Python developers with tech company and cloud experience using the HR Resume Search system.

[Using search_candidates tool]

I found 31 senior Python developers who match your criteria. Here are the top candidates:

**🏆 Top Matches:**

1. **Sarah Chen** (Match Score: 0.94)
   - 8 years experience, Senior Software Engineer at TechCorp
   - Skills: Python, AWS, Docker, Kubernetes, FastAPI
   - Previous: Google, Amazon Web Services
   - Location: San Francisco, CA

2. **Michael Rodriguez** (Match Score: 0.91) 
   - 7 years experience, Principal Engineer at DataFlow Inc
   - Skills: Python, Azure, Terraform, Django, PostgreSQL
   - Previous: Microsoft, Uber Technologies
   - Location: Seattle, WA

3. **Alex Kim** (Match Score: 0.89)
   - 6 years experience, Tech Lead at AI Innovations
   - Skills: Python, GCP, MLOps, TensorFlow, REST APIs
   - Previous: Netflix, Spotify
   - Location: Los Angeles, CA

**📊 Search Summary:**
- Total candidates found: 31
- Average experience: 7.2 years
- Top cloud platforms: AWS (18), Azure (12), GCP (15)
- Processing time: 287ms

Would you like me to:
1. Find similar profiles to any of these candidates?
2. Check if any have worked together before?
3. Get more detailed information about specific candidates?
4. Refine the search with additional criteria?
```

#### Example 2: Network Analysis

```
User: Can you find people who have worked with Sarah Chen and see if there are other connections in her network?

Claude: I'll analyze Sarah Chen's professional network to find colleagues and potential connections.

[Using find_colleagues tool for Sarah Chen]

**🤝 Former Colleagues of Sarah Chen:**

**Direct Colleagues (Worked Together):**
1. **David Park** - Engineering Manager at DataFlow Inc
   - Worked together at: TechCorp (18 months overlap, 2020-2021)
   - Same department: Backend Engineering
   - Current: Leading a team of 12 engineers

2. **Lisa Wang** - Senior DevOps Engineer at CloudTech
   - Worked together at: Google (12 months overlap, 2019)
   - Same department: Cloud Infrastructure
   - Current: Kubernetes specialist, AWS certified

3. **James Miller** - Principal Architect at StartupX
   - Worked together at: TechCorp (24 months overlap, 2021-2023)
   - Same department: Platform Engineering
   - Current: Designing microservices architecture

[Using find_similar_candidates for each colleague]

**🔗 Extended Network Analysis:**

**Similar to David Park:**
- **Emma Thompson** (Similarity: 0.88) - Also worked at TechCorp, now at Meta
- **Robert Chen** (Similarity: 0.85) - Similar backend experience, now at Stripe

**Similar to Lisa Wang:**
- **Maria Gonzalez** (Similarity: 0.90) - DevOps expert, worked at Netflix
- **Kevin Zhang** (Similarity: 0.87) - Cloud architect, worked at Airbnb

**🎯 Network Insights:**
- **Strong TechCorp Alumni Network**: 8 connected professionals
- **Cloud Infrastructure Expertise**: High concentration of AWS/GCP specialists
- **Startup Experience**: 60% have worked at high-growth startups
- **Geographic Concentration**: 70% in SF Bay Area

**💡 Recommendations:**
1. **David Park** - Excellent management candidate with direct collaboration history
2. **Lisa Wang** - Perfect for DevOps/Infrastructure roles, proven team player
3. **Emma Thompson** - High-potential candidate in Sarah's extended network

This network shows strong technical depth and collaborative relationships that could benefit team dynamics and knowledge sharing.
```

#### Example 3: Smart Search with Reasoning

```
User: Find me data scientists who have transitioned from academic research to industry and have experience with both traditional ML and deep learning

Claude: I'll search for data scientists with academic-to-industry transition experience and expertise in both traditional ML and deep learning.

[Using smart_search tool]

**🧠 AI Search Interpretation:**
- **Detected Intent**: Skills match with career transition analysis
- **Key Criteria**: Academic background + industry experience + dual ML expertise
- **Search Strategy**: Combined education filtering with skills analysis

**🔬 Academic-to-Industry Data Scientists:**

1. **Dr. Jennifer Liu** (Match Score: 0.96)
   - **Academic Background**: PhD Computer Science, Stanford (2018)
   - **Industry Transition**: 2019 - Joined Facebook AI Research
   - **ML Expertise**: Scikit-learn, TensorFlow, PyTorch, XGBoost
   - **Current Role**: Senior Data Scientist at Meta
   - **Notable**: Published 15 papers, 3 patents in deep learning

2. **Dr. Ahmed Hassan** (Match Score: 0.93)
   - **Academic Background**: PhD Statistics, MIT (2017) + 2 years postdoc
   - **Industry Transition**: 2020 - Joined Google DeepMind
   - **ML Expertise**: R, Python, Keras, Statistical modeling, NLP
   - **Current Role**: Principal Data Scientist at Alphabet
   - **Notable**: Expertise in both Bayesian methods and neural networks

3. **Dr. Rachel Kim** (Match Score: 0.90)
   - **Academic Background**: PhD Physics, UC Berkeley (2019)
   - **Industry Transition**: 2020 - Joined Netflix Machine Learning Platform
   - **ML Expertise**: Traditional econometrics + deep reinforcement learning
   - **Current Role**: Staff Data Scientist at Netflix
   - **Notable**: Recommendation systems expert, A/B testing specialist

**🎯 Analysis Summary:**
- **Academic Pedigree**: All have advanced degrees from top-tier institutions
- **Transition Timeline**: Average 1-2 years between PhD completion and industry entry
- **Skill Evolution**: Strong foundation in statistical methods enhanced with deep learning
- **Industry Impact**: All in senior roles within 3-4 years of transition

**💡 Why These Candidates Excel:**
1. **Research Rigor**: Academic training provides strong experimental design skills
2. **Learning Agility**: Successfully adapted cutting-edge research to business problems  
3. **Hybrid Expertise**: Combines theoretical depth with practical implementation
4. **Publication Track Record**: Demonstrates thought leadership and communication skills

**🔍 Additional Insights:**
- **Geographic Concentration**: 60% in SF Bay Area (tech hub proximity)
- **Industry Preferences**: Tech giants and research-focused companies
- **Specialization Areas**: NLP (40%), Computer Vision (30%), Recommender Systems (30%)

These candidates represent the ideal blend of academic rigor and industry pragmatism, capable of both advancing the state-of-the-art and delivering business value.
```

---

## Advanced Usage Patterns

### Batch Processing Example

```python
# batch_operations.py
import asyncio
from typing import List, Dict, Any
import json

async def batch_candidate_analysis(client: HRResumeMCPClient, search_queries: List[Dict]) -> Dict[str, Any]:
    """
    Perform batch analysis across multiple search criteria
    """
    print("🔄 Starting batch candidate analysis...")
    
    # Execute searches in parallel
    search_tasks = []
    for i, query in enumerate(search_queries):
        task = client.search_candidates(**query)
        search_tasks.append(task)
    
    search_results = await asyncio.gather(*search_tasks)
    
    # Aggregate results
    all_candidates = []
    successful_searches = 0
    total_processing_time = 0
    
    for i, result in enumerate(search_results):
        if result["success"]:
            successful_searches += 1
            all_candidates.extend(result["candidates"])
            total_processing_time += result["processing_time_ms"]
            print(f"✅ Search {i+1}: {result['total_results']} candidates found")
        else:
            print(f"❌ Search {i+1} failed: {result['error']}")
    
    # Remove duplicates based on candidate_id
    unique_candidates = {}
    for candidate in all_candidates:
        candidate_id = candidate["candidate_id"]
        if candidate_id not in unique_candidates or candidate["match_score"] > unique_candidates[candidate_id]["match_score"]:
            unique_candidates[candidate_id] = candidate
    
    # Sort by match score
    final_candidates = sorted(unique_candidates.values(), key=lambda x: x["match_score"], reverse=True)
    
    return {
        "success": True,
        "total_searches": len(search_queries),
        "successful_searches": successful_searches,
        "unique_candidates": len(final_candidates),
        "candidates": final_candidates[:20],  # Top 20
        "total_processing_time_ms": total_processing_time,
        "average_processing_time_ms": total_processing_time / successful_searches if successful_searches > 0 else 0
    }

async def candidate_network_analysis(client: HRResumeMCPClient, candidate_id: str) -> Dict[str, Any]:
    """
    Comprehensive network analysis for a candidate
    """
    print(f"🕸️ Analyzing network for candidate: {candidate_id}")
    
    # Parallel execution of network queries
    similar_task = client.find_similar_candidates(candidate_id, limit=10)
    colleagues_task = client.find_colleagues(candidate_id, limit=10)
    
    similar_result, colleagues_result = await asyncio.gather(similar_task, colleagues_task)
    
    # Analyze colleague networks
    colleague_networks = []
    if colleagues_result["success"]:
        colleague_tasks = []
        for colleague in colleagues_result["colleagues"][:5]:  # Limit to top 5
            task = client.find_colleagues(colleague["candidate_id"], limit=5)
            colleague_tasks.append(task)
        
        colleague_network_results = await asyncio.gather(*colleague_tasks)
        
        for i, colleague in enumerate(colleagues_result["colleagues"][:5]):
            network_result = colleague_network_results[i]
            if network_result["success"]:
                colleague_networks.append({
                    "colleague": colleague,
                    "network_size": network_result["total_found"],
                    "mutual_connections": []  # Could implement mutual connection detection
                })
    
    # Build comprehensive network map
    network_analysis = {
        "target_candidate_id": candidate_id,
        "similar_candidates": {
            "count": similar_result.get("total_found", 0),
            "candidates": similar_result.get("candidates", [])
        },
        "direct_colleagues": {
            "count": colleagues_result.get("total_found", 0),
            "colleagues": colleagues_result.get("colleagues", [])
        },
        "extended_network": colleague_networks,
        "network_insights": {
            "total_network_size": (
                similar_result.get("total_found", 0) + 
                colleagues_result.get("total_found", 0) +
                sum(net["network_size"] for net in colleague_networks)
            ),
            "strongest_connections": [],
            "common_companies": set(),
            "skill_overlap": []
        }
    }
    
    # Calculate network insights
    all_network_candidates = (
        similar_result.get("candidates", []) + 
        colleagues_result.get("colleagues", [])
    )
    
    # Find common companies
    for candidate in all_network_candidates:
        if "highlights" in candidate and "company" in candidate["highlights"]:
            network_analysis["network_insights"]["common_companies"].add(
                candidate["highlights"]["company"]
            )
    
    network_analysis["network_insights"]["common_companies"] = list(
        network_analysis["network_insights"]["common_companies"]
    )
    
    return network_analysis

# Usage example
async def advanced_search_demo():
    """Demonstration of advanced search patterns"""
    
    async with HRResumeMCPClient() as client:
        # 1. Batch multi-criteria search
        search_queries = [
            {"skills": ["Python", "Machine Learning"], "min_experience_years": 5},
            {"skills": ["JavaScript", "React"], "companies": ["Google", "Meta"]},
            {"skills": ["Java", "Spring"], "departments": ["Engineering"]},
            {"skills": ["Go", "Kubernetes"], "locations": ["San Francisco"]}
        ]
        
        batch_result = await batch_candidate_analysis(client, search_queries)
        print(f"\n📊 Batch Analysis Results:")
        print(f"   Unique candidates found: {batch_result['unique_candidates']}")
        print(f"   Average processing time: {batch_result['average_processing_time_ms']:.2f}ms")
        
        # 2. Network analysis for top candidate
        if batch_result["candidates"]:
            top_candidate = batch_result["candidates"][0]
            network_result = await candidate_network_analysis(
                client, 
                top_candidate["candidate_id"]
            )
            
            print(f"\n🕸️ Network Analysis for {top_candidate['full_name']}:")
            print(f"   Similar candidates: {network_result['similar_candidates']['count']}")
            print(f"   Direct colleagues: {network_result['direct_colleagues']['count']}")
            print(f"   Total network size: {network_result['network_insights']['total_network_size']}")
            print(f"   Common companies: {', '.join(network_result['network_insights']['common_companies'][:5])}")

if __name__ == "__main__":
    asyncio.run(advanced_search_demo())
```

This comprehensive MCP client example collection provides production-ready code for integrating with the HR Resume Search API through the Model Context Protocol, with extensive error handling, advanced usage patterns, and real-world conversation examples.