# HR Resume Search MCP - Jupyter Notebooks

This directory contains interactive Jupyter notebooks for testing, analyzing, and demonstrating the HR Resume Search MCP API.

## 📚 Notebook Categories

### 1. API Testing (`api_testing/`)
Interactive notebooks for testing all API endpoints with real examples.

- `01_api_health_checks.ipynb` - Health endpoint testing and monitoring
- `02_authentication_flow.ipynb` - JWT authentication testing
- `03_resume_upload_test.ipynb` - File upload and processing tests
- `04_search_queries.ipynb` - Search functionality testing
- `05_crud_operations.ipynb` - Complete CRUD operation examples

### 2. Data Analysis (`data_analysis/`)
Notebooks for analyzing resume data and search patterns.

- `01_resume_parser_analysis.ipynb` - Claude API parsing results analysis
- `02_search_patterns.ipynb` - Search query pattern analysis
- `03_candidate_matching.ipynb` - Matching algorithm visualization
- `04_data_quality.ipynb` - Data quality and validation checks

### 3. Performance Testing (`performance/`)
Load testing and performance analysis notebooks.

- `01_load_testing.ipynb` - API load testing with visualizations
- `02_response_time_analysis.ipynb` - Response time analysis
- `03_concurrent_requests.ipynb` - Concurrent request testing
- `04_memory_profiling.ipynb` - Memory usage profiling

### 4. Tutorials (`tutorials/`)
Step-by-step tutorials for using the API.

- `01_getting_started.ipynb` - Quick start guide
- `02_authentication_guide.ipynb` - Authentication walkthrough
- `03_resume_processing.ipynb` - Resume upload and processing guide
- `04_advanced_search.ipynb` - Advanced search techniques

## 🚀 Getting Started

### Prerequisites

1. Install Jupyter and dependencies:
```bash
make install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the API server:
```bash
make dev
```

### Running Notebooks

Start Jupyter Lab:
```bash
make jupyter
```

Or Jupyter Notebook:
```bash
make notebook
```

## 📊 Key Features

### Interactive API Testing
- Live API endpoint testing
- Request/response visualization
- Error handling demonstrations
- Performance metrics

### Data Visualization
- Search result visualization
- Resume data distribution
- Performance charts
- Real-time monitoring

### Automated Testing
- Batch endpoint testing
- Performance benchmarking
- Data validation
- Report generation

## 🛠️ Utility Functions

Common utility functions available in notebooks:

```python
from notebook_utils import (
    get_api_client,      # Configured API client
    authenticate,        # Get JWT token
    upload_resume,       # Upload resume file
    search_candidates,   # Search for candidates
    visualize_results,   # Visualize search results
    generate_report      # Generate test report
)
```

## 📝 Best Practices

1. **Environment Setup**: Always load environment variables at the start
2. **Error Handling**: Use try-except blocks for API calls
3. **Visualization**: Use plotly for interactive charts
4. **Documentation**: Include markdown cells explaining each step
5. **Reproducibility**: Set random seeds where applicable

## 🔧 Troubleshooting

### Common Issues

**API Connection Error**
- Ensure API server is running: `make dev`
- Check API_HOST and API_PORT in .env

**Authentication Failed**
- Verify JWT_SECRET_KEY in .env
- Check token expiration settings

**Import Errors**
- Run from project root: `cd workspace`
- Install dependencies: `make install`

## 📈 Example Usage

### Quick API Test
```python
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

API_URL = f"http://{os.getenv('API_HOST')}:{os.getenv('API_PORT')}"

# Test health endpoint
response = httpx.get(f"{API_URL}/health")
print(response.json())
```

### Authentication Flow
```python
# Login
login_data = {"email": "test@example.com", "password": "password123"}
response = httpx.post(f"{API_URL}/api/v1/auth/login", json=login_data)
token = response.json()["access_token"]

# Use token
headers = {"Authorization": f"Bearer {token}"}
response = httpx.get(f"{API_URL}/api/v1/resumes", headers=headers)
```

## 📚 Additional Resources

- [API Documentation](../api.md)
- [Implementation Plan](../implementation_plan.md)
- [Architecture Guide](../architecture.md)
- [Testing Strategy](../docs/testing.md)

## 🤝 Contributing

When adding new notebooks:
1. Follow naming convention: `XX_description.ipynb`
2. Include comprehensive markdown documentation
3. Add to appropriate category directory
4. Update this README
5. Test with fresh kernel

---

**Last Updated**: 2024-12-17  
**Version**: 1.0.0