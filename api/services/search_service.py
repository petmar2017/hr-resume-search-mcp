"""
Search Service for resume and candidate search functionality
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload
import asyncio
import re
from datetime import datetime, timedelta

from ..models import Candidate, Resume, WorkExperience
from ..database import get_db
from .claude_service import ClaudeService


class SearchService:
    """Service for handling search operations"""
    
    def __init__(self):
        self.claude_service = ClaudeService()
    
    async def search_by_skills(
        self,
        skills: List[str],
        min_score: float = 0.3,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search candidates by skills with similarity scoring"""
        
        async with get_db() as db:
            # Get resumes with matching skills
            query = select(Resume).options(
                selectinload(Resume.candidate)
            ).where(
                Resume.parsing_status == "completed"
            )
            
            result = await db.execute(query)
            resumes = result.scalars().all()
            
            # Score and filter results
            scored_results = []
            for resume in resumes:
                score = self._calculate_skill_match_score(resume.skills or [], skills)
                if score >= min_score:
                    scored_results.append({
                        "candidate": resume.candidate,
                        "resume": resume,
                        "score": score,
                        "matching_skills": list(set(resume.skills or []) & set(skills))
                    })
            
            # Sort by score
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            
            return scored_results[offset:offset + limit]
    
    async def search_by_department(
        self,
        department: str,
        seniority: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search candidates by department and optional seniority"""
        
        async with get_db() as db:
            query = select(Candidate).options(
                selectinload(Candidate.work_experiences),
                selectinload(Candidate.resumes)
            ).join(WorkExperience).where(
                WorkExperience.department.ilike(f"%{department}%")
            )
            
            if seniority:
                # Filter by seniority level in position titles
                seniority_patterns = {
                    "senior": ["senior", "lead", "principal", "staff"],
                    "junior": ["junior", "entry", "associate"],
                    "manager": ["manager", "director", "head", "vp"]
                }
                
                if seniority.lower() in seniority_patterns:
                    patterns = seniority_patterns[seniority.lower()]
                    seniority_conditions = [
                        WorkExperience.position.ilike(f"%{pattern}%") 
                        for pattern in patterns
                    ]
                    query = query.where(or_(*seniority_conditions))
            
            query = query.limit(limit)
            result = await db.execute(query)
            candidates = result.scalars().unique().all()
            
            return [
                {
                    "candidate": candidate,
                    "experience": [exp for exp in candidate.work_experiences 
                                 if department.lower() in (exp.department or "").lower()]
                }
                for candidate in candidates
            ]
    
    async def search_similar_candidates(
        self,
        candidate_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find candidates similar to the given candidate"""
        
        async with get_db() as db:
            # Get base candidate
            base_candidate = await db.get(Candidate, candidate_id)
            if not base_candidate:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Get base candidate's resume and experience
            base_resume_query = select(Resume).where(
                and_(
                    Resume.candidate_id == candidate_id,
                    Resume.parsing_status == "completed"
                )
            ).limit(1)
            
            base_resume_result = await db.execute(base_resume_query)
            base_resume = base_resume_result.scalar_one_or_none()
            
            if not base_resume:
                return []
            
            # Get all other candidates
            candidates_query = select(Candidate).options(
                selectinload(Candidate.resumes),
                selectinload(Candidate.work_experiences)
            ).where(Candidate.id != candidate_id)
            
            candidates_result = await db.execute(candidates_query)
            candidates = candidates_result.scalars().all()
            
            # Calculate similarity scores
            similar_candidates = []
            for candidate in candidates:
                for resume in candidate.resumes:
                    if resume.parsing_status == "completed":
                        similarity_score = self._calculate_similarity_score(
                            base_resume, resume
                        )
                        
                        if similarity_score > 0.3:  # Minimum threshold
                            match_reasons = self._get_match_reasons(
                                base_candidate, base_resume, candidate, resume
                            )
                            
                            similar_candidates.append({
                                "candidate": candidate,
                                "similarity_score": similarity_score,
                                "match_reasons": match_reasons
                            })
                        break  # Use first completed resume only
            
            # Sort by similarity score
            similar_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return similar_candidates[:limit]
    
    async def search_colleagues(
        self,
        candidate_id: int,
        include_potential: bool = True,
        min_overlap_months: int = 3
    ) -> List[Dict[str, Any]]:
        """Find candidates who worked with the given candidate"""
        
        async with get_db() as db:
            # Get base candidate's work experience
            base_exp_query = select(WorkExperience).where(
                WorkExperience.candidate_id == candidate_id
            )
            base_exp_result = await db.execute(base_exp_query)
            base_experiences = base_exp_result.scalars().all()
            
            if not base_experiences:
                return []
            
            colleagues = []
            
            # Find direct colleagues (mentioned in colleagues field)
            for exp in base_experiences:
                if exp.colleagues:
                    for colleague_name in exp.colleagues:
                        # Try to find candidates with matching names
                        name_query = select(Candidate).where(
                            Candidate.full_name.ilike(f"%{colleague_name}%")
                        )
                        name_result = await db.execute(name_query)
                        potential_matches = name_result.scalars().all()
                        
                        for match in potential_matches:
                            if match.id != candidate_id:
                                colleagues.append({
                                    "candidate": match,
                                    "relationship_type": "direct_colleague",
                                    "shared_companies": [exp.company],
                                    "mentioned_in": exp.company
                                })
            
            if include_potential:
                # Find potential colleagues (same company, overlapping dates)
                for base_exp in base_experiences:
                    overlapping_query = select(WorkExperience).options(
                        selectinload(WorkExperience.candidate)
                    ).where(
                        and_(
                            WorkExperience.candidate_id != candidate_id,
                            WorkExperience.company == base_exp.company,
                            # Check for date overlap
                            or_(
                                and_(
                                    WorkExperience.start_date <= (base_exp.end_date or datetime.now()),
                                    WorkExperience.end_date >= base_exp.start_date
                                ),
                                and_(
                                    WorkExperience.start_date <= (base_exp.end_date or datetime.now()),
                                    WorkExperience.end_date.is_(None),
                                    base_exp.end_date.is_(None)
                                )
                            )
                        )
                    )
                    
                    overlapping_result = await db.execute(overlapping_query)
                    overlapping_experiences = overlapping_result.scalars().all()
                    
                    for overlap_exp in overlapping_experiences:
                        # Calculate date overlap
                        overlap_info = self._calculate_date_overlap(
                            base_exp, overlap_exp, min_overlap_months
                        )
                        
                        if overlap_info["overlap_months"] >= min_overlap_months:
                            # Check if already added as direct colleague
                            already_added = any(
                                c["candidate"].id == overlap_exp.candidate.id 
                                for c in colleagues
                            )
                            
                            if not already_added:
                                colleagues.append({
                                    "candidate": overlap_exp.candidate,
                                    "relationship_type": "former_colleague" if overlap_exp.end_date else "current_colleague",
                                    "shared_companies": [base_exp.company],
                                    "date_overlap": overlap_info
                                })
            
            return colleagues
    
    async def smart_search(
        self,
        query: str,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """Intelligent search using Claude API to interpret queries"""
        
        try:
            # Use Claude to interpret the search query
            interpretation = await self.claude_service.interpret_search_query(query)
            
            # Extract search criteria
            criteria = interpretation.get("extracted_criteria", {})
            search_type = interpretation.get("search_intent", {}).get("type", "general")
            
            results = []
            sql_query = ""
            
            if search_type == "skill_based_search":
                skills = criteria.get("skills", [])
                if skills:
                    results = await self.search_by_skills(skills, limit=max_results)
                    sql_query = f"Skills search: {', '.join(skills)}"
            
            elif search_type == "department_search":
                department = criteria.get("department", "")
                seniority = criteria.get("experience_level", None)
                if department:
                    results = await self.search_by_department(
                        department, seniority, limit=max_results
                    )
                    sql_query = f"Department search: {department}"
            
            else:
                # Fallback to general skill search
                skills = self._extract_search_keywords(query)
                if skills:
                    results = await self.search_by_skills(skills, limit=max_results)
                    sql_query = f"Keyword search: {', '.join(skills)}"
            
            return {
                "results": results,
                "interpretation": interpretation,
                "sql_query": sql_query,
                "total_results": len(results)
            }
            
        except Exception as e:
            # Fallback to basic search
            skills = self._extract_search_keywords(query)
            results = await self.search_by_skills(skills, limit=max_results)
            
            return {
                "results": results,
                "fallback_used": True,
                "error": str(e),
                "sql_query": f"Fallback keyword search: {', '.join(skills)}"
            }
    
    async def advanced_search(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced search with multiple filters"""
        
        async with get_db() as db:
            query = select(Candidate).options(
                selectinload(Candidate.resumes),
                selectinload(Candidate.work_experiences)
            )
            
            # Apply filters
            if "skills" in filters:
                # Join with resumes and filter by skills
                query = query.join(Resume).where(
                    Resume.skills.contains(filters["skills"])
                )
            
            if "department" in filters:
                query = query.join(WorkExperience).where(
                    WorkExperience.department.ilike(f"%{filters['department']}%")
                )
            
            if "experience_years" in filters:
                query = query.where(
                    Candidate.total_experience_years >= filters["experience_years"]
                )
            
            if "location" in filters:
                query = query.where(
                    Candidate.location.ilike(f"%{filters['location']}%")
                )
            
            result = await db.execute(query)
            return result.scalars().unique().all()
    
    async def search_with_pagination(
        self,
        query: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Search with pagination support"""
        
        offset = (page - 1) * page_size
        skills = self._extract_search_keywords(query)
        
        results = await self.search_by_skills(skills, limit=page_size, offset=offset)
        
        # Get total count (simplified - in production, use a separate count query)
        total_results = await self.search_by_skills(skills, limit=1000)
        total = len(total_results)
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def _calculate_skill_match_score(
        self, 
        candidate_skills: List[str], 
        search_skills: List[str]
    ) -> float:
        """Calculate skill match score between candidate and search"""
        
        if not candidate_skills or not search_skills:
            return 0.0
        
        # Normalize skills (lowercase, strip)
        candidate_skills_norm = [s.lower().strip() for s in candidate_skills]
        search_skills_norm = [s.lower().strip() for s in search_skills]
        
        # Calculate exact matches
        exact_matches = len(set(candidate_skills_norm) & set(search_skills_norm))
        
        # Calculate partial matches (substring matching)
        partial_matches = 0
        for search_skill in search_skills_norm:
            for candidate_skill in candidate_skills_norm:
                if search_skill in candidate_skill or candidate_skill in search_skill:
                    partial_matches += 0.5
                    break
        
        # Calculate score
        total_matches = exact_matches + partial_matches
        max_possible = len(search_skills_norm)
        
        return min(total_matches / max_possible, 1.0)
    
    def _calculate_similarity_score(self, resume1: Resume, resume2: Resume) -> float:
        """Calculate overall similarity score between two resumes"""
        
        scores = []
        
        # Skill similarity
        if resume1.skills and resume2.skills:
            skill_score = self._calculate_skill_match_score(resume1.skills, resume2.skills)
            scores.append(skill_score * 0.4)  # 40% weight
        
        # Experience level similarity
        if hasattr(resume1.candidate, 'total_experience_years') and hasattr(resume2.candidate, 'total_experience_years'):
            exp1 = resume1.candidate.total_experience_years or 0
            exp2 = resume2.candidate.total_experience_years or 0
            
            if max(exp1, exp2) > 0:
                exp_score = 1 - abs(exp1 - exp2) / max(exp1, exp2, 10)  # Normalize by max 10 years
                scores.append(exp_score * 0.3)  # 30% weight
        
        # Add more similarity factors as needed
        
        return sum(scores) if scores else 0.0
    
    def _get_match_reasons(
        self, 
        base_candidate: Candidate, 
        base_resume: Resume,
        candidate: Candidate, 
        resume: Resume
    ) -> Dict[str, Any]:
        """Get detailed reasons for candidate match"""
        
        reasons = {
            "shared_skills": [],
            "shared_departments": [],
            "similar_experience": False
        }
        
        # Shared skills
        if base_resume.skills and resume.skills:
            shared = set(base_resume.skills) & set(resume.skills)
            reasons["shared_skills"] = list(shared)
        
        # Shared departments
        base_depts = [exp.department for exp in base_candidate.work_experiences if exp.department]
        candidate_depts = [exp.department for exp in candidate.work_experiences if exp.department]
        shared_depts = set(base_depts) & set(candidate_depts)
        reasons["shared_departments"] = list(shared_depts)
        
        # Similar experience level
        base_exp = base_candidate.total_experience_years or 0
        cand_exp = candidate.total_experience_years or 0
        if abs(base_exp - cand_exp) <= 2:  # Within 2 years
            reasons["similar_experience"] = True
        
        return reasons
    
    def _calculate_date_overlap(
        self, 
        exp1: WorkExperience, 
        exp2: WorkExperience,
        min_months: int
    ) -> Dict[str, Any]:
        """Calculate date overlap between two work experiences"""
        
        start1 = exp1.start_date
        end1 = exp1.end_date or datetime.now()
        start2 = exp2.start_date  
        end2 = exp2.end_date or datetime.now()
        
        # Calculate overlap
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start <= overlap_end:
            overlap_days = (overlap_end - overlap_start).days
            overlap_months = overlap_days / 30.44  # Average days per month
            
            return {
                "start_date": overlap_start.isoformat(),
                "end_date": overlap_end.isoformat(),
                "overlap_months": round(overlap_months, 1),
                "meets_minimum": overlap_months >= min_months
            }
        
        return {
            "overlap_months": 0,
            "meets_minimum": False
        }
    
    def _extract_search_keywords(self, query: str) -> List[str]:
        """Extract searchable keywords from query string"""
        
        # Common programming languages and technologies
        tech_keywords = [
            "python", "javascript", "java", "react", "node", "angular", "vue",
            "fastapi", "django", "flask", "express", "spring", "rails",
            "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
            "aws", "gcp", "azure", "git", "jenkins", "terraform"
        ]
        
        # Extract words from query
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter for tech keywords and common terms
        keywords = []
        for word in words:
            if len(word) >= 3 and (word in tech_keywords or word.endswith('js') or word.endswith('py')):
                keywords.append(word.title())  # Capitalize for consistency
        
        # If no tech keywords found, use all significant words
        if not keywords:
            keywords = [word.title() for word in words if len(word) >= 3]
        
        return keywords[:5]  # Limit to 5 keywords
    
    def _validate_search_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate search parameters"""
        
        if "page" in params and params["page"] < 1:
            return False
        
        if "page_size" in params and (params["page_size"] < 1 or params["page_size"] > 100):
            return False
        
        return True
    
    async def _query_database(self, query_params: Dict[str, Any]) -> List[Any]:
        """Execute database query with parameters"""
        # This is a placeholder for the actual database query implementation
        # In the real implementation, this would build and execute SQL queries
        return []