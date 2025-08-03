# Testing Strategy and Documentation

## Overview

This document outlines the comprehensive testing strategy for the HR Resume Search MCP API, including E2E tests, integration tests, and unit tests. Our target is **80% code coverage** with a focus on critical user journeys and edge cases.

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── e2e/                  # End-to-end tests
│   ├── test_health_endpoints.py     # Health check and monitoring
│   ├── test_authentication_flow.py  # Complete auth workflows
│   ├── test_resume_management.py    # Core business logic
│   ├── test_api_management.py       # Project and endpoint management
│   ├── test_rate_limiting_caching.py # Performance features
│   └── test_edge_cases.py          # Edge cases and error handling
├── integration/          # Integration tests (TODO)
├── unit/                # Unit tests (TODO)
└── fixtures/            # Test data
    └── data/           # Sample files for testing
```

## Test Categories

### 1. E2E Tests (Implemented)

#### Health and Monitoring Tests
- **Purpose**: Verify system health and readiness
- **Coverage**: Root endpoint, health checks, readiness checks, API documentation
- **Key Tests**:
  - Health endpoint returns correct status
  - Readiness check validates all dependencies
  - API documentation is accessible
  - CORS headers are properly configured
  - Response time within 2-second threshold
  - Concurrent health checks handle properly

#### Authentication Flow Tests
- **Purpose**: Test complete authentication user journeys
- **Coverage**: Registration, login, JWT tokens, protected endpoints, logout
- **Key Tests**:
  - User registration with validation
  - Login with email/username
  - JWT token generation and validation
  - Protected endpoint access control
  - Token refresh mechanism
  - Duplicate registration prevention
  - Invalid credential handling

#### Resume Management Tests (Core Business Logic)
- **Purpose**: Test resume upload, parsing, and search functionality
- **Coverage**: File uploads, Claude AI integration, search capabilities, MCP integration
- **Key Tests**:
  - PDF and DOCX file upload
  - Resume parsing with Claude API
  - Search for similar candidates
  - Department/desk matching
  - Professional network discovery
  - Pagination and performance
  - Smart search with MCP integration

#### API Management Tests
- **Purpose**: Test project and endpoint management
- **Coverage**: CRUD operations for projects and endpoints
- **Key Tests**:
  - Project creation and listing
  - Endpoint creation with schemas
  - API key management
  - Permission enforcement
  - Slug uniqueness validation
  - OpenAPI documentation generation

#### Rate Limiting and Caching Tests
- **Purpose**: Test performance optimization features
- **Coverage**: Rate limiting, caching, performance improvements
- **Key Tests**:
  - Rate limit enforcement per user
  - Rate limit headers in responses
  - Rate limit reset after time window
  - Cache hit optimization
  - Cache invalidation on updates
  - Conditional requests with ETags
  - Performance improvements from caching

#### Edge Cases and Error Handling Tests
- **Purpose**: Test system resilience and error handling
- **Coverage**: Boundary conditions, malformed input, service failures
- **Key Tests**:
  - Empty search results handling
  - Maximum file size uploads
  - SQL injection prevention
  - Special character handling
  - Malformed JSON requests
  - Database connection failures
  - External service failures
  - Unicode character support
  - Pagination edge cases

### 2. Integration Tests (TODO)

- Database integration tests
- Redis integration tests
- Claude API integration tests
- MCP server integration tests

### 3. Unit Tests (TODO)

- Model validation tests
- Service layer tests
- Utility function tests
- Authentication logic tests

## Running Tests

### Prerequisites

```bash
# Install Python 3.12 (REQUIRED)
export UV_PYTHON=/opt/homebrew/bin/python3.12

# Create virtual environment
uv venv --python /opt/homebrew/bin/python3.12
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

### Environment Setup

Create a `.env.test` file for test configuration:

