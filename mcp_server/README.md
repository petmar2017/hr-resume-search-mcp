# HR Resume Search MCP Server

Model Context Protocol (MCP) server for intelligent HR resume search and analysis.

## Overview

This MCP server provides advanced tools for searching, analyzing, and managing resumes with intelligent features like:
- Similar candidate discovery
- Department and team-based search
- Professional network analysis
- Natural language query processing
- Colleague relationship mapping

## Features

### Core Capabilities
- **Smart Search**: Natural language queries for complex resume searches
- **Similarity Matching**: Find candidates similar to existing profiles
- **Network Analysis**: Discover professional relationships and team structures
- **Department Search**: Find candidates by department/desk/team
- **Colleague Discovery**: Identify people who worked together

### API Development Tools
- FastAPI endpoint generation
- Pydantic model creation
- Test suite generation
- API documentation builder
- Database migration tools

### HR-Specific Tools
- Resume parsing (PDF, DOCX, DOC)
- Standardized JSON transformation
- Skill extraction and matching
- Experience timeline analysis
- Professional network mapping

## Installation

### Prerequisites
- Python 3.12 (MANDATORY - not 3.13)
- PostgreSQL 14+
- Redis 6+
- Claude API key for resume parsing

### Setup

1. **Create virtual environment**:
```bash
export UV_PYTHON=/opt/homebrew/bin/python3.12
uv venv --python /opt/homebrew/bin/python3.12
source .venv/bin/activate
```

2. **Install dependencies**:
```bash
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize database**:
```bash
make setup-db
make migrate
```

## Configuration

### Environment Variables

```bash
# Application
APP_NAME=hr-resume-search
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hr_resumes
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PREFIX=hr_search:

# Claude API
CLAUDE_API_KEY=your-api-key-here

# MCP Server
MCP_HOST=localhost
MCP_PORT=8080
```

### Claude Desktop Configuration

Add to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "PYTHONPATH": "/path/to/workspace",
        "DATABASE_URL": "postgresql://...",
        "CLAUDE_API_KEY": "${CLAUDE_API_KEY}"
      }
    }
  }
}
```

## Usage

### Starting the Server

```bash
# Development mode
make mcp-dev

# Production mode
make mcp-run

# With Docker
make docker-run
```

### Available Tools

#### Resume Search Tools

1. **search_similar_resumes**
   - Find candidates similar to a reference profile
   - Match by skills, department, company, or role
   - Returns ranked results with match scores

2. **search_by_department**
   - Find all candidates from specific departments
   - Filter by company and date range
   - Useful for team reconstruction

3. **find_colleagues**
   - Discover who worked with a candidate
   - Shows overlap periods and shared projects
   - Maps professional networks

4. **smart_query_resumes**
   - Natural language search interface
   - Examples: "Python developers with 5+ years in fintech"
   - Automatic query interpretation

5. **analyze_resume_network**
   - Build professional relationship graphs
   - Identify key connectors and clusters
   - Analyze team dynamics

#### API Development Tools

1. **create_endpoint** - Generate FastAPI endpoints
2. **create_model** - Create Pydantic models
3. **generate_test** - Build test suites
4. **generate_api_docs** - Create API documentation
5. **create_migration** - Generate database migrations

## Testing

### Run Tests

```bash
# All tests
make test

# With coverage
make test-coverage

# MCP-specific tests
make mcp-test-comprehensive

# Performance tests
make mcp-test-performance
```

### Test Coverage Requirements
- Overall: 80%
- Core tools: 90%
- HR tools: 85%
- Integration: 75%

## API Documentation

### Generated Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI spec: http://localhost:8000/openapi.json

### Tool Documentation
Each MCP tool is self-documenting. Use `list_available_tools()` to get all available tools and their descriptions.

## Development

### Project Structure
```
mcp_server/
├── server.py           # Main MCP server
├── hr_tools.py         # HR-specific tools
├── models/             # Data models
├── database/           # Database utilities
├── parsers/            # Resume parsers
├── tests/              # Test suite
├── templates/          # Code templates
└── hr_database/        # JSON database
```

### Adding New Tools

1. Define tool in appropriate module
2. Register with MCP server
3. Add tests
4. Update documentation

Example:
```python
@app.tool()
async def new_tool(param: str) -> Dict[str, Any]:
    """Tool description"""
    # Implementation
    return result
```

## Monitoring

### Metrics
- Prometheus metrics at `/metrics`
- Grafana dashboards for visualization
- Performance tracking for all tools

### Logging
- Structured JSON logging
- Dual format (console + Loki)
- Request/response tracking

## Deployment

### Docker

```bash
# Build image
make docker-build

# Run container
make docker-run

# Deploy to Kubernetes
make deploy
```

### Kubernetes

```yaml
# See k8s/deployment.yaml for configuration
kubectl apply -f k8s/
```

## Troubleshooting

### Common Issues

1. **Python Version Issues**
   - Ensure Python 3.12 is used (not 3.13)
   - Check with: `python --version`

2. **MCP Connection Failed**
   - Verify server is running
   - Check Claude Desktop config
   - Review logs: `tail -f logs/mcp.log`

3. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string
   - Test with: `make test-db-connection`

4. **Performance Issues**
   - Check Redis connectivity
   - Review query optimization
   - Monitor with: `make monitor-performance`

## Contributing

1. Follow Python standards (PEP 8)
2. Write tests for new features
3. Update documentation
4. Use meaningful commit messages
5. Create feature branches

## License

Proprietary - See LICENSE file

## Support

For issues or questions:
- Create GitHub issue
- Check troubleshooting guide
- Review logs in `logs/` directory