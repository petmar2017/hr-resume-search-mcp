"""Claude AI service for resume parsing and intelligent processing."""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from ..config import settings

class ClaudeService:
    """Service for interacting with Claude AI for resume parsing."""
    
    def __init__(self):
        """Initialize Claude client."""
        self.api_key = settings.claude_api_key or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("Claude API key not configured. Set CLAUDE_API_KEY in environment.")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-opus-20240229"  # Use latest available model
        
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume text into structured JSON format using Claude.
        
        Args:
            resume_text: Raw text extracted from resume file
            
        Returns:
            Structured resume data as dictionary
        """
        prompt = self._create_parsing_prompt(resume_text)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,  # Low temperature for consistent parsing
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text
            
            # Try to find JSON in the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                parsed_data = json.loads(json_str)
                
                # Validate and clean the parsed data
                return self._validate_and_clean_parsed_data(parsed_data)
            else:
                raise ValueError("No valid JSON found in Claude response")
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from Claude response: {e}")
            # Return basic structure with error
            return {
                "error": "Failed to parse resume",
                "raw_text": resume_text[:500],  # First 500 chars for debugging
                "parsed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            raise
    
    def _create_parsing_prompt(self, resume_text: str) -> str:
        """Create the prompt for Claude to parse the resume."""
        return f"""You are an expert resume parser. Extract structured information from the following resume text and return it as a valid JSON object.

The JSON should have this structure:
{{
    "name": "Full name",
    "email": "Email address",
    "phone": "Phone number",
    "location": "City, State/Country",
    "linkedin_url": "LinkedIn profile URL",
    "github_url": "GitHub profile URL",
    "summary": "Professional summary or objective",
    "current_position": "Current job title",
    "current_company": "Current employer",
    "years_of_experience": "Total years of experience (number)",
    "education": [
        {{
            "degree": "Degree type",
            "field": "Field of study",
            "institution": "School/University name",
            "graduation_date": "YYYY-MM or YYYY",
            "gpa": "GPA if mentioned"
        }}
    ],
    "work_experience": [
        {{
            "company": "Company name",
            "position": "Job title",
            "department": "Department name if mentioned",
            "desk": "Desk/team name if mentioned (e.g., trading desk, specific team)",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM or 'Present'",
            "is_current": true/false,
            "location": "City, State/Country",
            "description": "Job description and responsibilities",
            "achievements": ["List of key achievements"],
            "colleagues": ["Names of mentioned colleagues or team members"]
        }}
    ],
    "skills": {{
        "technical": ["List of technical skills"],
        "languages": ["Programming languages"],
        "tools": ["Software tools and platforms"],
        "soft_skills": ["Soft skills mentioned"],
        "certifications": ["Professional certifications"]
    }},
    "projects": [
        {{
            "name": "Project name",
            "description": "Project description",
            "technologies": ["Technologies used"],
            "link": "Project URL if available"
        }}
    ],
    "languages_spoken": [
        {{
            "language": "Language name",
            "proficiency": "Native/Fluent/Professional/Basic"
        }}
    ],
    "keywords": ["Relevant keywords for search optimization"]
}}