```bash
# Test Database
DATABASE_URL=postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
REDIS_URL=redis://localhost:6379/1

# Test Configuration
ENVIRONMENT=testing
JWT_SECRET_KEY=test-secret-key-for-testing-only
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Disable external services for testing
CLAUDE_API_ENABLED=false
MCP_SERVER_ENABLED=false
```

### Running All Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test category
pytest tests/e2e/ -v
pytest tests/integration/ -v
pytest tests/unit/ -v

# Run specific test file
pytest tests/e2e/test_health_endpoints.py -v

# Run specific test
pytest tests/e2e/test_health_endpoints.py::TestHealthEndpoints::test_root_endpoint -v
```

### Running E2E Tests Only

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run E2E tests with markers
pytest -m "e2e" -v

# Run E2E tests in parallel (faster)
pytest tests/e2e/ -n auto -v
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=api --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html

# Check coverage threshold (80%)
pytest tests/ --cov=api --cov-fail-under=80
```

## Test Fixtures

### Authentication Fixtures
- `client`: Basic test client
- `authenticated_client`: Client with user authentication
- `admin_client`: Client with admin privileges

### Data Fixtures
- `sample_resume_pdf`: Sample PDF file for testing
- `sample_resume_docx`: Sample DOCX file for testing
- `mock_claude_response`: Mocked Claude API response
- `sample_project`: Pre-created project for testing
- `sample_endpoint`: Pre-created endpoint for testing

### Performance Fixtures
- `performance_threshold`: Performance requirements
  - API response time: 2.0 seconds
  - Database query time: 0.5 seconds
  - File upload time: 5.0 seconds
  - Concurrent requests: 10

## Test Markers

```python
# Mark tests with categories
@pytest.mark.e2e  # End-to-end tests
@pytest.mark.integration  # Integration tests
@pytest.mark.unit  # Unit tests
@pytest.mark.slow  # Slow tests (>1 second)
@pytest.mark.critical  # Critical path tests
```

## Performance Testing

### Load Testing

```bash
# Run performance tests
pytest tests/e2e/ -k "performance" -v

# Use locust for load testing (TODO)
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### Concurrent Testing

Tests verify the system can handle:
- 10+ concurrent requests
- 5+ concurrent file uploads
- Multiple users accessing simultaneously

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements.txt
          uv pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest tests/ --cov=api --cov-fail-under=80
```

## Debugging Tests

### Verbose Output

```bash
# Run with verbose output
pytest tests/e2e/ -vv

# Show print statements
pytest tests/e2e/ -s

# Show local variables on failure
pytest tests/e2e/ -l
```

### Debugging Specific Failures

```bash
# Stop on first failure
pytest tests/e2e/ -x

# Enter debugger on failure
pytest tests/e2e/ --pdb

# Run last failed tests
pytest tests/e2e/ --lf
```

## Test Maintenance

### Adding New Tests

1. Create test file in appropriate directory
2. Follow naming convention: `test_*.py`
3. Use appropriate fixtures from `conftest.py`
4. Add markers for test categorization
5. Update this documentation

### Updating Existing Tests

1. Run tests before making changes
2. Update test logic
3. Verify coverage remains above 80%
4. Update documentation if needed

## Known Issues and TODOs

### Implementation TODOs
- Most endpoints are not yet implemented (marked with TODO comments)
- Authentication system needs to be built
- File upload functionality pending
- Claude API integration pending
- MCP server integration pending
- Rate limiting implementation needed
- Caching system needs implementation

### Test TODOs
- Integration tests need to be written
- Unit tests need to be written
- Load testing with Locust
- Security testing suite
- Performance benchmarking

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Use descriptive assertion messages
3. **Fixtures**: Reuse fixtures for common setup
4. **Mocking**: Mock external services appropriately
5. **Performance**: Keep tests fast (<1 second when possible)
6. **Documentation**: Document complex test logic
7. **Coverage**: Maintain 80%+ code coverage

## Contact

For questions about testing strategy or implementation, please refer to the project documentation or contact the development team.