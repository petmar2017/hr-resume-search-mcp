#!/usr/bin/env python3
"""
Seed script for HR Resume Search database
Creates test users, candidates, resumes, and work experience data
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List
import hashlib
import uuid

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from api.models import User, Candidate, Resume, WorkExperience
from api.config import get_settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

async def create_test_users(session: AsyncSession) -> List[User]:
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
    
    await session.commit()
    print(f"✅ Created {len(users)} test users")
    return users

async def create_test_candidates(session: AsyncSession) -> List[Candidate]:
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
    
    await session.commit()
    print(f"✅ Created {len(candidates)} test candidates")
    return candidates

async def create_test_work_experiences(session: AsyncSession, candidates: List[Candidate]) -> List[WorkExperience]:
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
        },
        {
            "candidate_id": bob.id,
            "company": "Research University",
            "position": "PhD Research Assistant",
            "department": "Computer Science",
            "location": "Stanford, CA",
            "start_date": datetime.now() - timedelta(days=365*6),
            "end_date": datetime.now() - timedelta(days=365*3),
            "is_current": False,
            "description": "Research in machine learning and artificial intelligence",
            "responsibilities": [
                "Conduct research experiments",
                "Publish academic papers",
                "Teaching assistance",
                "Grant writing"
            ],
            "achievements": [
                "Published 8 peer-reviewed papers",
                "Received Best Paper Award at AI Conference 2022"
            ],
            "technologies_used": ["Python", "PyTorch", "R", "MATLAB"],
            "colleagues": ["Dr. Sarah Johnson", "Dr. Mike Chen"]
        }
    ]
    
    # Carol Davis's work experience
    carol = candidates[2]
    carol_experiences = [
        {
            "candidate_id": carol.id,
            "company": "SaaS Solutions Ltd",
            "position": "Product Manager",
            "department": "Product",
            "location": "Chicago, IL",
            "start_date": datetime.now() - timedelta(days=365*2),
            "end_date": None,
            "is_current": True,
            "description": "Lead product strategy for B2B SaaS platform",
            "responsibilities": [
                "Product roadmap planning",
                "User research and feedback analysis",
                "Cross-functional team coordination",
                "Feature prioritization"
            ],
            "achievements": [
                "Increased user engagement by 35%",
                "Launched 3 major product features",
                "Reduced customer churn by 20%"
            ],
            "technologies_used": ["Jira", "Figma", "Google Analytics", "Amplitude"],
            "colleagues": ["David Kim", "Lisa Wang", "Tom Rodriguez"]
        }
    ]
    
    # David Wilson's work experience  
    david = candidates[3]
    david_experiences = [
        {
            "candidate_id": david.id,
            "company": "CloudTech Systems",
            "position": "DevOps Engineer",
            "department": "Infrastructure",
            "location": "Austin, TX",
            "start_date": datetime.now() - timedelta(days=365*2),
            "end_date": None,
            "is_current": True,
            "description": "Manage cloud infrastructure and CI/CD pipelines",
            "responsibilities": [
                "AWS infrastructure management",
                "Kubernetes cluster administration",
                "CI/CD pipeline development",
                "Monitoring and alerting setup"
            ],
            "achievements": [
                "Reduced deployment time by 70%",
                "Achieved 99.9% system uptime",
                "Cost optimization saved $50K annually"
            ],
            "technologies_used": ["AWS", "Kubernetes", "Docker", "Terraform", "Jenkins"],
            "colleagues": ["Alice Johnson", "Mike Stevens", "Sarah Chen"]
        }
    ]
    
    # Eve Brown's work experience
    eve = candidates[4]
    eve_experiences = [
        {
            "candidate_id": eve.id,
            "company": "Enterprise Design Co",
            "position": "Senior UX Designer",
            "department": "Design",
            "location": "Boston, MA", 
            "start_date": datetime.now() - timedelta(days=365*3),
            "end_date": None,
            "is_current": True,
            "description": "Lead UX design for enterprise software products",
            "responsibilities": [
                "User research and usability testing",
                "Wireframing and prototyping",
                "Design system maintenance",
                "Stakeholder collaboration"
            ],
            "achievements": [
                "Redesigned main product reducing user errors by 45%",
                "Created company-wide design system",
                "Improved user satisfaction scores by 30%"
            ],
            "technologies_used": ["Figma", "Sketch", "InVision", "Adobe Creative Suite"],
            "colleagues": ["Carol Davis", "Jenny Liu", "Mark Johnson"]
        }
    ]
    
    # Combine all experiences
    all_experiences = alice_experiences + bob_experiences + carol_experiences + david_experiences + eve_experiences
    
    for exp_data in all_experiences:
        experience = WorkExperience(**exp_data)
        session.add(experience)
        work_experiences.append(experience)
    
    await session.commit()
    print(f"✅ Created {len(work_experiences)} work experience records")
    return work_experiences

async def create_test_resumes(session: AsyncSession, candidates: List[Candidate], users: List[User]) -> List[Resume]:
    """Create test resume records"""
    resumes = []
    uploaded_by = users[1]  # HR Manager uploads resumes
    
    resume_data = [
        {
            "candidate_id": candidates[0].id,  # Alice Johnson
            "file_name": "alice_johnson_resume.pdf",
            "file_type": "pdf",
            "file_path": "/uploads/resumes/alice_johnson_resume.pdf",
            "file_size_bytes": 245760,
            "uploaded_by_id": uploaded_by.id,
            "parsing_status": "completed",
            "parsed_data": {
                "personal_info": {
                    "name": "Alice Johnson",
                    "email": "alice.johnson@email.com",
                    "phone": "+1-555-0101",
                    "location": "New York, NY"
                },
                "work_experience": [
                    {
                        "company": "TechCorp Inc",
                        "position": "Senior Software Engineer",
                        "duration": "2022 - Present",
                        "responsibilities": ["Lead team development", "API design", "Mentoring"]
                    }
                ],
                "skills": ["Python", "Django", "React", "PostgreSQL", "Docker", "AWS"],
                "education": [
                    {
                        "degree": "Bachelor of Science in Computer Science",
                        "institution": "State University",
                        "year": "2016"
                    }
                ]
            },
            "skills": ["Python", "Django", "React", "PostgreSQL", "Docker", "AWS", "JavaScript", "Git"],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "State University", 
                    "year": "2016",
                    "gpa": "3.8"
                }
            ],
            "certifications": [
                {
                    "name": "AWS Certified Solutions Architect",
                    "issuer": "Amazon Web Services",
                    "year": "2023"
                }
            ],
            "languages": [
                {"language": "English", "proficiency": "Native"},
                {"language": "Spanish", "proficiency": "Conversational"}
            ],
            "search_vector": "software engineer python django react postgresql docker aws full-stack",
            "tags": ["senior", "full-stack", "team-lead"],
            "notes": "Strong technical background, excellent leadership skills"
        },
        {
            "candidate_id": candidates[1].id,  # Bob Smith
            "file_name": "bob_smith_resume.pdf",
            "file_type": "pdf", 
            "file_path": "/uploads/resumes/bob_smith_resume.pdf",
            "file_size_bytes": 287340,
            "uploaded_by_id": uploaded_by.id,
            "parsing_status": "completed",
            "parsed_data": {
                "personal_info": {
                    "name": "Bob Smith",
                    "email": "bob.smith@email.com",
                    "phone": "+1-555-0102",
                    "location": "San Francisco, CA"
                }
            },
            "skills": ["Python", "TensorFlow", "Pandas", "SQL", "Apache Spark", "Machine Learning", "Statistics"],
            "education": [
                {
                    "degree": "PhD in Computer Science",
                    "institution": "Stanford University",
                    "year": "2021",
                    "specialization": "Artificial Intelligence"
                }
            ],
            "certifications": [
                {
                    "name": "Google Cloud Professional Data Engineer",
                    "issuer": "Google Cloud",
                    "year": "2023"
                }
            ],
            "languages": [
                {"language": "English", "proficiency": "Native"},
                {"language": "Mandarin", "proficiency": "Fluent"}
            ],
            "search_vector": "data scientist machine learning tensorflow python phd artificial intelligence",
            "tags": ["data-science", "ml-expert", "phd"],
            "notes": "PhD level expertise in AI/ML, strong research background"
        },
        {
            "candidate_id": candidates[2].id,  # Carol Davis
            "file_name": "carol_davis_resume.docx",
            "file_type": "docx",
            "file_path": "/uploads/resumes/carol_davis_resume.docx", 
            "file_size_bytes": 156890,
            "uploaded_by_id": uploaded_by.id,
            "parsing_status": "completed",
            "parsed_data": {
                "personal_info": {
                    "name": "Carol Davis",
                    "email": "carol.davis@email.com",
                    "phone": "+1-555-0103",
                    "location": "Chicago, IL"
                }
            },
            "skills": ["Product Management", "Agile", "Scrum", "User Research", "Analytics", "A/B Testing"],
            "education": [
                {
                    "degree": "MBA",
                    "institution": "Northwestern Kellogg",
                    "year": "2019"
                },
                {
                    "degree": "Bachelor of Business Administration",
                    "institution": "University of Illinois",
                    "year": "2017"
                }
            ],
            "certifications": [
                {
                    "name": "Certified Scrum Product Owner",
                    "issuer": "Scrum Alliance",
                    "year": "2022"
                }
            ],
            "languages": [
                {"language": "English", "proficiency": "Native"}
            ],
            "search_vector": "product manager saas agile scrum user research analytics mba",
            "tags": ["product-management", "b2b-saas", "mba"],
            "notes": "Strong product sense, excellent stakeholder management"
        }
    ]
    
    for resume_data_item in resume_data:
        # Set parsing timestamp
        resume_data_item["parsed_at"] = datetime.now()
        resume = Resume(**resume_data_item)
        session.add(resume)
        resumes.append(resume)
    
    await session.commit()
    print(f"✅ Created {len(resumes)} resume records")
    return resumes

async def main():
    """Main seed function"""
    settings = get_settings()
    
    # Convert sync database URL to async
    if settings.database_url.startswith("sqlite:///"):
        database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif settings.database_url.startswith("postgresql://"):
        database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    else:
        database_url = settings.database_url
    
    # Create async engine
    engine = create_async_engine(database_url, echo=False)
    
    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    print("🚀 Starting database seeding...")
    
    async with async_session() as session:
        try:
            # Create test data
            users = await create_test_users(session)
            candidates = await create_test_candidates(session)
            work_experiences = await create_test_work_experiences(session, candidates)
            resumes = await create_test_resumes(session, candidates, users)
            
            print(f"\n🎉 Database seeding completed successfully!")
            print(f"📊 Summary:")
            print(f"   - Users: {len(users)}")
            print(f"   - Candidates: {len(candidates)}")
            print(f"   - Work Experiences: {len(work_experiences)}")
            print(f"   - Resumes: {len(resumes)}")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await session.rollback()
            raise
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())