Important extraction rules:
1. Extract all dates in YYYY-MM format when possible
2. For current positions, set end_date to "Present" and is_current to true
3. Extract department and desk information carefully - these are crucial for finding colleagues
4. Look for team names, trading desks, divisions, or any organizational unit mentions
5. Extract any colleague names mentioned in the work experience
6. If information is not found, use null instead of empty strings
7. Ensure all URLs are complete (include https://)
8. Extract as many relevant keywords as possible for search optimization

Resume text to parse:
---
{resume_text}
---

Return ONLY the JSON object, no additional text or explanation."""
    
    def _validate_and_clean_parsed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean the parsed resume data.
        
        Args:
            data: Raw parsed data from Claude
            
        Returns:
            Cleaned and validated data
        """
        # Ensure required fields exist
        required_fields = ["name", "email", "work_experience", "education", "skills"]
        
        for field in required_fields:
            if field not in data:
                data[field] = None if field in ["name", "email"] else []
        
        # Clean email
        if data.get("email"):
            data["email"] = data["email"].lower().strip()
        
        # Ensure work_experience is a list
        if not isinstance(data.get("work_experience"), list):
            data["work_experience"] = []
        
        # Process work experience entries
        for exp in data.get("work_experience", []):
            # Ensure is_current is boolean
            if "is_current" not in exp:
                exp["is_current"] = exp.get("end_date", "").lower() == "present"
            
            # Ensure colleagues is a list
            if "colleagues" not in exp or not isinstance(exp["colleagues"], list):
                exp["colleagues"] = []
            
            # Clean up dates
            if exp.get("end_date", "").lower() in ["present", "current", "now"]:
                exp["end_date"] = "Present"
                exp["is_current"] = True
        
        # Ensure education is a list
        if not isinstance(data.get("education"), list):
            data["education"] = []
        
        # Process skills
        if not isinstance(data.get("skills"), dict):
            data["skills"] = {}
        
        # Ensure all skill categories are lists
        skill_categories = ["technical", "languages", "tools", "soft_skills", "certifications"]
        for category in skill_categories:
            if category not in data["skills"] or not isinstance(data["skills"][category], list):
                data["skills"][category] = []
        
        # Generate keywords if not present
        if "keywords" not in data or not data["keywords"]:
            keywords = set()
            
            # Add skills as keywords
            for category in data.get("skills", {}).values():
                if isinstance(category, list):
                    keywords.update(category)
            
            # Add company names
            for exp in data.get("work_experience", []):
                if exp.get("company"):
                    keywords.add(exp["company"])
                if exp.get("position"):
                    keywords.add(exp["position"])
            
            # Add education institutions
            for edu in data.get("education", []):
                if edu.get("institution"):
                    keywords.add(edu["institution"])
                if edu.get("field"):
                    keywords.add(edu["field"])
            
            data["keywords"] = list(keywords)
        
        # Add metadata
        data["parsed_at"] = datetime.utcnow().isoformat()
        data["parser_version"] = "1.0.0"
        
        return data
    
    async def find_similar_candidates(self, candidate_data: Dict[str, Any], limit: int = 10) -> str:
        """
        Generate search query for finding similar candidates.
        
        Args:
            candidate_data: Parsed candidate data
            limit: Maximum number of results
            
        Returns:
            Search query or criteria for finding similar candidates
        """
        prompt = f"""Based on this candidate profile, generate search criteria for finding similar candidates:

Candidate Profile:
- Current Position: {candidate_data.get('current_position')}
- Current Company: {candidate_data.get('current_company')}
- Years of Experience: {candidate_data.get('years_of_experience')}
- Key Skills: {', '.join(candidate_data.get('skills', {}).get('technical', [])[:5])}
- Education: {candidate_data.get('education', [{}])[0].get('degree', 'N/A')}

Generate a JSON object with search criteria including:
1. Required skills
2. Experience range
3. Similar companies or industries
4. Educational requirements
5. Keywords for search

Return only the JSON object."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error generating similar candidate search: {e}")
            return "{}"
    
    async def extract_colleague_network(self, work_experience: list) -> Dict[str, Any]:
        """
        Extract potential colleague relationships from work experience.
        
        Args:
            work_experience: List of work experience entries
            
        Returns:
            Network of potential colleagues based on overlapping employment
        """
        network = {
            "direct_colleagues": [],  # Explicitly mentioned
            "potential_colleagues": [],  # Same company/department/time
            "departments": set(),
            "companies": set(),
            "time_overlaps": []
        }
        
        for exp in work_experience:
            # Add direct colleagues if mentioned
            if exp.get("colleagues"):
                network["direct_colleagues"].extend(exp["colleagues"])
            
            # Track departments and companies
            if exp.get("department"):
                network["departments"].add(exp["department"])
            if exp.get("company"):
                network["companies"].add(exp["company"])
            
            # Track time periods for overlap analysis
            if exp.get("start_date") and exp.get("end_date"):
                network["time_overlaps"].append({
                    "company": exp.get("company"),
                    "department": exp.get("department"),
                    "desk": exp.get("desk"),
                    "start_date": exp.get("start_date"),
                    "end_date": exp.get("end_date")
                })
        
        # Convert sets to lists for JSON serialization
        network["departments"] = list(network["departments"])
        network["companies"] = list(network["companies"])
        
        return network