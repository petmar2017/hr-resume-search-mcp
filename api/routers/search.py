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
        
        # Sort by overlap duration and limit results
        colleagues_data.sort(key=lambda x: x["overlap_months"], reverse=True)
        return colleagues_data[:limit]


@router.post("/candidates", response_model=SearchResponse)
async def search_candidates(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Smart candidate search with multiple criteria
    """
    start_time = datetime.utcnow()
    
    try:
        # Build base query
        query = db.query(Candidate, Resume).join(
            Resume, Resume.candidate_id == Candidate.id
        ).filter(
            Candidate.is_active == True,
            Resume.parsing_status == "completed"
        )
        
        # Apply filters based on search type
        if search_request.search_type == SearchType.SKILLS_MATCH:
            if search_request.skills:
                # Search for candidates with matching skills
                skills_filter = []
                for skill in search_request.skills:
                    skills_filter.append(
                        func.jsonb_contains(
                            cast(Resume.skills, JSONB),
                            cast(json.dumps([skill]), JSONB)
                        )
                    )
                if skills_filter:
                    query = query.filter(or_(*skills_filter))
        
        elif search_request.search_type == SearchType.SAME_DEPARTMENT:
            if search_request.departments:
                # Join with WorkExperience to search by department
                query = query.join(
                    WorkExperience, WorkExperience.candidate_id == Candidate.id
                ).filter(
                    WorkExperience.department.in_(search_request.departments)
                )
        
        elif search_request.search_type == SearchType.EXPERIENCE_MATCH:
            # Filter by experience years
            if search_request.min_experience_years:
                query = query.filter(
                    Candidate.total_experience_years >= search_request.min_experience_years
                )
            if search_request.max_experience_years:
                query = query.filter(
                    Candidate.total_experience_years <= search_request.max_experience_years
                )
        
        # Apply additional filters
        if search_request.companies:
            query = query.join(
                WorkExperience, WorkExperience.candidate_id == Candidate.id
            ).filter(
                WorkExperience.company.in_(search_request.companies)
            )
        
        if search_request.locations:
            query = query.filter(
                Candidate.location.in_(search_request.locations)
            )
        
        if search_request.education_level:
            # Search in education JSON field
            query = query.filter(
                func.jsonb_path_exists(
                    cast(Resume.education, JSONB),
                    f'$[*] ? (@.level == "{search_request.education_level}")'
                )
            )
        
        # Keyword search in parsed_data
        if search_request.query:
            keyword = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    cast(Resume.parsed_data, String).ilike(keyword),
                    Candidate.full_name.ilike(keyword),
                    Candidate.headline.ilike(keyword),
                    Candidate.summary.ilike(keyword)
                )
            )
        
        # Get total count before pagination
        total_results = query.count()
        
        # Apply pagination
        query = query.offset(search_request.offset).limit(search_request.limit)
        
        # Execute query
        results = query.all()
        
        # Build response
        search_results = []
        for candidate, resume in results:
            # Calculate match score
            match_score = SearchService.calculate_match_score(
                candidate, 
                resume,
                {
                    "skills": search_request.skills,
                    "min_experience_years": search_request.min_experience_years,
                    "companies": search_request.companies,
                    "departments": search_request.departments
                }
            )
            
            # Build match reasons
            match_reasons = []
            if search_request.skills:
                matching_skills = set(search_request.skills).intersection(set(resume.skills or []))
                if matching_skills:
                    match_reasons.append(f"Skills: {', '.join(matching_skills)}")
            
            if search_request.companies:
                for exp in candidate.work_experiences:
                    if exp.company in search_request.companies:
                        match_reasons.append(f"Worked at {exp.company}")
                        break
            
            if search_request.departments:
                for exp in candidate.work_experiences:
                    if exp.department in search_request.departments:
                        match_reasons.append(f"Worked in {exp.department}")
                        break
            
            search_results.append(SearchResult(
                candidate_id=candidate.uuid,
                resume_id=resume.uuid,
                full_name=candidate.full_name,
                current_position=candidate.current_position,
                current_company=candidate.current_company,
                total_experience_years=candidate.total_experience_years,
                match_score=match_score,
                match_reasons=match_reasons,
                highlights={
                    "skills": resume.skills[:5] if resume.skills else [],
                    "location": candidate.location,
                    "headline": candidate.headline
                }
            ))
        
        # Sort by match score
        search_results.sort(key=lambda x: x.match_score, reverse=True)
        
        # Log search history
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        search_history = SearchHistory(
            query=search_request.query or "",
            search_type=search_request.search_type.value,
            filters=search_request.model_dump(exclude={"query", "search_type"}),
            results_count=total_results,
            results=[r.model_dump() for r in search_results[:5]],  # Store top 5 results
            processing_time_ms=processing_time,
            user_id=current_user.id
        )
        db.add(search_history)
        db.commit()
        
        return SearchResponse(
            query=search_request.query or "",
            search_type=search_request.search_type,
            total_results=total_results,
            results=search_results,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/similar", response_model=SearchResponse)
async def find_similar_profiles(
    candidate_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Find profiles similar to a given candidate
    """
    start_time = datetime.utcnow()
    
    try:
        # Get the reference candidate
        reference_candidate = db.query(Candidate).filter(
            Candidate.uuid == candidate_id
        ).first()
        
        if not reference_candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Get reference resume
        reference_resume = db.query(Resume).filter(
            Resume.candidate_id == reference_candidate.id
        ).first()
        
        if not reference_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found for candidate"
            )
        
        # Build similarity query
        query = db.query(Candidate, Resume).join(
            Resume, Resume.candidate_id == Candidate.id
        ).filter(
            Candidate.id != reference_candidate.id,
            Candidate.is_active == True,
            Resume.parsing_status == "completed"
        )
        
        # Find candidates with similar skills
        if reference_resume.skills:
            skills_filters = []
            for skill in reference_resume.skills[:10]:  # Use top 10 skills
                skills_filters.append(
                    func.jsonb_contains(
                        cast(Resume.skills, JSONB),
                        cast(json.dumps([skill]), JSONB)
                    )
                )
            if skills_filters:
                query = query.filter(or_(*skills_filters))
        
        # Similar experience level (within 2 years)
        if reference_candidate.total_experience_years:
            query = query.filter(
                Candidate.total_experience_years.between(
                    reference_candidate.total_experience_years - 2,
                    reference_candidate.total_experience_years + 2
                )
            )
        
        # Similar companies or industries
        reference_companies = set()
        reference_departments = set()
        for exp in reference_candidate.work_experiences:
            reference_companies.add(exp.company)
            if exp.department:
                reference_departments.add(exp.department)
        
        if reference_companies:
            query = query.join(
                WorkExperience, WorkExperience.candidate_id == Candidate.id
            ).filter(
                or_(
                    WorkExperience.company.in_(reference_companies),
                    WorkExperience.department.in_(reference_departments) if reference_departments else True
                )
            )
        
        # Limit results
        query = query.limit(limit)
        results = query.all()
        
        # Calculate similarity scores and build response
        search_results = []
        for candidate, resume in results:
            # Calculate similarity score
            similarity_score = 0.0
            match_reasons = []
            
            # Skills similarity (40% weight)
            if reference_resume.skills and resume.skills:
                common_skills = set(reference_resume.skills).intersection(set(resume.skills))
                if common_skills:
                    similarity_score += (len(common_skills) / len(reference_resume.skills)) * 0.4
                    match_reasons.append(f"Common skills: {', '.join(list(common_skills)[:3])}")
            
            # Experience similarity (30% weight)
            if reference_candidate.total_experience_years and candidate.total_experience_years:
                exp_diff = abs(reference_candidate.total_experience_years - candidate.total_experience_years)
                if exp_diff <= 2:
                    similarity_score += ((2 - exp_diff) / 2) * 0.3
                    match_reasons.append(f"Similar experience: {candidate.total_experience_years} years")
            
            # Company/Department similarity (30% weight)
            candidate_companies = set()
            candidate_departments = set()
            for exp in candidate.work_experiences:
                candidate_companies.add(exp.company)
                if exp.department:
                    candidate_departments.add(exp.department)
            
            common_companies = reference_companies.intersection(candidate_companies)
            common_departments = reference_departments.intersection(candidate_departments)
            
            if common_companies:
                similarity_score += 0.2
                match_reasons.append(f"Worked at: {', '.join(list(common_companies)[:2])}")
            
            if common_departments:
                similarity_score += 0.1
                match_reasons.append(f"Same department: {', '.join(list(common_departments)[:2])}")
            
            search_results.append(SearchResult(
                candidate_id=candidate.uuid,
                resume_id=resume.uuid,
                full_name=candidate.full_name,
                current_position=candidate.current_position,
                current_company=candidate.current_company,
                total_experience_years=candidate.total_experience_years,
                match_score=min(similarity_score, 1.0),
                match_reasons=match_reasons,
                highlights={
                    "skills": resume.skills[:5] if resume.skills else [],
                    "location": candidate.location,
                    "headline": candidate.headline
                }
            ))
        
        # Sort by similarity score
        search_results.sort(key=lambda x: x.match_score, reverse=True)
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return SearchResponse(
            query=f"Similar to {reference_candidate.full_name}",
            search_type=SearchType.SIMILAR_CANDIDATES,
            total_results=len(search_results),
            results=search_results,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar profiles search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/colleagues", response_model=SearchResponse)
async def find_former_colleagues(
    candidate_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Find former colleagues who worked with a candidate
    """
    start_time = datetime.utcnow()
    
    try:
        # Get the reference candidate
        reference_candidate = db.query(Candidate).filter(
            Candidate.uuid == candidate_id
        ).first()
        
        if not reference_candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Find colleagues
        colleagues_data = SearchService.find_colleagues(
            db, 
            reference_candidate.id, 
            limit
        )
        
        # Build response
        search_results = []
        for colleague_info in colleagues_data:
            colleague = colleague_info["candidate"]
            
            # Get colleague's resume
            colleague_resume = db.query(Resume).filter(
                Resume.candidate_id == colleague.id
            ).first()
            
            match_reasons = [
                f"Worked together at {colleague_info['company']}",
                f"Overlap: {colleague_info['overlap_months']} months"
            ]
            
            if colleague_info["department"]:
                match_reasons.append(f"Same department: {colleague_info['department']}")
            
            # Calculate a relevance score based on overlap duration
            # Normalize to 0-1 scale (assuming max overlap of 60 months / 5 years)
            match_score = min(colleague_info["overlap_months"] / 60, 1.0)
            
            search_results.append(SearchResult(
                candidate_id=colleague.uuid,
                resume_id=colleague_resume.uuid if colleague_resume else "",
                full_name=colleague.full_name,
                current_position=colleague.current_position,
                current_company=colleague.current_company,
                total_experience_years=colleague.total_experience_years,
                match_score=match_score,
                match_reasons=match_reasons,
                highlights={
                    "company": colleague_info["company"],
                    "department": colleague_info["department"],
                    "overlap_months": colleague_info["overlap_months"],
                    "positions": colleague_info["positions"]
                }
            ))
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log search history
        search_history = SearchHistory(
            query=f"Colleagues of {reference_candidate.full_name}",
            search_type=SearchType.WORKED_WITH.value,
            filters={"candidate_id": candidate_id, "limit": limit},
            results_count=len(search_results),
            results=[r.model_dump() for r in search_results[:5]],
            processing_time_ms=processing_time,
            user_id=current_user.id
        )
        db.add(search_history)
        db.commit()
        
        return SearchResponse(
            query=f"Colleagues of {reference_candidate.full_name}",
            search_type=SearchType.WORKED_WITH,
            total_results=len(search_results),
            results=search_results,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Colleagues search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/filters")
async def get_available_filters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get available search filters with counts
    """
    try:
        # Get unique companies
        companies_query = db.query(
            WorkExperience.company,
            func.count(WorkExperience.candidate_id.distinct()).label("count")
        ).group_by(WorkExperience.company).order_by(func.count(WorkExperience.candidate_id.distinct()).desc()).limit(50)
        
        companies = [
            {"name": company, "count": count}
            for company, count in companies_query.all()
        ]
        
        # Get unique departments
        departments_query = db.query(
            WorkExperience.department,
            func.count(WorkExperience.candidate_id.distinct()).label("count")
        ).filter(
            WorkExperience.department.isnot(None)
        ).group_by(WorkExperience.department).order_by(func.count(WorkExperience.candidate_id.distinct()).desc()).limit(50)
        
        departments = [
            {"name": dept, "count": count}
            for dept, count in departments_query.all()
        ]
        
        # Get unique locations
        locations_query = db.query(
            Candidate.location,
            func.count(Candidate.id).label("count")
        ).filter(
            Candidate.location.isnot(None)
        ).group_by(Candidate.location).order_by(func.count(Candidate.id).desc()).limit(50)
        
        locations = [
            {"name": location, "count": count}
            for location, count in locations_query.all()
        ]
        
        # Get skills (from resumes)
        # This is a simplified version - in production, you'd want to aggregate and normalize skills
        skills_sample = db.query(Resume.skills).filter(
            Resume.skills.isnot(None)
        ).limit(100).all()
        
        all_skills = []
        for (skills_list,) in skills_sample:
            if skills_list:
                all_skills.extend(skills_list)
        
        # Count skill occurrences
        skill_counts = {}
        for skill in all_skills:
            if isinstance(skill, str):
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Sort and limit skills
        top_skills = sorted(
            [{"name": skill, "count": count} for skill, count in skill_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:50]
        
        # Get experience range
        experience_stats = db.query(
            func.min(Candidate.total_experience_years).label("min"),
            func.max(Candidate.total_experience_years).label("max"),
            func.avg(Candidate.total_experience_years).label("avg")
        ).filter(
            Candidate.total_experience_years.isnot(None)
        ).first()
        
        # Get total counts
        total_candidates = db.query(Candidate).filter(Candidate.is_active == True).count()
        total_resumes = db.query(Resume).filter(Resume.parsing_status == "completed").count()
        
        return {
            "companies": companies,
            "departments": departments,
            "locations": locations,
            "skills": top_skills,
            "experience_range": {
                "min": experience_stats.min or 0,
                "max": experience_stats.max or 0,
                "average": round(experience_stats.avg or 0, 1)
            },
            "education_levels": [
                {"value": "high_school", "label": "High School"},
                {"value": "bachelors", "label": "Bachelor's Degree"},
                {"value": "masters", "label": "Master's Degree"},
                {"value": "phd", "label": "PhD"},
                {"value": "other", "label": "Other"}
            ],
            "search_types": [
                {"value": "similar_candidates", "label": "Similar Candidates"},
                {"value": "same_department", "label": "Same Department/Desk"},
                {"value": "worked_with", "label": "Worked Together"},
                {"value": "skills_match", "label": "Skills Match"},
                {"value": "experience_match", "label": "Experience Match"}
            ],
            "statistics": {
                "total_candidates": total_candidates,
                "total_resumes": total_resumes,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Get filters error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get filters: {str(e)}"
        )


@router.post("/smart", response_model=SmartSearchResponse)
async def smart_search(
    search_request: SmartSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SmartSearchResponse:
    """
    Natural language search powered by AI interpretation
    """
    start_time = datetime.utcnow()
    
    try:
        # TODO: Integrate with Claude API to interpret natural language query
        # For now, implement basic keyword extraction
        
        query_lower = search_request.query.lower()
        
        # Interpret the search intent
        interpreted_query = {
            "original_query": search_request.query,
            "detected_intent": None,
            "extracted_criteria": {}
        }
        
        # Detect search type from query
        if "similar to" in query_lower or "like" in query_lower:
            interpreted_query["detected_intent"] = "similar_candidates"
        elif "worked with" in query_lower or "colleagues" in query_lower:
            interpreted_query["detected_intent"] = "colleagues"
        elif "same department" in query_lower or "same desk" in query_lower:
            interpreted_query["detected_intent"] = "same_department"
        elif "skills" in query_lower or "experience in" in query_lower:
            interpreted_query["detected_intent"] = "skills_match"
        else:
            interpreted_query["detected_intent"] = "general_search"
        
        # Extract potential skills from query
        # This is a simplified version - production would use NLP
        common_skills = ["python", "java", "javascript", "react", "sql", "aws", "docker", "kubernetes"]
        detected_skills = [skill for skill in common_skills if skill in query_lower]
        if detected_skills:
            interpreted_query["extracted_criteria"]["skills"] = detected_skills
        
        # Extract experience years if mentioned
        import re
        years_pattern = r'(\d+)\+?\s*years?'
        years_match = re.search(years_pattern, query_lower)
        if years_match:
            interpreted_query["extracted_criteria"]["min_experience_years"] = int(years_match.group(1))
        
        # Build search request based on interpretation
        search_type = SearchType.SKILLS_MATCH  # Default
        if interpreted_query["detected_intent"] == "same_department":
            search_type = SearchType.SAME_DEPARTMENT
        elif interpreted_query["detected_intent"] == "colleagues":
            search_type = SearchType.WORKED_WITH
        
        # Perform the search
        internal_search = SearchRequest(
            query=search_request.query,
            search_type=search_type,
            skills=interpreted_query["extracted_criteria"].get("skills"),
            min_experience_years=interpreted_query["extracted_criteria"].get("min_experience_years"),
            limit=search_request.limit
        )
        
        # Reuse the main search logic
        search_response = await search_candidates(internal_search, current_user, db)
        
        # Generate AI reasoning if requested
        reasoning = None
        if search_request.include_reasoning:
            reasoning = (
                f"I interpreted your query as looking for {interpreted_query['detected_intent'].replace('_', ' ')}. "
            )
            if detected_skills:
                reasoning += f"I detected these skills: {', '.join(detected_skills)}. "
            if years_match:
                reasoning += f"I found you're looking for candidates with at least {years_match.group(1)} years of experience. "
            reasoning += f"I found {search_response.total_results} matching candidates."
        
        # Generate suggested queries
        suggested_queries = []
        if detected_skills:
            suggested_queries.append(f"Show me senior {detected_skills[0]} developers")
        suggested_queries.append("Find candidates who worked at top tech companies")
        suggested_queries.append("Show me candidates with leadership experience")
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return SmartSearchResponse(
            interpreted_query=interpreted_query,
            results=search_response.results,
            reasoning=reasoning,
            suggested_queries=suggested_queries,
            processing_time_ms=processing_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Smart search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Smart search failed: {str(e)}"
        )