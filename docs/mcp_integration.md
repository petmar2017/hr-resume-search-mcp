# MCP Server Integration Guide

**Model Context Protocol (MCP) Integration for HR Resume Search API**

## Table of Contents

- [Overview](#overview)
- [MCP Server Architecture](#mcp-server-architecture)
- [Installation & Setup](#installation--setup)
- [Available Tools](#available-tools)
- [Client Integration](#client-integration)
- [Authentication](#authentication)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

The HR Resume Search MCP Server provides intelligent tools for AI agents to interact with the resume database and perform sophisticated search operations. It bridges Claude AI with the HR Resume Search API through the Model Context Protocol.

### Key Capabilities

🔍 **Intelligent Resume Search**: Advanced search algorithms with natural language processing  
🧠 **AI-Powered Analysis**: Claude integration for resume parsing and candidate matching  
⚡ **Real-time Processing**: Async operations for optimal performance  
🛠️ **Extensible Tools**: Plugin-based architecture for custom functionality  
📊 **Analytics & Insights**: Candidate analytics and search pattern analysis  

---

## MCP Server Architecture

### Core Components

```
mcp_server/
├── server.py              # Main MCP server entry point
├── hr_tools.py            # HR-specific tools and utilities
├── claude_desktop_config.json  # Claude Desktop configuration
├── requirements.txt       # Python dependencies
└── tests/
    └── test_mcp_server.py # Server integration tests
```

### Tool Categories

1. **API Management Tools**: Health checks, endpoint creation, validation
2. **Resume Processing Tools**: Upload, parsing, data extraction
3. **Search & Discovery Tools**: Candidate search, similarity matching, colleague discovery
4. **Analytics Tools**: Performance metrics, search analytics
5. **Documentation Tools**: API docs generation, schema validation

---

## Installation & Setup

### Prerequisites

- Python 3.12+
- HR Resume Search API running on `localhost:8000`
- Claude Desktop or MCP-compatible client

### Step 1: Install Dependencies

```bash
cd mcp_server
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create `.env` file in `mcp_server/` directory:

```env
# API Configuration
API_BASE_URL=http://localhost:8000
API_KEY=your_api_key_here

# Claude Configuration
CLAUDE_API_KEY=your_claude_api_key
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Database Configuration (optional for direct access)
DATABASE_URL=postgresql://user:password@localhost:5432/hr_resume_db

# MCP Server Configuration
MCP_SERVER_NAME=hr-resume-search-mcp
MCP_SERVER_VERSION=1.0.0
DEBUG=true
```

### Step 3: Configure Claude Desktop

Add to your Claude Desktop configuration (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["/path/to/mcp_server/server.py"],
      "env": {
        "API_BASE_URL": "http://localhost:8000",
        "API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Step 4: Start MCP Server

```bash
# Development mode
python server.py

# Production mode with logging
python server.py --log-level INFO --log-file mcp_server.log
```

### Step 5: Verify Installation

```bash
# Test server connectivity
curl -X POST http://localhost:8000/mcp/health

# Test tool availability
python -c "
from mcp_server.server import app
tools = app.list_tools()
print(f'Available tools: {len(tools)}')
"
```

---

## Available Tools

### API Management Tools

#### `get_api_status`
**Description**: Check API health status and configuration

```python
# Usage in Claude
result = await get_api_status()
print(f"API Status: {result['status']}")
print(f"Endpoints: {result['endpoints_count']}")
```

**Response**:
```json
{
  "status": "running",
  "timestamp": "2025-08-03T10:30:00.000Z",
  "endpoints_count": 25,
  "api_path": "/path/to/api",
  "environment": "development"
}
```

#### `validate_api_structure`
**Description**: Validate API project structure and identify missing components

```python
result = await validate_api_structure()
if not result['valid']:
    print("Issues found:", result['issues'])
    print("Recommendations:", result['recommendations'])
```

### Resume Processing Tools

#### `search_candidates`
**Description**: Intelligent candidate search with multi-criteria matching

```python
# Basic skills search
candidates = await search_candidates(
    query="Senior Python developer",
    skills=["Python", "FastAPI", "PostgreSQL"],
    min_experience=5,
    limit=10
)

# Advanced search with filters
candidates = await search_candidates(
    query="Data scientist with startup experience",
    skills=["Python", "Machine Learning", "SQL"],
    companies=["startup", "tech"],
    departments=["Data Science", "Engineering"],
    location="San Francisco",
    education_level="masters"
)
```

**Response**:
```json
{
  "success": true,
  "total_results": 23,
  "candidates": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "John Doe",
      "match_score": 0.92,
      "skills": ["Python", "FastAPI", "PostgreSQL"],
      "experience_years": 8,
      "current_position": "Senior Software Engineer"
    }
  ],
  "processing_time_ms": 245
}
```

#### `find_similar_candidates`
**Description**: Find profiles similar to a reference candidate

```python
similar = await find_similar_candidates(
    reference_candidate_id="123e4567-e89b-12d3-a456-426614174000",
    similarity_threshold=0.7,
    limit=5
)

for candidate in similar['candidates']:
    print(f"Similar: {candidate['name']} (score: {candidate['similarity_score']})")
```

#### `find_colleagues`
**Description**: Discover former colleagues with workplace overlap analysis

```python
colleagues = await find_colleagues(
    candidate_id="123e4567-e89b-12d3-a456-426614174000",
    min_overlap_months=6,
    include_potential=True
)

for colleague in colleagues['colleagues']:
    print(f"Colleague: {colleague['name']} at {colleague['company']} ({colleague['overlap_months']} months)")
```

### Analytics Tools

#### `get_search_analytics`
**Description**: Retrieve search pattern analytics and insights

```python
analytics = await get_search_analytics(
    date_range="last_30_days",
    include_trends=True
)

print(f"Total searches: {analytics['total_searches']}")
print(f"Popular skills: {analytics['trending_skills']}")
print(f"Search success rate: {analytics['success_rate']}%")
```

#### `get_candidate_insights`
**Description**: Generate insights about candidate pool and trends

```python
insights = await get_candidate_insights(
    analysis_type="skills_gap",
    departments=["Engineering", "Data Science"]
)

print(f"Skills gap analysis: {insights['skills_analysis']}")
print(f"Recommendations: {insights['recommendations']}")
```

### Documentation Tools

#### `generate_api_docs`
**Description**: Generate API documentation from existing endpoints

```python
# Generate markdown documentation
docs = await generate_api_docs(
    format="markdown",
    include_examples=True,
    output_path="/docs/generated_api.md"
)

# Generate OpenAPI specification
openapi = await generate_api_docs(
    format="openapi",
    version="1.0.0",
    output_path="/docs/openapi.json"
)
```

#### `create_postman_collection`
**Description**: Generate Postman collection for API testing

```python
collection = await create_postman_collection(
    include_auth=True,
    include_examples=True,
    output_path="/docs/postman_collection.json"
)

print(f"Created collection with {collection['endpoint_count']} endpoints")
```

---

## Client Integration

### Python Client Example

```python
import asyncio
from mcp_client import MCPClient

async def main():
    # Initialize MCP client
    client = MCPClient("hr-resume-search")
    await client.connect()
    
    try:
        # Search for candidates
        candidates = await client.call_tool("search_candidates", {
            "query": "Python developer with AI experience",
            "skills": ["Python", "Machine Learning", "FastAPI"],
            "min_experience": 3,
            "limit": 10
        })
        
        print(f"Found {candidates['total_results']} candidates")
        
        # Analyze first candidate
        if candidates['candidates']:
            first_candidate = candidates['candidates'][0]
            
            # Find similar profiles
            similar = await client.call_tool("find_similar_candidates", {
                "reference_candidate_id": first_candidate['id'],
                "limit": 5
            })
            
            print(f"Found {len(similar['candidates'])} similar candidates")
            
            # Find colleagues
            colleagues = await client.call_tool("find_colleagues", {
                "candidate_id": first_candidate['id'],
                "min_overlap_months": 3
            })
            
            print(f"Found {len(colleagues['colleagues'])} former colleagues")
            
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript Client Example

```javascript
import { MCPClient } from '@anthropic/mcp-client';

async function searchResumes() {
    const client = new MCPClient('hr-resume-search');
    await client.connect();
    
    try {
        // Intelligent candidate search
        const searchResult = await client.callTool('search_candidates', {
            query: 'Senior full-stack developer',
            skills: ['React', 'Node.js', 'TypeScript'],
            companies: ['Google', 'Meta', 'Netflix'],
            min_experience: 5,
            location: 'Remote'
        });
        
        console.log(`Found ${searchResult.total_results} candidates`);
        
        // Process results
        for (const candidate of searchResult.candidates) {
            console.log(`${candidate.name} - Match Score: ${candidate.match_score}`);
            
            // Get detailed insights
            const insights = await client.callTool('get_candidate_insights', {
                candidate_id: candidate.id,
                include_recommendations: true
            });
            
            console.log(`Insights: ${insights.summary}`);
        }
        
    } finally {
        await client.disconnect();
    }
}

searchResumes().catch(console.error);
```

### Claude Conversation Example

```
User: I need to find senior Python developers who have worked at startups and have experience with AI/ML

Claude: I'll help you search for senior Python developers with startup and AI/ML experience using the HR Resume Search MCP server.

[Using search_candidates tool]

I found 18 senior Python developers who match your criteria. Here are the top candidates:

1. **Sarah Chen** (Match Score: 0.94)
   - 8 years experience, currently Senior ML Engineer at TechStartup Inc.
   - Skills: Python, TensorFlow, PyTorch, FastAPI, AWS
   - Previous: Data Scientist at early-stage fintech startup

2. **Mike Rodriguez** (Match Score: 0.89)
   - 7 years experience, Lead Python Developer at AI Innovations
   - Skills: Python, Scikit-learn, Docker, Kubernetes, MLOps
   - Previous: Founding engineer at two successful startups

3. **Alex Kim** (Match Score: 0.87)
   - 6 years experience, Senior Software Engineer at StartupX
   - Skills: Python, Machine Learning, React, PostgreSQL
   - Previous: Early employee at unicorn startup, now Series B

Would you like me to:
1. Find similar profiles to any of these candidates?
2. Discover former colleagues of these candidates?
3. Get more detailed insights about their experience?

User: Yes, please find similar profiles to Sarah Chen and also check if any of these candidates have worked together.

Claude: [Using find_similar_candidates and find_colleagues tools]

Perfect! Here's what I found:

**Similar Profiles to Sarah Chen:**
1. **David Park** (Similarity: 0.91) - Similar ML + startup background, 9 years exp
2. **Lisa Wang** (Similarity: 0.88) - TensorFlow expert, 3 startup exits
3. **James Miller** (Similarity: 0.85) - PyTorch specialist, founding team member

**Colleague Connections:**
- **Sarah Chen & Mike Rodriguez**: Worked together at DataFlow Startup (18 months overlap, 2019-2020)
- **Alex Kim & David Park**: Both at StartupX, different teams (8 months overlap)

This gives you a strong network of connected senior Python developers with proven startup and AI/ML experience!
```

---

## Authentication

### API Key Authentication

```python
# Configure API key for MCP server
import os
os.environ['HR_API_KEY'] = 'your_api_key_here'

# MCP server will automatically use this for API calls
result = await search_candidates(query="Python developer")
```

### JWT Token Authentication

```python
# For user-specific operations
async def authenticate_user(email: str, password: str):
    auth_result = await client.call_tool("authenticate_user", {
        "email": email,
        "password": password
    })
    
    # Store token for subsequent requests
    client.set_auth_token(auth_result['access_token'])
    
    return auth_result

# Use in MCP operations
await authenticate_user("hr@company.com", "secure_password")
candidates = await search_candidates(query="Senior developers")  # Uses authenticated context
```

### Role-Based Access Control

```python
# Check user permissions
permissions = await client.call_tool("get_user_permissions")
print(f"User roles: {permissions['roles']}")
print(f"Can search: {'search:candidates' in permissions['scopes']}")
print(f"Can upload: {'upload:resumes' in permissions['scopes']}")

# Conditional operations based on permissions
if 'admin' in permissions['roles']:
    analytics = await client.call_tool("get_system_analytics")
else:
    print("Admin access required for system analytics")
```

---

## Advanced Usage

### Batch Operations

```python
# Batch candidate search
async def batch_search(search_queries: list):
    tasks = []
    for query in search_queries:
        task = client.call_tool("search_candidates", query)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# Example usage
queries = [
    {"query": "Python developers", "skills": ["Python", "Django"]},
    {"query": "Data scientists", "skills": ["Python", "R", "SQL"]},
    {"query": "DevOps engineers", "skills": ["Docker", "Kubernetes", "AWS"]}
]

batch_results = await batch_search(queries)
for i, result in enumerate(batch_results):
    print(f"Query {i+1}: Found {result['total_results']} candidates")
```

### Custom Search Algorithms

```python
# Implement custom scoring logic
async def custom_candidate_scoring(candidates: list, weights: dict):
    """
    Apply custom scoring weights to candidate results
    weights: {"skills": 0.4, "experience": 0.3, "company": 0.2, "location": 0.1}
    """
    scored_candidates = []
    
    for candidate in candidates:
        custom_score = 0
        
        # Skills matching
        if candidate.get('matching_skills'):
            skills_score = len(candidate['matching_skills']) / len(candidate['total_skills'])
            custom_score += skills_score * weights.get('skills', 0.4)
        
        # Experience matching
        if candidate.get('experience_years'):
            exp_score = min(candidate['experience_years'] / 10, 1.0)  # Normalize to 10 years
            custom_score += exp_score * weights.get('experience', 0.3)
        
        # Company prestige (example scoring)
        prestigious_companies = ['Google', 'Meta', 'Apple', 'Amazon', 'Microsoft']
        if candidate.get('current_company') in prestigious_companies:
            custom_score += weights.get('company', 0.2)
        
        # Location preference
        preferred_locations = ['San Francisco', 'New York', 'Seattle', 'Remote']
        if candidate.get('location') in preferred_locations:
            custom_score += weights.get('location', 0.1)
        
        candidate['custom_score'] = custom_score
        scored_candidates.append(candidate)
    
    # Sort by custom score
    return sorted(scored_candidates, key=lambda x: x['custom_score'], reverse=True)

# Usage example
search_result = await search_candidates(
    query="Senior software engineer",
    skills=["Python", "React", "AWS"],
    limit=50
)

# Apply custom scoring
custom_weights = {
    "skills": 0.5,      # Emphasize skills matching
    "experience": 0.3,
    "company": 0.1,
    "location": 0.1
}

scored_candidates = await custom_candidate_scoring(
    search_result['candidates'], 
    custom_weights
)

print("Top candidates with custom scoring:")
for candidate in scored_candidates[:5]:
    print(f"{candidate['name']}: {candidate['custom_score']:.2f}")
```

### Real-time Search Monitoring

```python
import asyncio
from datetime import datetime

async def monitor_search_performance():
    """Monitor search performance and log metrics"""
    while True:
        try:
            # Get current search metrics
            metrics = await client.call_tool("get_search_metrics", {
                "time_window": "last_hour"
            })
            
            # Log performance data
            print(f"[{datetime.now()}] Search Metrics:")
            print(f"  Total searches: {metrics['search_count']}")
            print(f"  Average response time: {metrics['avg_response_time_ms']}ms")
            print(f"  Success rate: {metrics['success_rate']}%")
            print(f"  Popular skills: {metrics['trending_skills'][:5]}")
            
            # Alert on performance issues
            if metrics['avg_response_time_ms'] > 1000:
                print("⚠️  WARNING: High response times detected")
            
            if metrics['success_rate'] < 95:
                print("⚠️  WARNING: Low success rate detected")
            
            # Wait before next check
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            print(f"Error monitoring search performance: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

# Start monitoring in background
asyncio.create_task(monitor_search_performance())
```

### AI-Enhanced Search Suggestions

```python
async def get_ai_search_suggestions(user_query: str, context: dict = None):
    """
    Use Claude to enhance search queries and suggest better parameters
    """
    
    # Analyze the query with Claude
    analysis_prompt = f"""
    User is searching for: "{user_query}"
    
    Context: {context or "No additional context"}
    
    Please suggest:
    1. Optimized search parameters (skills, experience level, etc.)
    2. Alternative search queries that might yield better results
    3. Filters that would improve relevance
    
    Respond in JSON format with search suggestions.
    """
    
    # Get AI suggestions (this would use Claude through MCP)
    suggestions = await client.call_tool("analyze_search_query", {
        "query": user_query,
        "context": context,
        "prompt": analysis_prompt
    })
    
    return suggestions

# Example usage
user_input = "I need someone for our AI team"
context = {
    "company_size": "startup",
    "location": "San Francisco",
    "budget": "competitive",
    "urgency": "high"
}

suggestions = await get_ai_search_suggestions(user_input, context)
print("AI-Enhanced Search Suggestions:")
print(f"Optimized query: {suggestions['optimized_query']}")
print(f"Suggested skills: {suggestions['skills']}")
print(f"Recommended filters: {suggestions['filters']}")

# Execute the optimized search
optimized_result = await search_candidates(**suggestions['search_params'])
```

---

## Error Handling & Resilience

### Retry Logic

```python
import asyncio
from functools import wraps

def retry_on_failure(max_retries=3, delay=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"All {max_retries} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator

# Apply retry logic to search operations
@retry_on_failure(max_retries=3, delay=2.0)
async def robust_search(query_params):
    return await client.call_tool("search_candidates", query_params)

# Usage
try:
    result = await robust_search({
        "query": "Python developer",
        "skills": ["Python", "FastAPI"],
        "limit": 10
    })
    print(f"Search successful: {result['total_results']} results")
except Exception as e:
    print(f"Search failed after retries: {e}")
```

### Circuit Breaker Pattern

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except self.expected_exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
search_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

async def protected_search(query_params):
    return await search_breaker.call(
        client.call_tool, 
        "search_candidates", 
        query_params
    )
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Errors

**Problem**: Cannot connect to MCP server
```
Error: Connection refused to hr-resume-search MCP server
```

**Solutions**:
```bash
# Check if server is running
ps aux | grep "server.py"

# Check port availability  
netstat -an | grep :8000

# Restart MCP server
python mcp_server/server.py --debug

# Verify configuration
cat ~/.claude/claude_desktop_config.json
```

#### 2. Authentication Failures

**Problem**: API key or JWT token issues
```
Error: 401 Unauthorized - Invalid API key
```

**Solutions**:
```python
# Verify API key
import os
print(f"API Key: {os.getenv('HR_API_KEY', 'NOT_SET')}")

# Test authentication
auth_test = await client.call_tool("test_authentication")
print(f"Auth status: {auth_test['status']}")

# Refresh JWT token
if auth_test['token_expired']:
    await client.call_tool("refresh_auth_token")
```

#### 3. Performance Issues

**Problem**: Slow search responses
```
Warning: Search took 5000ms (expected <1000ms)
```

**Solutions**:
```python
# Enable performance monitoring
await client.call_tool("enable_performance_monitoring", {"detailed": True})

# Check database performance
db_stats = await client.call_tool("get_database_stats")
print(f"Query time: {db_stats['avg_query_time_ms']}ms")
print(f"Connection pool: {db_stats['connection_pool_usage']}")

# Optimize search parameters
optimized_params = await client.call_tool("optimize_search_params", {
    "current_params": search_params,
    "performance_target": "fast"
})
```

#### 4. Tool Not Found Errors

**Problem**: MCP tool not available
```
Error: Tool 'search_candidates' not found
```

**Solutions**:
```python
# List available tools
tools = await client.list_tools()
print("Available tools:", [tool['name'] for tool in tools])

# Refresh tool registry
await client.call_tool("refresh_tools")

# Check tool status
tool_status = await client.call_tool("get_tool_status", {"tool_name": "search_candidates"})
print(f"Tool status: {tool_status}")
```

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('mcp_client')

# Enable MCP debug mode
client = MCPClient('hr-resume-search', debug=True)

# Trace tool calls
async def traced_search(params):
    logger.info(f"Starting search with params: {params}")
    
    try:
        result = await client.call_tool("search_candidates", params)
        logger.info(f"Search completed: {result['total_results']} results in {result['processing_time_ms']}ms")
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise
```

### Health Checks

Implement regular health checks for reliability:

```python
async def health_check():
    """Comprehensive health check for MCP integration"""
    health_status = {
        "mcp_server": False,
        "api_connection": False,
        "database": False,
        "authentication": False
    }
    
    try:
        # Test MCP server
        server_status = await client.call_tool("get_api_status")
        health_status["mcp_server"] = server_status["status"] == "running"
        
        # Test API connection
        api_health = await client.call_tool("test_api_connection")
        health_status["api_connection"] = api_health["connected"]
        
        # Test database
        db_health = await client.call_tool("test_database_connection")
        health_status["database"] = db_health["connected"]
        
        # Test authentication
        auth_health = await client.call_tool("test_authentication")
        health_status["authentication"] = auth_health["valid"]
        
    except Exception as e:
        print(f"Health check error: {e}")
    
    # Report status
    all_healthy = all(health_status.values())
    print(f"System Health: {'✅ Healthy' if all_healthy else '❌ Issues detected'}")
    
    for component, status in health_status.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {component}: {'OK' if status else 'FAILED'}")
    
    return health_status

# Run health check periodically
import asyncio

async def periodic_health_check(interval=300):  # 5 minutes
    while True:
        await health_check()
        await asyncio.sleep(interval)

# Start background health monitoring
asyncio.create_task(periodic_health_check())
```

---

## Production Deployment

### Docker Configuration

Create `Dockerfile` for MCP server:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  hr-api:
    build: ../
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/hr_resume_db
    depends_on:
      - db

  mcp-server:
    build: .
    ports:
      - "8001:8001"
    environment:
      - API_BASE_URL=http://hr-api:8000
      - API_KEY=${API_KEY}
    depends_on:
      - hr-api

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=hr_resume_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Environment Configuration

```bash
# Production environment variables
export API_BASE_URL=https://api.company.com
export API_KEY=prod_api_key_here
export CLAUDE_API_KEY=prod_claude_key
export DATABASE_URL=postgresql://user:password@prod-db:5432/hr_resume_db
export MCP_SERVER_ENV=production
export LOG_LEVEL=INFO
export SENTRY_DSN=your_sentry_dsn
```

---

## Next Steps

1. **Deployment Guide**: See `/docs/deployment.md` for production deployment
2. **Performance Guide**: See `/docs/performance.md` for optimization tips  
3. **API Reference**: See `/docs/api_reference.md` for complete endpoint documentation
4. **Examples**: See `/docs/examples/` for practical integration examples

For advanced MCP development and custom tool creation, refer to the [MCP SDK Documentation](https://github.com/anthropics/mcp) and the project's development guidelines.