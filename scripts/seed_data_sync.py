#!/usr/bin/env python3
"""
Sync seed script for HR Resume Search database
Creates test users, candidates, resumes, and work experience data
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List
import hashlib
import uuid

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    from passlib.context import CryptContext
    
    from api.models import User, Candidate, Resume, WorkExperience
    from api.config import get_settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Installing missing dependencies...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "sqlalchemy", "passlib", "bcrypt", "psycopg2-binary"])
    print("Please run the script again after dependencies are installed.")
    sys.exit(1)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def create_test_users(session: Session) -> List[User]:
    """Create test users"""
    users_data = [
        {
            "email": "admin@company.com",
            "username": "admin",
            "full_name": "System Administrator",
            "hashed_password": hash_password("admin123"),
            "is_superuser": True,
            "is_verified": True
        },
        {
            "email": "hr.manager@company.com",
            "username": "hr_manager",
            "full_name": "HR Manager",
            "hashed_password": hash_password("hr123"),
            "is_superuser": False,
            "is_verified": True
        },
        {
            "email": "recruiter@company.com", 
            "username": "recruiter",
            "full_name": "Senior Recruiter",
            "hashed_password": hash_password("recruiter123"),
            "is_superuser": False,
            "is_verified": True
        }
    ]
    
    users = []
    for user_data in users_data:
        user = User(**user_data)
        session.add(user)
        users.append(user)
    
    session.commit()
    print(f"✅ Created {len(users)} test users")
    return users

def create_test_candidates(session: Session) -> List[Candidate]:
    """Create test candidates"""
    candidates_data = [
        {
            "full_name": "Alice Johnson",
            "email": "alice.johnson@email.com",
            "phone": "+1-555-0101",
            "location": "New York, NY",
            "linkedin_url": "https://linkedin.com/in/alice-johnson-dev",
            "github_url": "https://github.com/alicejohnson",
            "headline": "Senior Software Engineer with 8+ years experience",
            "summary": "Experienced full-stack developer specializing in Python, React, and cloud architecture. Led teams of 5+ developers in building scalable web applications.",
            "current_position": "Senior Software Engineer",
            "current_company": "TechCorp Inc",
            "total_experience_years": 8,
            "preferred_locations": ["New York, NY", "San Francisco, CA", "Remote"],
            "salary_expectations": {"min": 120000, "max": 150000, "currency": "USD"}
        },
        {
            "full_name": "Bob Smith",
            "email": "bob.smith@email.com", 
            "phone": "+1-555-0102",
            "location": "San Francisco, CA",
            "linkedin_url": "https://linkedin.com/in/bob-smith-data",
            "headline": "Data Scientist & ML Engineer",
            "summary": "Data scientist with expertise in machine learning, deep learning, and statistical analysis. PhD in Computer Science with focus on AI.",
            "current_position": "Senior Data Scientist",
            "current_company": "DataFlow Solutions",
            "total_experience_years": 6,
            "preferred_locations": ["San Francisco, CA", "Seattle, WA", "Austin, TX"],
            "salary_expectations": {"min": 110000, "max": 140000, "currency": "USD"}
        },
        {
            "full_name": "Carol Davis",
            "email": "carol.davis@email.com",
            "phone": "+1-555-0103", 
            "location": "Chicago, IL",
            "linkedin_url": "https://linkedin.com/in/carol-davis-pm",
            "headline": "Product Manager - B2B SaaS",
            "summary": "Product manager with 5+ years experience in B2B SaaS products. Expert in agile methodologies, user research, and product strategy.",
            "current_position": "Product Manager",
            "current_company": "SaaS Solutions Ltd",
            "total_experience_years": 5,
            "preferred_locations": ["Chicago, IL", "New York, NY", "Remote"],
            "salary_expectations": {"min": 95000, "max": 120000, "currency": "USD"}
        },
        {
            "full_name": "David Wilson",
            "email": "david.wilson@email.com",
            "phone": "+1-555-0104",
            "location": "Austin, TX", 
            "linkedin_url": "https://linkedin.com/in/david-wilson-devops",
            "github_url": "https://github.com/davidwilson",
            "headline": "DevOps Engineer - Cloud Infrastructure",
            "summary": "DevOps engineer specializing in AWS, Kubernetes, and CI/CD pipelines. Experience with infrastructure as code and monitoring systems.",
            "current_position": "DevOps Engineer",
            "current_company": "CloudTech Systems",
            "total_experience_years": 4,
            "preferred_locations": ["Austin, TX", "Remote"],
            "salary_expectations": {"min": 85000, "max": 110000, "currency": "USD"}
        },
        {
            "full_name": "Eve Brown",
            "email": "eve.brown@email.com",
            "phone": "+1-555-0105",
            "location": "Boston, MA",
            "linkedin_url": "https://linkedin.com/in/eve-brown-ux",
            "portfolio_url": "https://evebrown.design",
            "headline": "UX/UI Designer - Enterprise Software",
            "summary": "UX/UI designer with 6+ years experience designing enterprise software. Expert in user research, wireframing, and design systems.",
            "current_position": "Senior UX Designer", 
            "current_company": "Enterprise Design Co",
            "total_experience_years": 6,
            "preferred_locations": ["Boston, MA", "New York, NY", "Remote"],
            "salary_expectations": {"min": 75000, "max": 95000, "currency": "USD"}
        }
    ]
    
    candidates = []
    for candidate_data in candidates_data:
        candidate = Candidate(**candidate_data)
        session.add(candidate)
        candidates.append(candidate)
    
    session.commit()
    print(f"✅ Created {len(candidates)} test candidates")
    return candidates

def create_test_work_experiences(session: Session, candidates: List[Candidate]) -> List[WorkExperience]:
    """Create test work experience data"""
    work_experiences = []
    
    # Alice Johnson's work experience
    alice = candidates[0]
    alice_experiences = [
        {
            "candidate_id": alice.id,
            "company": "TechCorp Inc",
            "position": "Senior Software Engineer",
            "department": "Engineering",
            "location": "New York, NY",
            "start_date": datetime.now() - timedelta(days=365*2),  # 2 years ago
            "end_date": None,
            "is_current": True,
            "description": "Lead development of microservices architecture, mentor junior developers",
            "responsibilities": [
                "Lead team of 5 developers",
                "Design and implement REST APIs",
                "Code review and mentoring",
                "Performance optimization"
            ],
            "achievements": [
                "Reduced API response time by 40%",
                "Implemented CI/CD pipeline",
                "Led migration to containerized architecture"
            ],
            "technologies_used": ["Python", "Django", "React", "PostgreSQL", "Docker", "AWS"],
            "colleagues": ["Bob Martinez", "Sarah Chen", "Mike Rodriguez"]
        },
        {
            "candidate_id": alice.id,
            "company": "StartupXYZ",
            "position": "Software Engineer",
            "department": "Product Development",
            "location": "San Francisco, CA",
            "start_date": datetime.now() - timedelta(days=365*5),  # 5 years ago
            "end_date": datetime.now() - timedelta(days=365*2),   # 2 years ago
            "is_current": False,
            "description": "Full-stack development of web applications",
            "responsibilities": [
                "Frontend and backend development",
                "Database design and optimization",
                "API integration",
                "Bug fixes and feature development"
            ],
            "achievements": [
                "Built user dashboard from scratch",
                "Improved database query performance by 60%"
            ],
            "technologies_used": ["Python", "Flask", "Vue.js", "MySQL", "Redis"],
            "colleagues": ["Jennifer Lee", "Tom Anderson"]
        }
    ]
    
    # Bob Smith's work experience
    bob = candidates[1]
    bob_experiences = [
        {
            "candidate_id": bob.id,
            "company": "DataFlow Solutions",
            "position": "Senior Data Scientist", 
            "department": "Data Science",
            "location": "San Francisco, CA",
            "start_date": datetime.now() - timedelta(days=365*3),
            "end_date": None,
            "is_current": True,
            "description": "Lead data science projects and ML model development",
            "responsibilities": [
                "Build and deploy ML models",
                "Data analysis and visualization",
                "A/B testing and experimentation",
                "Collaborate with engineering teams"
            ],
            "achievements": [
                "Deployed ML models serving 1M+ predictions daily",
                "Improved recommendation system CTR by 25%"
            ],
            "technologies_used": ["Python", "TensorFlow", "Pandas", "SQL", "Apache Spark"],
            "colleagues": ["Alice Johnson", "Maria Garcia", "John Kim"]
        }
    ]
    
    # Add more experiences
    all_experiences = alice_experiences + bob_experiences
    
    for exp_data in all_experiences:
        experience = WorkExperience(**exp_data)
        session.add(experience)
        work_experiences.append(experience)
    
    session.commit()
    print(f"✅ Created {len(work_experiences)} work experience records")
    return work_experiences

def main():
    """Main seed function"""
    settings = get_settings()
    
    # Create sync engine
    engine = create_engine(settings.database_url, echo=False)
    
    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    
    print("🚀 Starting database seeding...")
    
    with SessionLocal() as session:
        try:
            # Create test data
            users = create_test_users(session)
            candidates = create_test_candidates(session)
            work_experiences = create_test_work_experiences(session, candidates)
            
            print(f"\n🎉 Database seeding completed successfully!")
            print(f"📊 Summary:")
            print(f"   - Users: {len(users)}")
            print(f"   - Candidates: {len(candidates)}")
            print(f"   - Work Experiences: {len(work_experiences)}")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    main()