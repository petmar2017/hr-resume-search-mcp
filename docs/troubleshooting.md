# Troubleshooting Guide - HR Resume Search MCP API

## 🔍 Common Issues and Solutions

### Installation Issues

#### Python Version Error
**Problem**: `ERROR: Python 3.13 is not supported`

**Solution**:
```bash
# Ensure Python 3.12 is installed
python3.12 --version

# Set UV to use Python 3.12
export UV_PYTHON=/opt/homebrew/bin/python3.12

# Create virtual environment with correct Python
uv venv --python /opt/homebrew/bin/python3.12
```

#### Package Installation Failures
**Problem**: `pydantic-core compilation error with Python 3.13`

**Solution**:
```bash
# Use Python 3.12 exclusively
# Ensure pydantic version is 2.5.2, not 3.0
pip install pydantic==2.5.2
```

### Database Issues

#### Connection Refused
**Problem**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
brew services start postgresql@14  # macOS
sudo systemctl start postgresql    # Linux
docker-compose up -d postgres      # Docker

# Verify connection
psql -U postgres -h localhost -c "SELECT 1"
```

#### Migration Errors
**Problem**: `alembic.util.exc.CommandError`

**Solution**:
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head

# If corrupted, recreate database
dropdb hr_resume_db
createdb hr_resume_db
alembic upgrade head
```

### Redis Issues

#### Connection Error
**Problem**: `redis.exceptions.ConnectionError`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis # Linux
docker-compose up -d redis # Docker

# Test connection
redis-cli SET test "hello"
redis-cli GET test
```

### API Issues

#### Port Already in Use
**Problem**: `[Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8001
```

#### CORS Errors
**Problem**: `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solution**:
```python
# Update CORS settings in .env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# Or allow all origins in development
CORS_ORIGINS=["*"]
```

### Authentication Issues

#### JWT Token Invalid
**Problem**: `Invalid authentication credentials`

**Solution**:
```bash
# Regenerate JWT secret
openssl rand -hex 32

# Update .env
JWT_SECRET_KEY=<new_secret>

# Restart application
make dev
```

#### Token Expired
**Problem**: `Token has expired`

**Solution**:
```python
# Increase token expiration in .env
ACCESS_TOKEN_EXPIRE_MINUTES=60  # Default is 30

# Or implement refresh token flow
POST /api/v1/auth/refresh
```

### File Upload Issues

#### File Too Large
**Problem**: `413 Request Entity Too Large`

**Solution**:
```python
# Increase max file size in config
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB

# For nginx, update nginx.conf
client_max_body_size 20M;
```

#### Unsupported File Format
**Problem**: `File format not supported`

**Solution**:
```python
# Ensure file is PDF, DOC, or DOCX
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx'}

# Convert other formats before upload
libreoffice --convert-to pdf document.odt
```

### Claude API Issues

#### Rate Limit Exceeded
**Problem**: `Claude API rate limit exceeded`

**Solution**:
```python
# Implement exponential backoff
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_claude_api():
    # API call here
    pass
```

#### API Key Invalid
**Problem**: `Invalid Claude API key`

**Solution**:
```bash
# Verify API key
echo $CLAUDE_API_KEY

# Update .env with correct key
CLAUDE_API_KEY=sk-ant-api03-...

# Restart application
make dev
```

### MCP Server Issues

#### MCP Connection Failed
**Problem**: `Failed to connect to MCP server`

**Solution**:
```bash
# Start MCP server manually
python -m mcp_server.server

# Check Claude Desktop config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Verify MCP server is in config
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/project"
    }
  }
}
```

### Performance Issues

#### Slow Response Times
**Problem**: API responses taking >2 seconds

**Solution**:
```bash
# Enable caching
REDIS_URL=redis://localhost:6379

# Add database indexes
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_skills_name ON skills(name);

# Optimize queries
# Use select_related() and prefetch_related() in Django
# Use joinedload() in SQLAlchemy
```

#### High Memory Usage
**Problem**: Application consuming excessive memory

**Solution**:
```python
# Limit connection pool size
DATABASE_POOL_SIZE=10  # Default 20
DATABASE_MAX_OVERFLOW=20  # Default 40

# Enable query result streaming
# Use server-side cursors for large result sets
```

### Docker Issues

#### Build Failures
**Problem**: Docker build failing

**Solution**:
```bash
# Clear Docker cache
docker system prune -a

# Build with no cache
docker build --no-cache -t hr-resume-api .

# Check Docker resources
docker system df
```

#### Container Crashes
**Problem**: Container exits immediately

**Solution**:
```bash
# Check logs
docker logs <container_id>

# Run with interactive shell
docker run -it hr-resume-api /bin/bash

# Increase memory limits
docker run -m 1g hr-resume-api
```

### Testing Issues

#### Tests Failing
**Problem**: pytest tests failing

**Solution**:
```bash
# Run tests verbosely
pytest -vvs

# Run specific test
pytest tests/unit/test_models.py::test_candidate_model

# Clear test cache
pytest --cache-clear
```

#### Coverage Below Target
**Problem**: Test coverage below 80%

**Solution**:
```bash
# Generate coverage report
pytest --cov=api --cov-report=html

# Open report
open htmlcov/index.html

# Add missing tests for uncovered lines
```

## 🛠️ Debugging Tools

### Application Debugging

```python
# Enable debug mode
DEBUG=true

# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")

# Use debugger
import pdb; pdb.set_trace()
```

### Database Debugging

```sql
-- Check active connections
SELECT pid, usename, application_name, client_addr, state
FROM pg_stat_activity
WHERE datname = 'hr_resume_db';

-- Kill stuck queries
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'hr_resume_db' AND state = 'idle';

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM candidates WHERE email = 'test@example.com';
```

### Network Debugging

```bash
# Check port availability
netstat -an | grep 8000

# Test API endpoint
curl -v http://localhost:8000/health

# Monitor network traffic
tcpdump -i lo0 port 8000
```

## 📞 Getting Help

### Resources
- [GitHub Issues](https://github.com/your-org/hr_resume_search_mcp/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/fastapi)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Support Channels
- Slack: #hr-resume-api
- Email: support@example.com
- Discord: [Join Server](https://discord.gg/example)

### Reporting Issues

When reporting issues, include:
1. Error message and stack trace
2. Steps to reproduce
3. Environment details (OS, Python version)
4. Configuration (.env values, without secrets)
5. Relevant logs

Example issue template:
```markdown
**Description**: Brief description of the issue

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Environment**:
- OS: macOS 13.0
- Python: 3.12.0
- FastAPI: 0.104.1
- PostgreSQL: 14.5

**Logs**:
```
[paste relevant logs here]
```
```