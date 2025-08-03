"""
Enhanced Search Testing Module for HR Resume Search MCP API

This module provides sophisticated test datasets and helper functions
for showcasing the advanced search capabilities of the API.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

# Companies and departments for realistic test data
COMPANIES = [
    {"name": "TechCorp Inc", "industry": "Technology", "size": "Large"},
    {"name": "DataDyne Solutions", "industry": "Data Analytics", "size": "Medium"},
    {"name": "CloudFirst Systems", "industry": "Cloud Computing", "size": "Large"},
    {"name": "StartupXYZ", "industry": "Fintech", "size": "Small"},
    {"name": "BigTech Corporation", "industry": "Software", "size": "Enterprise"},
    {"name": "Innovation Labs", "industry": "R&D", "size": "Medium"},
    {"name": "Digital Dynamics", "industry": "Digital Marketing", "size": "Small"},
    {"name": "Enterprise Solutions Co", "industry": "Enterprise Software", "size": "Large"},
    {"name": "AI Ventures", "industry": "Artificial Intelligence", "size": "Medium"},
    {"name": "DevOps Central", "industry": "Infrastructure", "size": "Medium"}
]

DEPARTMENTS = [
    "Engineering", "Product", "Data Science", "DevOps", "QA", 
    "Security", "Marketing", "Sales", "HR", "Finance", "Operations"
]

DESKS = {
    "Engineering": ["Backend Team", "Frontend Team", "Mobile Team", "Platform Team", "Infrastructure Team"],
    "Product": ["Product Management", "Product Design", "Product Analytics", "Growth Team"],
    "Data Science": ["ML Engineering", "Data Analytics", "Business Intelligence", "Research"],
    "DevOps": ["Platform Engineering", "Site Reliability", "Cloud Infrastructure", "Automation"],
    "QA": ["Test Automation", "Manual Testing", "Performance Testing", "Security Testing"],
    "Security": ["InfoSec", "AppSec", "Compliance", "Risk Management"],
    "Marketing": ["Digital Marketing", "Content Marketing", "Growth Marketing", "Brand"],
    "Sales": ["Inside Sales", "Enterprise Sales", "Sales Engineering", "Customer Success"]
}

SKILLS_BY_CATEGORY = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", 
        "C#", "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "SQL"
    ],
    "Frameworks & Libraries": [
        "React", "Vue.js", "Angular", "Node.js", "Express", "Django", "Flask",
        "Spring Boot", "FastAPI", "Rails", "Laravel", "TensorFlow", "PyTorch"
    ],
    "Cloud & Infrastructure": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
        "Jenkins", "GitLab CI", "CircleCI", "Prometheus", "Grafana"
    ],
    "Databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
        "DynamoDB", "InfluxDB", "Neo4j", "Snowflake"
    ],
    "Tools & Technologies": [
        "Git", "Jira", "Slack", "Figma", "Tableau", "Power BI", "Jupyter",
        "VS Code", "IntelliJ", "Postman", "Swagger"
    ],
    "Soft Skills": [
        "Leadership", "Team Management", "Project Management", "Communication",
        "Problem Solving", "Strategic Thinking", "Mentoring", "Public Speaking"
    ]
}

def generate_realistic_candidate(candidate_id: int) -> Dict[str, Any]:
    """Generate a realistic candidate profile with interconnected data"""
    
    # Select primary company and department
    current_company = random.choice(COMPANIES)
    primary_dept = random.choice(DEPARTMENTS)
    current_desk = random.choice(DESKS.get(primary_dept, ["General"]))
    
    # Generate work history with some overlapping companies/departments
    work_history = []
    years_experience = random.randint(2, 15)
    current_year = datetime.now().year
    
    # Current position
    work_history.append({
        "company": current_company["name"],
        "position": generate_position_title(primary_dept, years_experience),
        "department": primary_dept,
        "desk": current_desk,
        "start_date": f"{current_year - random.randint(1, 3)}-{random.randint(1,12):02d}-01",
        "end_date": None,
        "description": f"Leading {primary_dept.lower()} initiatives at {current_company['name']}"
    })
    
    # Previous positions
    remaining_years = years_experience - random.randint(1, 3)
    while remaining_years > 0:
        # 30% chance of staying in same company, 40% chance of same department
        if len(work_history) > 1 and random.random() < 0.3:
            company = work_history[0]["company"]
        else:
            company = random.choice(COMPANIES)["name"]
        
        if random.random() < 0.4:
            dept = primary_dept
            desk = random.choice(DESKS.get(dept, ["General"]))
        else:
            dept = random.choice(DEPARTMENTS)
            desk = random.choice(DESKS.get(dept, ["General"]))
        
        years_in_role = min(random.randint(1, 4), remaining_years)
        start_year = current_year - years_experience + (years_experience - remaining_years)
        
        work_history.append({
            "company": company,
            "position": generate_position_title(dept, remaining_years),
            "department": dept,
            "desk": desk,
            "start_date": f"{start_year}-{random.randint(1,12):02d}-01",
            "end_date": f"{start_year + years_in_role - 1}-{random.randint(1,12):02d}-01",
            "description": f"Worked on {dept.lower()} projects at {company}"
        })
        
        remaining_years -= years_in_role
    
    # Generate skills based on department and experience
    skills = generate_skills_for_department(primary_dept, years_experience)
    
    # Generate education
    education = [{
        "institution": random.choice([
            "MIT", "Stanford University", "UC Berkeley", "Carnegie Mellon",
            "University of Washington", "Georgia Tech", "UT Austin",
            "Harvard University", "Yale University", "Princeton University"
        ]),
        "degree": random.choice([
            "Bachelor of Science", "Master of Science", "Master of Engineering",
            "Bachelor of Engineering", "PhD"
        ]),
        "field_of_study": random.choice([
            "Computer Science", "Software Engineering", "Data Science",
            "Information Systems", "Mathematics", "Statistics", "Physics"
        ]),
        "graduation_date": f"{current_year - years_experience - random.randint(0, 2)}-06-01"
    }]
    
    return {
        "name": f"Candidate {candidate_id:03d}",
        "email": f"candidate{candidate_id:03d}@example.com",
        "phone": f"+1-555-{candidate_id:04d}",
        "location": random.choice([
            "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
            "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Denver, CO"
        ]),
        "summary": f"Experienced {primary_dept.lower()} professional with {years_experience}+ years in {current_company['industry'].lower()}",
        "experience": work_history,
        "skills": skills,
        "education": education,
        "metadata": {
            "years_experience": years_experience,
            "primary_department": primary_dept,
            "current_company_size": current_company["size"],
            "industry": current_company["industry"]
        }
    }

def generate_position_title(department: str, experience_years: int) -> str:
    """Generate realistic position titles based on department and experience"""
    level = "Senior" if experience_years >= 5 else "Junior" if experience_years < 3 else ""
    
    titles_by_dept = {
        "Engineering": ["Software Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Engineer"],
        "Product": ["Product Manager", "Product Owner", "Product Analyst", "Growth Manager"],
        "Data Science": ["Data Scientist", "ML Engineer", "Data Analyst", "Research Scientist"],
        "DevOps": ["DevOps Engineer", "Site Reliability Engineer", "Platform Engineer", "Cloud Architect"],
        "QA": ["QA Engineer", "Test Engineer", "Automation Engineer", "Quality Analyst"],
        "Security": ["Security Engineer", "InfoSec Analyst", "Security Architect", "Compliance Officer"]
    }
    
    base_title = random.choice(titles_by_dept.get(department, ["Specialist", "Analyst", "Coordinator"]))
    
    if experience_years >= 8:
        return f"Lead {base_title}" if random.random() < 0.3 else f"Senior {base_title}"
    elif experience_years >= 5:
        return f"Senior {base_title}"
    elif experience_years >= 3:
        return base_title
    else:
        return f"Junior {base_title}"

def generate_skills_for_department(department: str, experience: int) -> List[str]:
    """Generate realistic skills based on department and experience level"""
    base_skills = []
    
    # Department-specific skills
    if department == "Engineering":
        base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Programming Languages"], 3))
        base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Frameworks & Libraries"], 2))
        base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Cloud & Infrastructure"], 2))
    elif department == "Data Science":
        base_skills.extend(["Python", "R", "SQL"])
        base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Frameworks & Libraries"], 2))
        base_skills.extend(["TensorFlow", "PyTorch", "Jupyter"])
    elif department == "DevOps":
        base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Cloud & Infrastructure"], 4))
        base_skills.extend(["Python", "Bash", "Linux"])
    elif department == "Product":
        base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Tools & Technologies"], 3))
        base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Soft Skills"], 3))
    
    # Add database skills
    base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Databases"], 2))
    
    # Add soft skills based on experience
    if experience >= 5:
        base_skills.extend(random.sample(SKILLS_BY_CATEGORY["Soft Skills"], 2))
    
    # Remove duplicates and limit based on experience
    skills = list(set(base_skills))
    max_skills = min(len(skills), 8 + (experience // 2))
    
    return skills[:max_skills]

def create_test_search_scenarios() -> List[Dict[str, Any]]:
    """Create comprehensive search test scenarios"""
    
    return [
        {
            "name": "Multi-Criteria Engineering Search",
            "description": "Find senior engineers with Python and AWS experience",
            "endpoint": "/search/candidates",
            "payload": {
                "query": "senior software engineer",
                "filters": {
                    "skills": ["Python", "AWS"],
                    "departments": ["Engineering"],
                    "experience_years": {"min": 5, "max": 12},
                    "current_location": ["San Francisco, CA", "Seattle, WA"]
                },
                "scoring": {
                    "skills_weight": 0.4,
                    "experience_weight": 0.3,
                    "title_weight": 0.2,
                    "location_weight": 0.1
                },
                "limit": 10
            },
            "expected_features": ["skill matching", "experience filtering", "location preference"]
        },
        {
            "name": "Similar Profile Matching",
            "description": "Find candidates similar to a specific profile",
            "endpoint": "/search/similar",
            "payload": {
                "candidate_id": "will_be_filled",  # Will be filled with actual candidate ID
                "similarity_threshold": 0.7,
                "include_factors": ["skills", "experience", "education", "career_path"],
                "exclude_current_company": True,
                "limit": 15
            },
            "expected_features": ["AI similarity scoring", "career path analysis", "skill overlap"]
        },
        {
            "name": "Colleague Discovery",
            "description": "Find former colleagues and professional connections",
            "endpoint": "/search/colleagues",
            "payload": {
                "candidate_id": "will_be_filled",
                "overlap_types": ["company", "department", "project"],
                "time_overlap_required": True,
                "include_indirect": True,
                "max_degrees": 2,
                "limit": 20
            },
            "expected_features": ["temporal overlap", "network analysis", "relationship mapping"]
        },
        {
            "name": "Smart Natural Language Search",
            "description": "AI-powered search using natural language queries",
            "endpoint": "/search/smart",
            "payload": {
                "query": "Find me data scientists who have worked at startups and know machine learning",
                "context": {
                    "role": "hiring_manager",
                    "department": "Data Science",
                    "priority": "experience_over_education"
                },
                "enhance_query": True,
                "explain_reasoning": True
            },
            "expected_features": ["NLP processing", "query enhancement", "reasoning explanation"]
        },
        {
            "name": "Advanced Multi-Factor Search",
            "description": "Complex search with multiple weighted factors",
            "endpoint": "/search/candidates",
            "payload": {
                "query": "product manager fintech experience",
                "filters": {
                    "departments": ["Product", "Engineering"],
                    "industries": ["Fintech", "Banking", "Technology"],
                    "company_sizes": ["Medium", "Large"],
                    "skills": ["Product Strategy", "SQL", "Python"],
                    "education_levels": ["Bachelor", "Master"]
                },
                "scoring": {
                    "industry_match": 0.25,
                    "skills_overlap": 0.25,
                    "experience_relevance": 0.2,
                    "education_fit": 0.15,
                    "location_preference": 0.15
                },
                "boost": {
                    "recent_experience": 1.2,
                    "leadership_roles": 1.3,
                    "top_companies": 1.1
                },
                "sort_by": "relevance_score",
                "include_score_breakdown": True,
                "limit": 25
            },
            "expected_features": ["weighted scoring", "boosting factors", "score explanation"]
        },
        {
            "name": "Performance Benchmark Search",
            "description": "High-volume search for performance testing",
            "endpoint": "/search/candidates",
            "payload": {
                "query": "engineer",
                "filters": {
                    "experience_years": {"min": 2}
                },
                "limit": 100,
                "include_aggregations": True,
                "cache_results": True
            },
            "expected_features": ["high volume", "caching", "aggregations"]
        }
    ]

def create_search_visualization_data(search_results: List[Dict]) -> pd.DataFrame:
    """Create DataFrame for search result visualization"""
    
    visualization_data = []
    
    for result in search_results:
        if 'data' in result and 'results' in result['data']:
            for candidate in result['data']['results']:
                viz_entry = {
                    'search_type': result.get('search_type', 'unknown'),
                    'candidate_id': candidate.get('id'),
                    'name': candidate.get('name'),
                    'score': candidate.get('score', 0),
                    'experience_years': candidate.get('metadata', {}).get('years_experience', 0),
                    'department': candidate.get('experience', [{}])[0].get('department', 'Unknown'),
                    'current_company': candidate.get('experience', [{}])[0].get('company', 'Unknown'),
                    'skills_count': len(candidate.get('skills', [])),
                    'location': candidate.get('location', 'Unknown'),
                    'response_time': result.get('response_time', 0)
                }
                visualization_data.append(viz_entry)
    
    return pd.DataFrame(visualization_data)

def analyze_search_performance(results: List[Dict]) -> Dict[str, Any]:
    """Analyze search performance metrics"""
    
    if not results:
        return {"error": "No results to analyze"}
    
    response_times = [r.get('response_time', 0) for r in results]
    result_counts = [len(r.get('data', {}).get('results', [])) for r in results]
    success_rates = [1 if r.get('success', False) else 0 for r in results]
    
    return {
        "total_searches": len(results),
        "success_rate": sum(success_rates) / len(success_rates) * 100,
        "avg_response_time": sum(response_times) / len(response_times),
        "min_response_time": min(response_times),
        "max_response_time": max(response_times),
        "avg_results_per_search": sum(result_counts) / len(result_counts),
        "total_results": sum(result_counts),
        "response_time_p95": sorted(response_times)[int(len(response_times) * 0.95)],
        "searches_under_1s": sum(1 for t in response_times if t < 1.0),
        "searches_under_2s": sum(1 for t in response_times if t < 2.0)
    }

# Export all functions
__all__ = [
    'COMPANIES', 'DEPARTMENTS', 'DESKS', 'SKILLS_BY_CATEGORY',
    'generate_realistic_candidate', 'create_test_search_scenarios',
    'create_search_visualization_data', 'analyze_search_performance'
]