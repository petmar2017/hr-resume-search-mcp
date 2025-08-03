# AG-UI Streaming MCP Server for HR Resume Search

A thin proxy layer MCP server with streaming responses for real-time user experience, connecting to the FastAPI backend.

## Overview

This MCP server provides a streaming interface to the HR Resume Search FastAPI backend, delivering real-time updates and progress indicators for search operations and file processing.

### Key Features

- **🔄 Real-time Streaming**: Progressive results with visual progress indicators
- **🔗 Thin Proxy Pattern**: All business logic stays in FastAPI backend  
- **🚀 High Performance**: Connection pooling, caching, and optimization
- **🔐 Authentication Passthrough**: Seamless JWT token management
- **⚡ AG-UI Integration**: Enhanced UI streaming support
- **📊 Progress Tracking**: Visual progress bars and status updates

## Architecture

```
Claude Desktop ↔ MCP Server (Streaming Proxy) ↔ FastAPI Backend ↔ PostgreSQL
```

The MCP server acts as a streaming proxy that:
1. Receives requests from Claude Desktop  
2. Proxies them to FastAPI endpoints
3. Streams responses back with progress updates
4. Provides real-time user experience

## Available Tools

### Authentication
- `authenticate_user(email, password)` - Login and set session token
- `check_api_status()` - Verify FastAPI backend health

### Search Operations  
- `search_candidates(query, filters...)` - Multi-criteria candidate search with streaming results
- `search_similar(candidate_id, limit)` - Find similar profiles with match scoring
- `search_colleagues(candidate_id, limit)` - Find former colleagues with overlap details
- `get_search_filters()` - Get available filters and statistics

### Resume Management
- `upload_resume(file_name, content, metadata...)` - Upload and process resume with progress
- `get_resume(resume_id)` - Get detailed resume information

## Installation & Setup

### 1. Install Dependencies

```bash
cd mcp_server
pip install -r requirements-ag-ui.txt
```

### 2. Configure Environment

Create `.env` file:
```bash
# FastAPI Backend
FASTAPI_BASE_URL=http://localhost:8000

# Streaming Configuration  
MCP_STREAMING_ENABLED=true
MCP_CHUNK_DELAY_MS=100
MCP_MAX_CHUNK_SIZE=3
MCP_PROGRESS_INDICATORS=true

# Performance
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3
MCP_ENABLE_CACHING=true
MCP_MAX_POOL_CONNECTIONS=20

# Security
MCP_VERIFY_SSL=true
MCP_MAX_REQUEST_SIZE=10485760

# Logging
LOG_LEVEL=INFO
LOG_STRUCTURED=false
```

### 3. Configure Claude Desktop

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "hr-resume-search-streaming": {
      "command": "python",
      "args": ["-m", "mcp_server.ag_ui_server"],
      "env": {
        "FASTAPI_BASE_URL": "http://localhost:8000",
        "PYTHONPATH": "."
      }
    }
  }
}
```

### 4. Start the Server

Make sure FastAPI backend is running first:
```bash
# Terminal 1: Start FastAPI  
cd api
python -m uvicorn main:app --reload

