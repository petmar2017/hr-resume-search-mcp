"""
Test Data Factories using Factory Boy
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
import uuid
import json

from api.models import User, Candidate, Resume, WorkExperience, Project, Endpoint, APIKey


class UserFactory(factory.Factory):
    """Factory for User model"""
    
    class Meta:
        model = User
    
    id = factory.Sequence(lambda n: n)
    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.Faker('email')
    username = factory.Faker('user_name')
    hashed_password = factory.LazyFunction(
        lambda: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewCwcAk2n93kE7/e'  # "testpassword"
    )
    full_name = factory.Faker('name')
    
    is_active = True
    is_superuser = False
    is_verified = True
    
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at + timedelta(days=1))
    last_login = factory.LazyAttribute(lambda obj: obj.updated_at)


class SuperUserFactory(UserFactory):
    """Factory for superuser"""
    is_superuser = True
    is_verified = True


class CandidateFactory(factory.Factory):
    """Factory for Candidate model"""
    
    class Meta:
        model = Candidate
    
    id = factory.Sequence(lambda n: n)
    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    
    full_name = factory.Faker('name')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    location = factory.Faker('city')
    
    linkedin_url = factory.LazyAttribute(
        lambda obj: f"https://linkedin.com/in/{obj.full_name.lower().replace(' ', '-')}"
    )
    github_url = factory.LazyAttribute(
        lambda obj: f"https://github.com/{obj.full_name.lower().replace(' ', '')}"
    )
    portfolio_url = factory.Faker('url')
    
    headline = factory.Faker('job')
    summary = factory.Faker('text', max_nb_chars=500)
    
    current_position = factory.Faker('job')
    current_company = factory.Faker('company')
    total_experience_years = fuzzy.FuzzyInteger(1, 15)
    
    preferred_locations = factory.LazyFunction(
        lambda: [factory.Faker('city').generate(), factory.Faker('city').generate()]
    )
    salary_expectations = factory.LazyFunction(
        lambda: {
            "min": fuzzy.FuzzyInteger(50000, 80000).fuzz(),
            "max": fuzzy.FuzzyInteger(90000, 150000).fuzz(),
            "currency": "USD"
        }
    )
    
    is_active = True
    is_available = True
    
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at + timedelta(days=1))


class WorkExperienceFactory(factory.Factory):
    """Factory for WorkExperience model"""
    
    class Meta:
        model = WorkExperience
    
    id = factory.Sequence(lambda n: n)
    candidate_id = factory.SubFactory(CandidateFactory)
    
    company = factory.Faker('company')
    position = factory.Faker('job')
    department = fuzzy.FuzzyChoice([
        'Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations'
    ])
    location = factory.Faker('city')
    
    start_date = factory.Faker('date_between', start_date='-5y', end_date='-1y')
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timedelta(days=fuzzy.FuzzyInteger(365, 1095).fuzz())
    )
    is_current = False
    
    description = factory.Faker('text', max_nb_chars=300)
    responsibilities = factory.LazyFunction(
        lambda: [
            factory.Faker('sentence').generate(),
            factory.Faker('sentence').generate(),
            factory.Faker('sentence').generate()
        ]
    )
    achievements = factory.LazyFunction(
        lambda: [
            factory.Faker('sentence').generate(),
            factory.Faker('sentence').generate()
        ]
    )
    technologies_used = fuzzy.FuzzyChoice([
        ['Python', 'FastAPI', 'PostgreSQL'],
        ['JavaScript', 'React', 'Node.js'],
        ['Java', 'Spring', 'MySQL'],
        ['C#', '.NET', 'SQL Server'],
        ['Go', 'Docker', 'Kubernetes']
    ])
    colleagues = factory.LazyFunction(
        lambda: [
            factory.Faker('name').generate(),
            factory.Faker('name').generate(),
            factory.Faker('name').generate()
        ]
    )
    
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at + timedelta(days=1))


class CurrentWorkExperienceFactory(WorkExperienceFactory):
    """Factory for current work experience"""
    end_date = None
    is_current = True


class ResumeFactory(factory.Factory):
    """Factory for Resume model"""
    
    class Meta:
        model = Resume
    
    id = factory.Sequence(lambda n: n)
    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    
    file_name = factory.LazyAttribute(
        lambda obj: f"resume_{obj.id}_{factory.Faker('file_name', extension='pdf').generate()}"
    )
    file_type = fuzzy.FuzzyChoice(['pdf', 'docx', 'doc'])
    file_path = factory.LazyAttribute(
        lambda obj: f"/uploads/resumes/{obj.file_name}"
    )
    file_size_bytes = fuzzy.FuzzyInteger(100000, 5000000)  # 100KB to 5MB
    
    candidate_id = factory.SubFactory(CandidateFactory)
    
    parsed_data = factory.LazyFunction(lambda: {
        "personal_info": {
            "name": factory.Faker('name').generate(),
            "email": factory.Faker('email').generate(),
            "phone": factory.Faker('phone_number').generate(),
            "location": factory.Faker('city').generate()
        },
        "experience": [
            {
                "company": factory.Faker('company').generate(),
                "position": factory.Faker('job').generate(),
                "duration": "2020-2023",
                "department": "Engineering",
                "responsibilities": [
                    factory.Faker('sentence').generate(),
                    factory.Faker('sentence').generate()
                ]
            }
        ],
        "education": [
            {
                "institution": factory.Faker('company').generate(),
                "degree": "BS Computer Science",
                "year": "2020"
            }
        ],
        "skills": ['Python', 'FastAPI', 'PostgreSQL']
    })
    
    skills = factory.LazyFunction(
        lambda: fuzzy.FuzzyChoice([
            ['Python', 'FastAPI', 'PostgreSQL'],
            ['JavaScript', 'React', 'Node.js'],
            ['Java', 'Spring', 'MySQL'],
            ['C#', '.NET', 'SQL Server']
        ]).fuzz()
    )
    
    education = factory.LazyFunction(lambda: [
        {
            "institution": factory.Faker('company').generate(),
            "degree": fuzzy.FuzzyChoice([
                'BS Computer Science',
                'MS Software Engineering',
                'BA Information Technology',
                'PhD Computer Science'
            ]).fuzz(),
            "year": str(fuzzy.FuzzyInteger(2010, 2023).fuzz())
        }
    ])
    
    certifications = factory.LazyFunction(lambda: [
        f"AWS {fuzzy.FuzzyChoice(['Solutions Architect', 'Developer', 'DevOps Engineer']).fuzz()}",
        f"Google Cloud {fuzzy.FuzzyChoice(['Professional', 'Associate']).fuzz()}"
    ])
    
    languages = factory.LazyFunction(lambda: [
        {"language": "English", "proficiency": "Native"},
        {"language": "Spanish", "proficiency": "Conversational"}
    ])
    
    parsing_status = "completed"
    parsing_error = None
    parsing_time_ms = fuzzy.FuzzyInteger(1000, 5000)
    
    search_vector = factory.LazyAttribute(
        lambda obj: " ".join(obj.skills + [obj.candidate_id.full_name])
    )
    tags = factory.LazyFunction(
        lambda: fuzzy.FuzzyChoice([
            ['senior', 'experienced'],
            ['junior', 'entry-level'],
            ['lead', 'manager'],
            ['freelancer', 'contractor']
        ]).fuzz()
    )
    notes = factory.Faker('text', max_nb_chars=200)
    
    uploaded_by_id = factory.SubFactory(UserFactory)
    
    uploaded_at = factory.Faker('date_time_this_year')
    parsed_at = factory.LazyAttribute(lambda obj: obj.uploaded_at + timedelta(minutes=5))
    updated_at = factory.LazyAttribute(lambda obj: obj.parsed_at)


class PendingResumeFactory(ResumeFactory):
    """Factory for pending resume (not yet parsed)"""
    parsing_status = "pending"
    parsed_data = None
    parsed_at = None


class FailedResumeFactory(ResumeFactory):
    """Factory for failed resume parsing"""
    parsing_status = "failed"
    parsing_error = "Failed to extract text from PDF"
    parsed_data = None
    parsed_at = None


class ProjectFactory(factory.Factory):
    """Factory for Project model"""
    
    class Meta:
        model = Project
    
    id = factory.Sequence(lambda n: n)
    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Faker('catch_phrase')
    slug = factory.LazyAttribute(
        lambda obj: obj.name.lower().replace(' ', '-').replace('.', '')[:50]
    )
    description = factory.Faker('text', max_nb_chars=300)
    
    owner_id = factory.SubFactory(UserFactory)
    
    config = factory.LazyFunction(lambda: {
        "rate_limit": fuzzy.FuzzyInteger(50, 200).fuzz(),
        "cache_ttl": fuzzy.FuzzyInteger(300, 3600).fuzz(),
        "allowed_origins": ["http://localhost:3000"],
        "max_file_size": "10MB"
    })
    
    is_active = True
    is_public = False
    
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at + timedelta(days=1))


class PublicProjectFactory(ProjectFactory):
    """Factory for public project"""
    is_public = True


class EndpointFactory(factory.Factory):
    """Factory for Endpoint model"""
    
    class Meta:
        model = Endpoint
    
    id = factory.Sequence(lambda n: n)
    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    
    path = factory.LazyAttribute(
        lambda obj: f"/api/v1/{factory.Faker('slug').generate()}"
    )
    method = fuzzy.FuzzyChoice(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    name = factory.Faker('catch_phrase')
    description = factory.Faker('text', max_nb_chars=200)
    
    project_id = factory.SubFactory(ProjectFactory)
    
    request_schema = factory.LazyFunction(lambda: {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"}
        },
        "required": ["name"]
    })
    
    response_schema = factory.LazyFunction(lambda: {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"}
        }
    })
    
    headers = factory.LazyFunction(lambda: {
        "Content-Type": "application/json",
        "Authorization": "Bearer {token}"
    })
    
    query_params = factory.LazyFunction(lambda: {
        "page": {"type": "integer", "default": 1},
        "page_size": {"type": "integer", "default": 10}
    })
    
    auth_required = True
    scopes_required = factory.LazyFunction(
        lambda: fuzzy.FuzzyChoice([
            ['read:candidates'],
            ['write:candidates'],
            ['read:candidates', 'write:candidates'],
            ['admin']
        ]).fuzz()
    )
    
    rate_limit = fuzzy.FuzzyInteger(50, 200)
    
    is_active = True
    is_deprecated = False
    
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at + timedelta(days=1))


class PublicEndpointFactory(EndpointFactory):
    """Factory for public endpoint (no auth required)"""
    auth_required = False
    scopes_required = None


class DeprecatedEndpointFactory(EndpointFactory):
    """Factory for deprecated endpoint"""
    is_deprecated = True
    is_active = False


class APIKeyFactory(factory.Factory):
    """Factory for APIKey model"""
    
    class Meta:
        model = APIKey
    
    id = factory.Sequence(lambda n: n)
    key = factory.LazyFunction(
        lambda: f"ak_{uuid.uuid4().hex[:32]}"
    )
    name = factory.Faker('catch_phrase')
    description = factory.Faker('text', max_nb_chars=200)
    
    user_id = factory.SubFactory(UserFactory)
    
    scopes = factory.LazyFunction(
        lambda: fuzzy.FuzzyChoice([
            ['read:candidates'],
            ['write:candidates'],
            ['read:candidates', 'write:candidates'],
            ['admin']
        ]).fuzz()
    )
    
    is_active = True
    expires_at = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=365)  # 1 year from creation
    )
    last_used = None
    
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class ExpiredAPIKeyFactory(APIKeyFactory):
    """Factory for expired API key"""
    expires_at = factory.LazyAttribute(
        lambda obj: obj.created_at - timedelta(days=1)  # Expired yesterday
    )
    is_active = False


class RecentlyUsedAPIKeyFactory(APIKeyFactory):
    """Factory for recently used API key"""
    last_used = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(hours=1)
    )


# Utility functions for creating test data sets

def create_candidate_with_resume(user=None):
    """Create a candidate with associated resume and work experience"""
    if user is None:
        user = UserFactory()
    
    candidate = CandidateFactory()
    work_exp = WorkExperienceFactory(candidate_id=candidate)
    resume = ResumeFactory(candidate_id=candidate, uploaded_by_id=user)
    
    return {
        'candidate': candidate,
        'work_experience': work_exp,
        'resume': resume,
        'user': user
    }


def create_project_with_endpoints(user=None, num_endpoints=3):
    """Create a project with multiple endpoints"""
    if user is None:
        user = UserFactory()
    
    project = ProjectFactory(owner_id=user)
    endpoints = [EndpointFactory(project_id=project) for _ in range(num_endpoints)]
    
    return {
        'project': project,
        'endpoints': endpoints,
        'user': user
    }


def create_user_with_api_keys(num_keys=2):
    """Create a user with multiple API keys"""
    user = UserFactory()
    api_keys = [APIKeyFactory(user_id=user) for _ in range(num_keys)]
    
    return {
        'user': user,
        'api_keys': api_keys
    }


def create_search_test_data():
    """Create comprehensive test data for search functionality"""
    # Create users
    hr_user = UserFactory(email="hr@company.com")
    admin_user = SuperUserFactory(email="admin@company.com")
    
    # Create candidates with diverse backgrounds
    python_dev = CandidateFactory(
        full_name="Alice Python",
        current_position="Senior Python Developer",
        current_company="Tech Corp"
    )
    js_dev = CandidateFactory(
        full_name="Bob JavaScript",
        current_position="Frontend Developer",
        current_company="StartupCo"
    )
    fullstack_dev = CandidateFactory(
        full_name="Charlie Fullstack",
        current_position="Full Stack Developer",
        current_company="MegaCorp"
    )
    
    # Create work experiences
    WorkExperienceFactory(
        candidate_id=python_dev,
        company="Tech Corp",
        position="Senior Python Developer",
        department="Engineering",
        technologies_used=['Python', 'FastAPI', 'PostgreSQL'],
        colleagues=["Bob JavaScript", "David Manager"]
    )
    
    WorkExperienceFactory(
        candidate_id=js_dev,
        company="StartupCo",
        position="Frontend Developer",
        department="Engineering",
        technologies_used=['JavaScript', 'React', 'Node.js'],
        colleagues=["Alice Python", "Eve Designer"]
    )
    
    WorkExperienceFactory(
        candidate_id=fullstack_dev,
        company="MegaCorp",
        position="Full Stack Developer",
        department="Engineering",
        technologies_used=['Python', 'JavaScript', 'PostgreSQL', 'React'],
        colleagues=["Alice Python", "Bob JavaScript"]
    )
    
    # Create resumes
    ResumeFactory(
        candidate_id=python_dev,
        uploaded_by_id=hr_user,
        skills=['Python', 'FastAPI', 'PostgreSQL', 'Docker']
    )
    
    ResumeFactory(
        candidate_id=js_dev,
        uploaded_by_id=hr_user,
        skills=['JavaScript', 'React', 'Node.js', 'CSS']
    )
    
    ResumeFactory(
        candidate_id=fullstack_dev,
        uploaded_by_id=admin_user,
        skills=['Python', 'JavaScript', 'React', 'PostgreSQL', 'Docker']
    )
    
    return {
        'users': [hr_user, admin_user],
        'candidates': [python_dev, js_dev, fullstack_dev],
        'python_dev': python_dev,
        'js_dev': js_dev,
        'fullstack_dev': fullstack_dev
    }