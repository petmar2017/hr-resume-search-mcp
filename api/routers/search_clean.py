"""
Search API Routes for HR Resume System
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text, cast, String
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json

from ..database import get_db
from ..auth import get_current_user
from ..schemas import (
    SearchRequest, SearchResponse, SearchResult,
    SmartSearchRequest, SmartSearchResponse,
    CandidateAnalytics, ErrorResponse, SearchType
)
from ..models import User, Candidate, Resume, WorkExperience, SearchHistory
from ..config import settings
from ..middleware.metrics_middleware import get_search_metrics_collector, get_db_metrics_tracker

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search"]
)


@router.get("/skills")
async def search_by_skills(
    skills: str = Query(..., description="Comma-separated list of skills"),
    min_score: float = Query(0.3, description="Minimum match score"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search candidates by skills"""
    try:
        skills_list = [skill.strip() for skill in skills.split(",")]
        
        # Import search service
        from ..services.search_service import SearchService
        search_service = SearchService()
        
        results = await search_service.search_by_skills(
            skills_list, min_score, limit, offset
        )
        
        return {
            "success": True,
            "results": results,
            "total_results": len(results),
            "query": skills,
            "processing_time_ms": 100  # Placeholder
        }
    except Exception as e:
        logger.error(f"Skills search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/department")