# Terminal 2: Test MCP server
cd mcp_server
python ag_ui_server.py
```

## Usage Examples

### 1. Basic Search with Streaming

```python
# Search for Python developers - results stream progressively
await search_candidates(
    query="Python developers with FastAPI experience", 
    search_type="skills_match",
    skills=["Python", "FastAPI"],
    min_experience_years=3,
    limit=10
)
```

**Streaming Output:**
```
🔍 **Search Progress Update**
📊 **Progress:** 0% [░░░░░░░░░░░░░░░░░░░░]
📈 **Found 24 candidates matching your criteria**
📊 **Progress:** 30% [██████░░░░░░░░░░░░░░]
👤 **John Doe** - Skills: Python, FastAPI, Docker...
👤 **Jane Smith** - Skills: Python, React, PostgreSQL...
📊 **Progress:** 100% [████████████████████]
✅ **Search completed successfully!**
```

### 2. Authentication Flow

```python
# Login and establish session
await authenticate_user("hr@company.com", "password")
```

**Output:**
```
✅ **Authentication successful!** You can now use all HR search tools.
🔑 **Session expires in:** 1800 seconds
```

### 3. Finding Similar Profiles

```python
# Find candidates similar to John Doe
await search_similar("candidate-uuid-123", limit=5)
```

**Streaming Output:**
```
🔍 **Similarity Search Update**
👤 **Alice Johnson** - Match: 92% [🟢🟢🟢🟢🟢🟢🟢🟢🟢⚪]
👤 **Bob Wilson** - Match: 85% [🟢🟢🟢🟢🟢🟢🟢🟢⚪⚪]
```

### 4. Resume Upload with Progress

```python
# Upload resume with real-time processing status
await upload_resume(
    file_name="john_doe_resume.pdf",
    file_content="<base64-content>",
    candidate_name="John Doe"
)
```

**Streaming Output:**
```
📄 **Starting upload of john_doe_resume.pdf...**
📤 **Upload Progress**
🤖 **Claude AI is analyzing the resume...**
✅ **Resume processed successfully!**
```

## Configuration Reference

### Streaming Settings

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_STREAMING_ENABLED` | `true` | Enable streaming responses |
| `MCP_CHUNK_DELAY_MS` | `100` | Delay between chunks (ms) |
| `MCP_MAX_CHUNK_SIZE` | `3` | Max items per chunk |
| `MCP_PROGRESS_INDICATORS` | `true` | Show progress bars |

### Performance Settings

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_TIMEOUT` | `30` | Request timeout (seconds) |
| `MCP_MAX_RETRIES` | `3` | Max retry attempts |
| `MCP_MAX_POOL_CONNECTIONS` | `20` | HTTP connection pool size |
| `MCP_ENABLE_CACHING` | `true` | Enable response caching |

### Security Settings

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_VERIFY_SSL` | `true` | Verify SSL certificates |
| `MCP_MAX_REQUEST_SIZE` | `10485760` | Max request size (bytes) |
| `MCP_RATE_LIMIT_REQUESTS` | `100` | Rate limit (per minute) |

## Troubleshooting

### Common Issues

**1. Connection Refused**
```
❌ **API Health Check Failed:** Cannot connect to FastAPI server
Make sure FastAPI server is running on http://localhost:8000
```
**Solution:** Start FastAPI backend first

**2. Authentication Errors**
```
❌ **Authentication Error:** 401 Unauthorized
```
**Solution:** Use `authenticate_user()` tool first

**3. Slow Streaming**
```
# Adjust chunk delay for faster streaming
MCP_CHUNK_DELAY_MS=50
```

**4. Timeout Issues**
```
# Increase timeout for large operations
MCP_TIMEOUT=60
```

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG
LOG_STRUCTURED=true
```

### Health Checks

Test connectivity:
```python
await check_api_status()
```

Expected output:
```
✅ **FastAPI backend is healthy and ready!**
📋 **Service:** API Builder
🔧 **Version:** 1.0.0
```

## Development

### Adding New Tools

1. Add tool function to `ag_ui_server.py`:
```python
@app.tool()
async def new_tool(param: str) -> List[TextContent]:
    """New tool description"""
    async with StreamingAPIClient(config.api_proxy.base_url) as client:
        async for chunk in client.stream_request("GET", "/new-endpoint"):
            # Process streaming response
            yield chunk
```

2. Update documentation and tests

### Performance Optimization

- **Connection Pooling**: Configured automatically
- **Caching**: Enable with `MCP_ENABLE_CACHING=true`
- **Compression**: Enable with `MCP_ENABLE_COMPRESSION=true`
- **HTTP/2**: Enable with `MCP_ENABLE_HTTP2=true`

## License

Same license as the main HR Resume Search project.