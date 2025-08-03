# Quick Start Guide - HR Resume Search MCP API

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.12 (REQUIRED - DO NOT USE Python 3.13)
- PostgreSQL 14+
- Redis 6+
- uv package manager
- Docker & Docker Compose (optional)

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/your-org/hr_resume_search_mcp.git
cd hr_resume_search_mcp

# Run the setup
make setup

# Start the application
make dev
```

That's it! The API is now running at `http://localhost:8000`

## 📋 Step-by-Step Setup

### 1. Install Python 3.12

```bash
# macOS with Homebrew
brew install python@3.12

# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv

# Verify installation
python3.12 --version
# Should output: Python 3.12.x
```

### 2. Install uv Package Manager

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Verify installation
uv --version
```

### 3. Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/your-org/hr_resume_search_mcp.git
cd hr_resume_search_mcp

# Set Python path
export UV_PYTHON=/opt/homebrew/bin/python3.12  # Adjust path as needed

# Create virtual environment
uv venv --python /opt/homebrew/bin/python3.12

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hr_resume_db

# Redis
REDIS_URL=redis://localhost:6379

# JWT Secret (generate a secure key)
JWT_SECRET_KEY=your-super-secret-key-here

# Claude API (for resume parsing)
CLAUDE_API_KEY=your-claude-api-key
```

### 5. Setup Database

```bash
# Using Docker (recommended)
docker-compose up -d postgres redis

# Or install locally
# PostgreSQL: https://www.postgresql.org/download/
# Redis: https://redis.io/download

# Create database
createdb hr_resume_db

# Run migrations
alembic upgrade head

# Load sample data (optional)
python scripts/load_sample_data.py
```

### 6. Start the Application

```bash
# Development mode with auto-reload
make dev

# Or directly with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "service": "api-builder",
  "version": "1.0.0"
}

# View API documentation
open http://localhost:8000/docs
```

## 🐳 Docker Setup (Alternative)

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/hr_resume_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=hr_resume_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## 🧪 Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test type
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run MCP server tests
make mcp-test-comprehensive
```

## 🔧 Common Make Commands

```bash
make help          # Show all available commands
make setup         # Complete project setup
make dev           # Run in development mode
make test          # Run all tests
make lint          # Run code linting
make format        # Format code
make clean         # Clean generated files
make docker-build  # Build Docker image
make docker-run    # Run in Docker
```

## 📝 First API Call

### 1. Get Authentication Token

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'

# Save the token
export TOKEN="<your-jwt-token>"
```

### 2. Upload a Resume

```bash
# Upload a PDF resume
curl -X POST http://localhost:8000/api/v1/resumes/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_resume.pdf"
```

### 3. Search Resumes

```bash
# Search for Python developers
curl -X GET "http://localhost:8000/api/v1/resumes/search?q=python&skills[]=Python" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔌 MCP Server Setup

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hr-resume-search": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/hr_resume_search_mcp",
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/hr_resume_db",
        "REDIS_URL": "redis://localhost:6379"
      }
    }
  }
}
```

### Test MCP Server

```bash
# Start MCP server standalone
python -m mcp_server.server

# In another terminal, test with MCP client
mcp-client test hr-resume-search
```

## 🌐 Using the Web UI

If you have the frontend application:

```bash
# Install frontend dependencies
cd frontend
npm install

# Start development server
npm run dev

# Open browser
open http://localhost:3000
```

## 📊 Monitoring Setup

### Start Monitoring Stack

```bash
# Using shared infrastructure
cd /Users/petermager/Downloads/code/create_staging
make up

# Access services
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

### View Metrics

1. Open Grafana: `http://localhost:3000`
2. Login with `admin/admin`
3. Import dashboard from `monitoring/dashboards/api-metrics.json`
4. View real-time metrics

## 🐛 Troubleshooting

### Common Issues

#### Python Version Error
```bash
# Error: Python 3.13 not supported
# Solution: Ensure Python 3.12 is used
export UV_PYTHON=/opt/homebrew/bin/python3.12
uv venv --python /opt/homebrew/bin/python3.12
```

#### Database Connection Error
```bash
# Error: could not connect to database
# Solution: Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL if needed
brew services start postgresql@14  # macOS
sudo systemctl start postgresql    # Linux
```

#### Redis Connection Error
```bash
# Error: Could not connect to Redis
# Solution: Check Redis is running
redis-cli ping

# Start Redis if needed
brew services start redis  # macOS
sudo systemctl start redis # Linux
```

#### Port Already in Use
```bash
# Error: Address already in use
# Solution: Find and kill process
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8001
```

#### Module Import Error
```bash
# Error: ModuleNotFoundError
# Solution: Ensure virtual environment is activated
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 📚 Next Steps

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run Tests**
   ```bash
   make test
   make lint
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature
   # Create pull request on GitHub
   ```

### Useful Resources

- [API Documentation](./api.md) - Complete API reference
- [Architecture Guide](./architecture.md) - System design details
- [Implementation Plan](./implementation_plan.md) - Development roadmap
- [Testing Guide](./docs/testing.md) - Testing strategies
- [Deployment Guide](./docs/deployment.md) - Production deployment

### Getting Help

- Check the [Troubleshooting Guide](./docs/troubleshooting.md)
- Review [Common Issues](https://github.com/your-org/hr_resume_search_mcp/issues)
- Join our [Slack Channel](#)
- Email: support@example.com

## 🎯 Quick Command Reference

```bash
# Development
make dev                # Start development server
make test              # Run tests
make lint              # Check code quality
make format            # Format code

# Database
make db-migrate        # Run migrations
make db-seed           # Load sample data
make db-reset          # Reset database

# Docker
make docker-build      # Build image
make docker-run        # Run container
make docker-compose    # Start all services

# MCP
make mcp-test          # Test MCP server
make mcp-run           # Run MCP server

# Monitoring
make metrics           # View Prometheus metrics
make logs              # View application logs
make dashboard         # Open Grafana
```

## ✅ Checklist

Before going to production:

- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Redis cache configured
- [ ] Claude API key set
- [ ] JWT secret key generated
- [ ] Tests passing (80%+ coverage)
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Backups configured
- [ ] Security review completed