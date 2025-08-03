# Testing Guide - HR Resume Search MCP API

## 🧪 Testing Overview

Comprehensive testing strategy ensuring 80%+ code coverage with unit, integration, and end-to-end tests.

## 📋 Test Structure

```
tests/
├── unit/                 # Unit tests (isolated components)
│   ├── test_models.py   # Database model tests
│   ├── test_schemas.py  # Pydantic schema tests
│   ├── test_services.py # Service layer tests
│   └── test_utils.py    # Utility function tests
├── integration/         # Integration tests (component interaction)
│   ├── test_api.py     # API endpoint tests
│   ├── test_auth.py    # Authentication flow tests
│   ├── test_db.py      # Database integration tests
│   └── test_cache.py   # Redis cache tests
├── e2e/                 # End-to-end tests (complete workflows)
│   ├── test_resume_flow.py    # Resume upload/process flow
│   ├── test_search_flow.py    # Search functionality
│   └── test_mcp_flow.py       # MCP server integration
├── performance/         # Performance tests
│   ├── test_load.py    # Load testing
│   └── test_stress.py  # Stress testing
├── fixtures/           # Test data and mocks
│   ├── resumes/       # Sample resume files
│   ├── data.py        # Test data generators
│   └── mocks.py       # Mock objects
└── conftest.py        # Pytest configuration