async def search_by_department(
    department: str = Query(..., description="Department name"),
    seniority: Optional[str] = Query(None, description="Seniority level"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search candidates by department"""
    try:
        from ..services.search_service import SearchService
        search_service = SearchService()
        
        results = await search_service.search_by_department(
            department, seniority, limit
        )
        
        return {
            "success": True,
            "results": results,
            "total_results": len(results),
            "query": department,
            "processing_time_ms": 100
        }
    except Exception as e:
        logger.error(f"Department search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/colleagues")
async def search_colleagues(
    candidate_id: int = Query(..., description="Base candidate ID"),
    include_potential: bool = Query(True, description="Include potential colleagues"),
    min_overlap_months: int = Query(3, description="Minimum overlap in months"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Find colleagues of a candidate"""
    try:
        from ..services.search_service import SearchService
        search_service = SearchService()
        
        results = await search_service.search_colleagues(
            candidate_id, include_potential, min_overlap_months
        )
        
        return {
            "success": True,
            "results": results,
            "total_results": len(results),
            "processing_time_ms": 100
        }
    except Exception as e:
        logger.error(f"Colleagues search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{candidate_id}")
async def search_similar_candidates(
    candidate_id: int,
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Find similar candidates"""
    try:
        from ..services.search_service import SearchService
        search_service = SearchService()
        
        results = await search_service.search_similar_candidates(
            candidate_id, limit
        )
        
        return {
            "success": True,
            "results": results,
            "total_results": len(results),
            "processing_time_ms": 100
        }
    except Exception as e:
        logger.error(f"Similar candidates search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart")
async def smart_search_with_claude(
    query: str,
    max_results: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Smart search using Claude AI to interpret natural language queries"""
    try:
        from ..services.search_service import SearchService
        search_service = SearchService()
        
        results = await search_service.smart_search(query, max_results)
        
        return {
            "success": True,
            "results": results.get("results", []),
            "total_results": results.get("total_results", 0),
            "interpretation": results.get("interpretation", {}),
            "sql_query": results.get("sql_query", ""),
            "processing_time_ms": 150
        }
    except Exception as e:
        logger.error(f"Smart search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SearchService:
    """
    Service class for handling search operations
    """
    
    @staticmethod
    def calculate_match_score(
        candidate: Candidate,
        resume: Resume,
        search_criteria: Dict[str, Any]
    ) -> float:
        """
        Calculate match score for a candidate based on search criteria
        """
        score = 0.0
        max_score = 0.0
        
        # Skills matching (40% weight)
        if search_criteria.get("skills"):
            max_score += 0.4
            required_skills = set(search_criteria["skills"])
            candidate_skills = set(resume.skills or [])
            
            if required_skills and candidate_skills:
                matching_skills = required_skills.intersection(candidate_skills)
                score += (len(matching_skills) / len(required_skills)) * 0.4
        
        # Experience matching (30% weight)
        if search_criteria.get("min_experience_years"):
            max_score += 0.3
            if candidate.total_experience_years:
                if candidate.total_experience_years >= search_criteria["min_experience_years"]:
                    score += 0.3
                else:
                    # Partial score based on how close they are
                    ratio = candidate.total_experience_years / search_criteria["min_experience_years"]
                    score += ratio * 0.3
        
        # Company matching (15% weight)
        if search_criteria.get("companies"):
            max_score += 0.15
            target_companies = set(search_criteria["companies"])
            worked_companies = set()
            
            for exp in candidate.work_experiences:
                worked_companies.add(exp.company)
            
            if target_companies and worked_companies:
                matching_companies = target_companies.intersection(worked_companies)
                score += (len(matching_companies) / len(target_companies)) * 0.15
        
        # Department matching (15% weight)
        if search_criteria.get("departments"):
            max_score += 0.15
            target_departments = set(search_criteria["departments"])
            worked_departments = set()
            
            for exp in candidate.work_experiences:
                if exp.department:
                    worked_departments.add(exp.department)
            
            if target_departments and worked_departments:
                matching_departments = target_departments.intersection(worked_departments)
                score += (len(matching_departments) / len(target_departments)) * 0.15
        
        # Normalize score to 0-1 range
        if max_score > 0:
            return min(score / max_score, 1.0)
        return 0.0
    
    @staticmethod
    def find_colleagues(
        db: Session,
        candidate_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find colleagues who worked with a candidate
        """
        # Get the candidate's work experiences
        work_experiences = db.query(WorkExperience).filter(
            WorkExperience.candidate_id == candidate_id
        ).all()
        
        colleagues_data = []
        
        for exp in work_experiences:
            # Find other candidates who worked at the same company during overlapping periods
            overlapping_experiences = db.query(WorkExperience).filter(
                WorkExperience.candidate_id != candidate_id,
                WorkExperience.company == exp.company,
                or_(
                    # Their start date is between our candidate's employment period
                    and_(
                        WorkExperience.start_date >= exp.start_date,
                        WorkExperience.start_date <= (exp.end_date if exp.end_date else datetime.utcnow())
                    ),
                    # Their end date is between our candidate's employment period
                    and_(
                        WorkExperience.end_date >= exp.start_date,
                        WorkExperience.end_date <= (exp.end_date if exp.end_date else datetime.utcnow())
                    ),
                    # They started before and ended after (full overlap)
                    and_(
                        WorkExperience.start_date <= exp.start_date,
                        or_(
                            WorkExperience.end_date >= (exp.end_date if exp.end_date else datetime.utcnow()),
                            WorkExperience.is_current == True
                        )
                    )
                )
            )
            
            # If department is specified, filter by department
            if exp.department:
                overlapping_experiences = overlapping_experiences.filter(
                    WorkExperience.department == exp.department
                )
            
            for colleague_exp in overlapping_experiences.all():
                colleague = db.query(Candidate).filter(
                    Candidate.id == colleague_exp.candidate_id
                ).first()
                
                if colleague:
                    # Calculate overlap duration
                    overlap_start = max(exp.start_date, colleague_exp.start_date)
                    overlap_end = min(
                        exp.end_date if exp.end_date else datetime.utcnow(),
                        colleague_exp.end_date if colleague_exp.end_date else datetime.utcnow()
                    )
                    overlap_months = (overlap_end.year - overlap_start.year) * 12 + (overlap_end.month - overlap_start.month)
                    
                    colleagues_data.append({
                        "candidate": colleague,
                        "company": exp.company,
                        "department": exp.department,
                        "overlap_months": overlap_months,
                        "positions": {
                            "original": exp.position,
                            "colleague": colleague_exp.position
                        }
                    })
        
