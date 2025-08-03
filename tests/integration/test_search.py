"""
Integration Tests for Search Functionality
Tests all 5 search endpoints with complex search logic
"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import json

from tests.factories import (
    UserFactory, CandidateFactory, WorkExperienceFactory, 
    ResumeFactory, create_search_test_data
)
from api.models import Candidate, Resume, WorkExperience


class TestSearchEndpoints:
    """Integration tests for all search endpoints"""
    
    @pytest.fixture
    async def search_test_data(self, db_session: AsyncSession):
        """Create comprehensive test data for search functionality"""
        
        # Create HR user
        hr_user = UserFactory(email="hr@company.com", full_name="HR Manager")
        
        # Create Python Developer
        python_dev = CandidateFactory(
            full_name="Alice Python",
            email="alice@example.com",
            current_position="Senior Python Developer",
            current_company="Tech Corp",
            total_experience_years=5
        )
        
        python_work = WorkExperienceFactory(
            candidate_id=python_dev,
            company="Tech Corp",
            position="Senior Python Developer",
            department="Engineering",
            start_date=datetime(2020, 1, 1),
            end_date=None,
            is_current=True,
            technologies_used=["Python", "FastAPI", "PostgreSQL", "Docker"],
            colleagues=["Bob JavaScript", "Charlie Fullstack", "David Manager"]
        )
        
        python_resume = ResumeFactory(
            candidate_id=python_dev,
            uploaded_by_id=hr_user,
            skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
            parsing_status="completed",
            parsed_data={
                "personal_info": {
                    "name": "Alice Python",
                    "email": "alice@example.com",
                    "location": "San Francisco, CA"
                },
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Senior Python Developer",
                        "duration": "2020-present",
                        "department": "Engineering",
                        "responsibilities": ["Led API development", "Mentored junior developers"],
                        "technologies": ["Python", "FastAPI", "PostgreSQL"]
                    }
                ],
                "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
            }
        )
        
        # Create JavaScript Developer
        js_dev = CandidateFactory(
            full_name="Bob JavaScript",
            email="bob@example.com",
            current_position="Frontend Developer",
            current_company="StartupCo",
            total_experience_years=3
        )
        
        js_work = WorkExperienceFactory(
            candidate_id=js_dev,
            company="StartupCo",
            position="Frontend Developer",
            department="Engineering",
            start_date=datetime(2021, 6, 1),
            end_date=None,
            is_current=True,
            technologies_used=["JavaScript", "React", "Node.js", "CSS"],
            colleagues=["Alice Python", "Eve Designer"]
        )
        
        # Previous work at same company as Alice
        js_prev_work = WorkExperienceFactory(
            candidate_id=js_dev,
            company="Tech Corp",
            position="Junior Developer",
            department="Engineering",
            start_date=datetime(2019, 1, 1),
            end_date=datetime(2021, 5, 31),
            is_current=False,
            technologies_used=["JavaScript", "React"],
            colleagues=["Alice Python", "Charlie Fullstack"]
        )
        
        js_resume = ResumeFactory(
            candidate_id=js_dev,
            uploaded_by_id=hr_user,
            skills=["JavaScript", "React", "Node.js", "CSS", "HTML"],
            parsing_status="completed",
            parsed_data={
                "personal_info": {
                    "name": "Bob JavaScript",
                    "email": "bob@example.com",
                    "location": "Austin, TX"
                },
                "experience": [
                    {
                        "company": "StartupCo",
                        "position": "Frontend Developer",
                        "duration": "2021-present",
                        "department": "Engineering"
                    },
                    {
                        "company": "Tech Corp",
                        "position": "Junior Developer",
                        "duration": "2019-2021",
                        "department": "Engineering"
                    }
                ],
                "skills": ["JavaScript", "React", "Node.js", "CSS", "HTML"]
            }
        )
        
        # Create Full Stack Developer
        fullstack_dev = CandidateFactory(
            full_name="Charlie Fullstack",
            email="charlie@example.com",
            current_position="Full Stack Developer",
            current_company="MegaCorp",
            total_experience_years=7
        )
        
        fullstack_work = WorkExperienceFactory(
            candidate_id=fullstack_dev,
            company="MegaCorp",
            position="Full Stack Developer",
            department="Engineering",
            start_date=datetime(2018, 3, 1),
            end_date=None,
            is_current=True,
            technologies_used=["Python", "JavaScript", "PostgreSQL", "React", "Docker"],
            colleagues=["Frank Manager", "Grace Designer"]
        )
        
        fullstack_resume = ResumeFactory(
            candidate_id=fullstack_dev,
            uploaded_by_id=hr_user,
            skills=["Python", "JavaScript", "React", "PostgreSQL", "Docker", "AWS"],
            parsing_status="completed"
        )
        
        # Create Data Scientist (different department)
        data_scientist = CandidateFactory(
            full_name="Diana Data",
            email="diana@example.com",
            current_position="Data Scientist",
            current_company="DataCorp",
            total_experience_years=4
        )
        
        data_work = WorkExperienceFactory(
            candidate_id=data_scientist,
            company="DataCorp",
            position="Data Scientist",
            department="Data Science",
            start_date=datetime(2020, 1, 1),
            end_date=None,
            is_current=True,
            technologies_used=["Python", "Pandas", "TensorFlow", "SQL"],
            colleagues=["Helen Analyst", "Ivan Researcher"]
        )
        
        data_resume = ResumeFactory(
            candidate_id=data_scientist,
            uploaded_by_id=hr_user,
            skills=["Python", "Pandas", "TensorFlow", "SQL", "Statistics"],
            parsing_status="completed"
        )
        
        # Add all to session
        entities = [
            hr_user, python_dev, js_dev, fullstack_dev, data_scientist,
            python_work, js_work, js_prev_work, fullstack_work, data_work,
            python_resume, js_resume, fullstack_resume, data_resume
        ]
        
        for entity in entities:
            db_session.add(entity)
        
        await db_session.commit()
        
        return {
            'hr_user': hr_user,
            'python_dev': python_dev,
            'js_dev': js_dev,
            'fullstack_dev': fullstack_dev,
            'data_scientist': data_scientist,
            'all_candidates': [python_dev, js_dev, fullstack_dev, data_scientist]
        }
    
    @pytest.mark.asyncio
    async def test_search_by_skills(self, authenticated_client: AsyncClient, search_test_data):
        """Test /api/v1/search/skills endpoint"""
        
        # Search for Python skills
        response = await authenticated_client.get(
            "/api/v1/search/skills",
            params={"skills": "Python,FastAPI", "min_score": 0.5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total" in data
        assert data["total"] >= 2  # Alice (Python) and Charlie (Fullstack)
        
        # Verify scoring
        results = data["results"]
        for result in results:
            assert "candidate" in result
            assert "score" in result
            assert "matching_skills" in result
            assert result["score"] >= 0.5
            assert "Python" in result["matching_skills"]
        
        # Verify top result is Python specialist
        top_result = results[0]
        assert top_result["candidate"]["full_name"] == "Alice Python"
        assert top_result["score"] > 0.8  # High score for exact match
    
    @pytest.mark.asyncio
    async def test_search_similar_candidates(self, authenticated_client: AsyncClient, search_test_data):
        """Test /api/v1/search/similar/{candidate_id} endpoint"""
        
        python_dev = search_test_data['python_dev']
        
        response = await authenticated_client.get(
            f"/api/v1/search/similar/{python_dev.id}",
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "base_candidate" in data
        assert data["base_candidate"]["id"] == python_dev.id
        
        results = data["results"]
        
        # Should find Charlie (fullstack with Python) and maybe others
        found_fullstack = False
        for result in results:
            assert "candidate" in result
            assert "similarity_score" in result
            assert "match_reasons" in result
            assert result["candidate"]["id"] != python_dev.id  # Not self
            
            if result["candidate"]["full_name"] == "Charlie Fullstack":
                found_fullstack = True
                assert "Python" in result["match_reasons"]["shared_skills"]
                assert "Engineering" in result["match_reasons"]["shared_departments"]
        
        assert found_fullstack, "Should find Charlie as similar candidate"
    
    @pytest.mark.asyncio
    async def test_search_by_department(self, authenticated_client: AsyncClient, search_test_data):
        """Test /api/v1/search/department endpoint"""
        
        response = await authenticated_client.get(
            "/api/v1/search/department",
            params={"department": "Engineering", "seniority": "senior"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert data["total"] >= 3  # Alice, Bob, Charlie
        
        results = data["results"]
        engineering_candidates = ["Alice Python", "Bob JavaScript", "Charlie Fullstack"]
        
        for result in results:
            assert result["candidate"]["full_name"] in engineering_candidates
            assert "Engineering" in [exp["department"] for exp in result["experience"]]
    
    @pytest.mark.asyncio
    async def test_search_colleagues(self, authenticated_client: AsyncClient, search_test_data):
        """Test /api/v1/search/colleagues/{candidate_id} endpoint"""
        
        python_dev = search_test_data['python_dev']
        
        response = await authenticated_client.get(
            f"/api/v1/search/colleagues/{python_dev.id}",
            params={"include_potential": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "base_candidate" in data
        
        results = data["results"]
        
        # Should find Bob as colleague (worked at Tech Corp)
        found_bob = False
        for result in results:
            if result["candidate"]["full_name"] == "Bob JavaScript":
                found_bob = True
                assert "relationship_type" in result
                assert result["relationship_type"] in ["direct_colleague", "former_colleague"]
                assert "shared_companies" in result
                assert "Tech Corp" in result["shared_companies"]
                
                # Check date overlap
                assert "date_overlap" in result
                overlap = result["date_overlap"]
                assert overlap["start_date"] is not None
                assert overlap["end_date"] is not None
        
        assert found_bob, "Should find Bob as colleague"
    
    @pytest.mark.asyncio
    async def test_smart_search_with_claude(self, authenticated_client: AsyncClient, search_test_data):
        """Test /api/v1/search/smart endpoint with Claude integration"""
        
        # Mock Claude API response
        mock_claude_response = {
            "search_intent": {
                "type": "skill_based_search",
                "confidence": 0.9
            },
            "extracted_criteria": {
                "skills": ["Python", "API development"],
                "experience_level": "senior",
                "department": "Engineering"
            },
            "sql_strategy": "focus_on_skills_and_experience"
        }
        
        with patch('api.services.claude_service.ClaudeService.interpret_search_query') as mock_claude:
            mock_claude.return_value = mock_claude_response
            
            response = await authenticated_client.post(
                "/api/v1/search/smart",
                json={
                    "query": "Find senior Python developers with API experience",
                    "max_results": 10
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "results" in data
            assert "interpretation" in data
            assert "sql_query" in data
            
            # Verify Claude interpretation
            interpretation = data["interpretation"]
            assert interpretation["type"] == "skill_based_search"
            assert "Python" in interpretation["extracted_criteria"]["skills"]
            
            # Verify results
            results = data["results"]
            assert len(results) > 0
            
            # Should prioritize Alice (Python specialist)
            top_result = results[0]
            assert "Alice" in top_result["candidate"]["full_name"]
            
            mock_claude.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_skills_search_with_jsonb_queries(self, authenticated_client: AsyncClient, search_test_data):
        """Test JSONB queries in parsed_data fields"""
        
        response = await authenticated_client.get(
            "/api/v1/search/skills",
            params={
                "skills": "React,JavaScript",
                "search_parsed_data": True,
                "min_score": 0.3
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find Bob and Charlie who have React/JavaScript
        assert data["total"] >= 2
        
        results = data["results"]
        js_candidates = []
        
        for result in results:
            if "JavaScript" in result["matching_skills"] or "React" in result["matching_skills"]:
                js_candidates.append(result["candidate"]["full_name"])
        
        assert "Bob JavaScript" in js_candidates
        assert "Charlie Fullstack" in js_candidates
    
    @pytest.mark.asyncio
    async def test_colleague_detection_with_date_overlaps(self, authenticated_client: AsyncClient, search_test_data):
        """Test colleague detection with complex date range overlaps"""
        
        js_dev = search_test_data['js_dev']
        
        response = await authenticated_client.get(
            f"/api/v1/search/colleagues/{js_dev.id}",
            params={
                "min_overlap_months": 6,
                "include_potential": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        results = data["results"]
        
        # Find Alice (overlapped at Tech Corp)
        found_alice = False
        for result in results:
            if result["candidate"]["full_name"] == "Alice Python":
                found_alice = True
                
                # Verify date overlap calculation
                overlap = result["date_overlap"]
                assert "overlap_months" in overlap
                assert overlap["overlap_months"] >= 6
                
                # Verify shared company
                assert "Tech Corp" in result["shared_companies"]
                
                # Verify relationship details
                assert result["relationship_type"] in ["direct_colleague", "former_colleague"]
        
        assert found_alice, "Should detect Alice as colleague with date overlap"
    
    @pytest.mark.asyncio
    async def test_search_scoring_algorithm(self, authenticated_client: AsyncClient, search_test_data):
        """Test the scoring algorithm accuracy"""
        
        response = await authenticated_client.get(
            "/api/v1/search/skills",
            params={
                "skills": "Python,PostgreSQL,Docker",
                "include_scoring_details": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        results = data["results"]
        
        for result in results:
            assert "score_breakdown" in result
            breakdown = result["score_breakdown"]
            
            # Verify score components
            assert "skill_match_score" in breakdown
            assert "experience_score" in breakdown
            assert "seniority_bonus" in breakdown
            assert "total_score" in breakdown
            
            # Verify score calculation
            expected_total = (
                breakdown["skill_match_score"] + 
                breakdown["experience_score"] + 
                breakdown["seniority_bonus"]
            )
            assert abs(breakdown["total_score"] - expected_total) < 0.01
            
            # Verify skill matching
            if result["candidate"]["full_name"] == "Alice Python":
                # Alice should have high skill match for Python/PostgreSQL/Docker
                assert breakdown["skill_match_score"] > 0.7
                assert "Python" in result["matching_skills"]
                assert "PostgreSQL" in result["matching_skills"]
                assert "Docker" in result["matching_skills"]
    
    @pytest.mark.asyncio
    async def test_search_pagination_and_sorting(self, authenticated_client: AsyncClient, search_test_data):
        """Test search pagination and sorting options"""
        
        # Test with pagination
        response = await authenticated_client.get(
            "/api/v1/search/skills",
            params={
                "skills": "Python",
                "page": 1,
                "page_size": 2,
                "sort_by": "score",
                "sort_order": "desc"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "pagination" in data
        
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 2
        assert pagination["total_pages"] >= 1
        
        results = data["results"]
        assert len(results) <= 2
        
        # Verify sorting (scores should be descending)
        if len(results) > 1:
            assert results[0]["score"] >= results[1]["score"]
    
    @pytest.mark.asyncio
    async def test_search_filters_and_combinations(self, authenticated_client: AsyncClient, search_test_data):
        """Test advanced search filters and combinations"""
        
        response = await authenticated_client.get(
            "/api/v1/search/skills",
            params={
                "skills": "Python",
                "min_experience_years": 4,
                "departments": "Engineering",
                "locations": "San Francisco",
                "exclude_candidates": str(search_test_data['data_scientist'].id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        results = data["results"]
        
        for result in results:
            candidate = result["candidate"]
            
            # Should not include the excluded data scientist
            assert candidate["id"] != search_test_data['data_scientist'].id
            
            # Should have Python skills
            assert "Python" in result["matching_skills"]
            
            # Should have sufficient experience
            assert candidate["total_experience_years"] >= 4
    
    @pytest.mark.asyncio
    async def test_search_performance_and_caching(self, authenticated_client: AsyncClient, search_test_data):
        """Test search performance and caching behavior"""
        
        import time
        
        # First search (cache miss)
        start_time = time.time()
        response1 = await authenticated_client.get(
            "/api/v1/search/skills",
            params={"skills": "Python,FastAPI"}
        )
        first_time = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Second identical search (cache hit)
        start_time = time.time()
        response2 = await authenticated_client.get(
            "/api/v1/search/skills",
            params={"skills": "Python,FastAPI"}
        )
        second_time = time.time() - start_time
        
        assert response2.status_code == 200
        
        # Results should be identical
        assert response1.json() == response2.json()
        
        # Second request should be faster (cached)
        assert second_time < first_time * 0.8  # At least 20% faster
        
        # Check for cache headers
        assert "X-Cache-Status" in response2.headers
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, authenticated_client: AsyncClient):
        """Test search error handling"""
        
        # Test invalid candidate ID
        response = await authenticated_client.get("/api/v1/search/similar/99999")
        assert response.status_code == 404
        
        # Test invalid search parameters
        response = await authenticated_client.get(
            "/api/v1/search/skills",
            params={"skills": "", "min_score": -1}
        )
        assert response.status_code == 422
        
        # Test invalid department
        response = await authenticated_client.get(
            "/api/v1/search/department",
            params={"department": "NonExistentDept"}
        )
        assert response.status_code == 200  # Should return empty results
        assert response.json()["total"] == 0
    
    @pytest.mark.asyncio
    async def test_search_with_claude_api_failure(self, authenticated_client: AsyncClient):
        """Test smart search when Claude API fails"""
        
        with patch('api.services.claude_service.ClaudeService.interpret_search_query') as mock_claude:
            mock_claude.side_effect = Exception("Claude API unavailable")
            
            response = await authenticated_client.post(
                "/api/v1/search/smart",
                json={
                    "query": "Find Python developers",
                    "fallback_to_basic": True
                }
            )
            
            # Should fallback to basic search
            assert response.status_code == 200
            data = response.json()
            
            assert "fallback_used" in data
            assert data["fallback_used"] is True
            assert "results" in data
    
    @pytest.mark.asyncio
    async def test_search_analytics_tracking(self, authenticated_client: AsyncClient, search_test_data):
        """Test that search analytics are tracked"""
        
        response = await authenticated_client.get(
            "/api/v1/search/skills",
            params={"skills": "Python", "track_analytics": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for analytics metadata
        assert "search_id" in data
        assert "timestamp" in data
        assert "performance_metrics" in data
        
        metrics = data["performance_metrics"]
        assert "query_time_ms" in metrics
        assert "results_count" in metrics
        assert "cache_hit" in metrics