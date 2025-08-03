"""
Pytest Configuration and Shared Fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app
from api.database import Base, get_db
from api.config import get_settings

# Override settings for testing
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool,  # Disable connection pooling for tests
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    """Create an authenticated test client"""
    # First create a test user
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    
    # Register user
    await client.post("/api/v1/auth/register", json=user_data)
    
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"]
        }
    )
    
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    
    return client


@pytest.fixture
async def admin_client(client: AsyncClient) -> AsyncClient:
    """Create an admin authenticated test client"""
    # Create admin user (implementation depends on your user creation logic)
    admin_data = {
        "email": "admin@example.com",
        "username": "admin",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "is_superuser": True
    }
    
    # Register admin (you might need a special endpoint or direct DB access)
    await client.post("/api/v1/auth/register", json=admin_data)
    
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_data["email"],
            "password": admin_data["password"]
        }
    )
    
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    
    return client


@pytest.fixture
def test_data_dir() -> Path:
    """Get test data directory"""
    return Path(__file__).parent / "fixtures" / "data"


@pytest.fixture
def sample_resume_pdf(test_data_dir) -> bytes:
    """Load sample resume PDF for testing"""
    pdf_path = test_data_dir / "sample_resume.pdf"
    if not pdf_path.exists():
        # Create a simple PDF for testing if it doesn't exist
        # This is just placeholder content
        return b"%PDF-1.4\n%Test PDF Content\n"
    return pdf_path.read_bytes()


@pytest.fixture
def sample_resume_docx(test_data_dir) -> bytes:
    """Load sample resume DOCX for testing"""
    docx_path = test_data_dir / "sample_resume.docx"
    if not docx_path.exists():
        # Create a simple DOCX for testing if it doesn't exist
        # This is just placeholder content
        return b"PK\x03\x04"  # DOCX file signature
    return docx_path.read_bytes()


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response for resume parsing"""
    return {
        "parsed_resume": {
            "personal_info": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "location": "New York, NY"
            },
            "experience": [
                {
                    "company": "Tech Corp",
                    "position": "Senior Developer",
                    "duration": "2020-2023",
                    "department": "Engineering",
                    "desk": "Platform Team",
                    "responsibilities": [
                        "Developed microservices architecture",
                        "Led team of 5 developers"
                    ]
                }
            ],
            "education": [
                {
                    "institution": "MIT",
                    "degree": "BS Computer Science",
                    "year": "2019"
                }
            ],
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "colleagues": ["Jane Smith", "Bob Johnson"]
        }
    }


@pytest.fixture
async def sample_project(authenticated_client: AsyncClient) -> dict:
    """Create a sample project for testing"""
    project_data = {
        "name": "Test Project",
        "slug": "test-project",
        "description": "A test project for E2E testing"
    }
    
    response = await authenticated_client.post("/api/v1/projects", json=project_data)
    return response.json()


@pytest.fixture
async def sample_endpoint(authenticated_client: AsyncClient, sample_project: dict) -> dict:
    """Create a sample endpoint for testing"""
    endpoint_data = {
        "path": "/test/endpoint",
        "method": "GET",
        "name": "Test Endpoint",
        "description": "A test endpoint",
        "project_id": sample_project["id"],
        "auth_required": True,
        "rate_limit": 100
    }
    
    response = await authenticated_client.post("/api/v1/endpoints", json=endpoint_data)
    return response.json()


# Performance testing fixtures
@pytest.fixture
def performance_threshold():
    """Define performance thresholds for tests"""
    return {
        "api_response_time": 2.0,  # seconds
        "database_query_time": 0.5,  # seconds
        "file_upload_time": 5.0,  # seconds
        "concurrent_requests": 10
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_test_files():
    """Clean up any test files created during tests"""
    yield
    # Cleanup logic here if needed
    test_upload_dir = Path("/tmp/test_uploads")
    if test_upload_dir.exists():
        import shutil
        shutil.rmtree(test_upload_dir)