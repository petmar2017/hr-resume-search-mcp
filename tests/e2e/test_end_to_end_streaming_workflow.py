#!/usr/bin/env python3
"""
End-to-End Streaming Workflow Test
Tests the complete streaming workflow from file upload to MCP integration
"""
import asyncio
import json
import time
from typing import Dict, Any

class MockClaudeService:
    """Mock ClaudeService for end-to-end testing"""
    
    async def interpret_search_query(self, query: str) -> Dict[str, Any]:
        """Mock search query interpretation"""
        await asyncio.sleep(0.1)  # Simulate AI processing
        
        # Parse common query patterns
        if "python" in query.lower():
            return {
                "skills": ["Python", "FastAPI", "Django"],
                "experience_years": {"min": 3, "max": 7},
                "departments": ["Engineering"],
                "keywords": ["python", "backend", "api"]
            }
        elif "frontend" in query.lower() or "react" in query.lower():
            return {
                "skills": ["JavaScript", "React", "TypeScript"],
                "experience_years": {"min": 2, "max": 5},
                "departments": ["Engineering", "Product"],
                "keywords": ["frontend", "ui", "react"]
            }
        else:
            return {
                "skills": [],
                "experience_years": {"min": None, "max": None},
                "departments": [],
                "keywords": query.split()
            }
    
    async def extract_keywords(self, text: str) -> list:
        """Mock keyword extraction"""
        await asyncio.sleep(0.05)  # Simulate processing
        
        # Simple keyword extraction simulation
        tech_keywords = []
        words = text.lower().split()
        
        tech_terms = [
            "python", "javascript", "react", "vue", "angular", "node.js",
            "django", "fastapi", "flask", "express", "postgresql", "mysql",
            "mongodb", "redis", "docker", "kubernetes", "aws", "azure",
            "microservices", "api", "rest", "graphql", "machine learning",
            "data science", "ai", "tensorflow", "pytorch"
        ]
        
        for word in words:
            if word in tech_terms:
                tech_keywords.append(word.title())
        
        return tech_keywords[:10]  # Limit to 10 keywords
    
    async def parse_resume(self, text: str) -> Dict[str, Any]:
        """Mock resume parsing"""
        await asyncio.sleep(0.2)  # Simulate AI processing
        
        # Extract mock structured data
        return {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "(555) 123-4567",
            "skills": {
                "technical": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "soft": ["Leadership", "Communication", "Problem Solving"]
            },
            "work_experience": [
                {
                    "company": "TechCorp",
                    "position": "Senior Developer",
                    "duration": "2020-2023",
                    "department": "Engineering",
                    "responsibilities": [
                        "Led development of microservices architecture",
                        "Managed team of 5 developers"
                    ]
                }
            ],
            "education": [
                {
                    "institution": "MIT",
                    "degree": "BS Computer Science",
                    "year": "2018"
                }
            ]
        }

class MockFileService:
    """Mock FileService for end-to-end testing"""
    
    async def process_uploaded_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Mock file processing"""
        await asyncio.sleep(0.1)  # Simulate file I/O
        
        if not self.validate_file_type(filename):
            return {
                "success": False,
                "error": "Invalid file type",
                "processing_time": 0.1
            }
        
        # Mock text extraction based on file type
        file_type = self.get_file_type(filename)
        if file_type == "pdf":
            extracted_text = "John Doe - Senior Software Engineer. Python, FastAPI, PostgreSQL. Led microservices development at TechCorp."
        elif file_type in ["docx", "doc"]:
            extracted_text = "John Doe\\nSenior Software Engineer\\nSkills: Python, FastAPI, PostgreSQL\\nExperience: TechCorp - Engineering Department"
        else:
            extracted_text = "Text extraction not supported"
        
        return {
            "success": True,
            "file_path": f"/uploads/{filename}",
            "extracted_text": extracted_text,
            "file_size": len(content),
            "file_type": file_type,
            "processing_time": 0.1
        }
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate file type"""
        return filename.lower().endswith(('.pdf', '.docx', '.doc'))
    
    def get_file_type(self, filename: str) -> str:
        """Get file extension"""
        return filename.lower().split('.')[-1] if '.' in filename else ""

class MockSearchService:
    """Mock SearchService for end-to-end testing"""
    
    def __init__(self):
        # Mock database of candidates
        self.candidates = [
            {
                "id": 1,
                "name": "John Doe",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "department": "Engineering",
                "company": "TechCorp",
                "experience_years": 5
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "skills": ["JavaScript", "React", "Node.js"],
                "department": "Engineering",
                "company": "StartupCo",
                "experience_years": 3
            },
            {
                "id": 3,
                "name": "Bob Johnson",
                "skills": ["Python", "Django", "Machine Learning"],
                "department": "Data Science",
                "company": "DataCorp",
                "experience_years": 7
            }
        ]
    
    async def search_candidates(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Mock candidate search"""
        await asyncio.sleep(0.05)  # Simulate search
        
        matching_candidates = []
        
        for candidate in self.candidates:
            score = 0.0
            match_details = {}
            
            # Check skills match
            if "skills" in criteria and criteria["skills"]:
                skill_matches = set(candidate["skills"]) & set(criteria["skills"])
                if skill_matches:
                    score += 0.5
                    match_details["skills"] = list(skill_matches)
            
            # Check department match
            if "departments" in criteria and criteria["departments"]:
                if candidate["department"] in criteria["departments"]:
                    score += 0.3
                    match_details["department"] = candidate["department"]
            
            # Check experience years
            if "experience_years" in criteria:
                exp_criteria = criteria["experience_years"]
                if exp_criteria.get("min") and candidate["experience_years"] >= exp_criteria["min"]:
                    score += 0.2
                if exp_criteria.get("max") and candidate["experience_years"] <= exp_criteria["max"]:
                    score += 0.1
            
            if score > 0:
                matching_candidates.append({
                    **candidate,
                    "match_score": score,
                    "match_details": match_details
                })
        
        # Sort by match score
        matching_candidates.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "candidates": matching_candidates,
            "total_count": len(matching_candidates),
            "search_time": 0.05
        }

class MockMCPServer:
    """Mock MCP Server for end-to-end testing"""
    
    async def smart_query_resumes(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mock MCP smart query"""
        await asyncio.sleep(0.1)  # Simulate MCP processing
        
        return {
            "success": True,
            "query": query,
            "interpreted_as": {
                "skills": ["Python", "FastAPI"],
                "experience_years": 5,
                "department": "Engineering"
            },
            "results": [
                {
                    "id": "mcp_result_1",
                    "name": "Sarah Chen",
                    "relevance_score": 0.92,
                    "highlights": {
                        "skills": ["Python", "FastAPI", "PostgreSQL"],
                        "experience": "7 years",
                        "department": "Engineering"
                    }
                }
            ],
            "total_results": 1,
            "execution_time_ms": 100
        }
    
    async def search_similar_resumes(self, candidate_id: str, criteria: list = None) -> Dict[str, Any]:
        """Mock similar resume search"""
        await asyncio.sleep(0.08)  # Simulate processing
        
        return {
            "success": True,
            "reference_candidate": candidate_id,
            "similar_candidates": [
                {
                    "id": "similar_1",
                    "name": "Alice Johnson",
                    "match_score": 0.85,
                    "matching_criteria": {
                        "skills": ["Python", "FastAPI"],
                        "department": "Engineering"
                    }
                }
            ],
            "total_matches": 1
        }

class StreamingWorkflowOrchestrator:
    """Orchestrates the complete streaming workflow"""
    
    def __init__(self):
        self.claude_service = MockClaudeService()
        self.file_service = MockFileService()
        self.search_service = MockSearchService()
        self.mcp_server = MockMCPServer()
    
    async def process_resume_upload_and_search(self, filename: str, content: bytes, search_query: str) -> Dict[str, Any]:
        """Complete workflow: upload resume, parse it, and search for similar candidates"""
        workflow_start = time.time()
        results = {}
        
        try:
            # Step 1: Process uploaded file
            print("📄 Step 1: Processing uploaded file...")
            file_result = await self.file_service.process_uploaded_file(filename, content)
            results["file_processing"] = file_result
            
            if not file_result["success"]:
                return {"success": False, "error": "File processing failed", "results": results}
            
            # Step 2: Parse resume with Claude AI
            print("🤖 Step 2: Parsing resume with Claude AI...")
            resume_data = await self.claude_service.parse_resume(file_result["extracted_text"])
            results["resume_parsing"] = resume_data
            
            # Step 3: Extract keywords from resume
            print("🔍 Step 3: Extracting keywords...")
            keywords = await self.claude_service.extract_keywords(file_result["extracted_text"])
            results["keywords"] = keywords
            
            # Step 4: Interpret search query
            print("💭 Step 4: Interpreting search query...")
            search_criteria = await self.claude_service.interpret_search_query(search_query)
            results["search_interpretation"] = search_criteria
            
            # Step 5: Search for candidates using interpreted criteria
            print("🔎 Step 5: Searching candidates...")
            search_results = await self.search_service.search_candidates(search_criteria)
            results["search_results"] = search_results
            
            # Step 6: Use MCP server for advanced queries
            print("🌐 Step 6: MCP server advanced search...")
            mcp_results = await self.mcp_server.smart_query_resumes(search_query, search_criteria)
            results["mcp_results"] = mcp_results
            
            # Step 7: Find similar candidates to uploaded resume
            print("🤝 Step 7: Finding similar candidates...")
            similar_results = await self.mcp_server.search_similar_resumes("uploaded_candidate", ["skills", "department"])
            results["similar_candidates"] = similar_results
            
            workflow_time = time.time() - workflow_start
            
            return {
                "success": True,
                "workflow_time": workflow_time,
                "total_steps": 7,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workflow_time": time.time() - workflow_start,
                "results": results
            }
    
    async def concurrent_processing_test(self, num_files: int = 3) -> Dict[str, Any]:
        """Test concurrent processing of multiple files"""
        print(f"🚀 Testing concurrent processing of {num_files} files...")
        
        # Create mock files
        files = []
        for i in range(num_files):
            files.append({
                "filename": f"resume_{i}.pdf",
                "content": f"Resume content for candidate {i} with Python and FastAPI skills".encode(),
                "query": f"Find Python developers with {3+i} years experience"
            })
        
        # Process all files concurrently
        start_time = time.time()
        tasks = [
            self.process_resume_upload_and_search(f["filename"], f["content"], f["query"])
            for f in files
        ]
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        successful_results = [r for r in results if r["success"]]
        
        return {
            "total_files": num_files,
            "successful_processing": len(successful_results),
            "total_time": total_time,
            "average_time_per_file": total_time / num_files,
            "results": results
        }

async def test_end_to_end_streaming_workflow():
    """Test the complete end-to-end streaming workflow"""
    print("🔄 End-to-End Streaming Workflow Test")
    print("=" * 60)
    
    orchestrator = StreamingWorkflowOrchestrator()
    
    # Test 1: Single file processing workflow
    print("\n1️⃣ Testing Single File Processing Workflow:")
    print("-" * 45)
    
    # Mock uploaded resume file
    resume_content = b"""
    John Doe
    Senior Software Engineer
    john.doe@example.com
    (555) 123-4567
    
    Experience:
    - Senior Developer at TechCorp (2020-2023)
    - Python, FastAPI, PostgreSQL development
    - Led microservices architecture implementation
    - Managed team of 5 developers
    
    Education:
    - BS Computer Science, MIT (2018)
    
    Skills: Python, FastAPI, PostgreSQL, Docker, AWS, React
    """
    
    search_query = "Find senior Python developers with microservices experience"
    
    result = await orchestrator.process_resume_upload_and_search(
        "john_doe_resume.pdf", 
        resume_content, 
        search_query
    )
    
    if result["success"]:
        print(f"✅ Workflow completed successfully in {result['workflow_time']:.2f}s")
        print(f"   📊 Steps completed: {result['total_steps']}")
        
        # Display key results
        file_result = result["results"]["file_processing"]
        print(f"   📄 File processed: {file_result['file_type']} ({file_result['file_size']} bytes)")
        
        keywords = result["results"]["keywords"]
        print(f"   🔍 Keywords extracted: {', '.join(keywords)}")
        
        search_results = result["results"]["search_results"]
        print(f"   🔎 Candidates found: {search_results['total_count']}")
        
        mcp_results = result["results"]["mcp_results"]
        print(f"   🌐 MCP results: {mcp_results['total_results']}")
        
    else:
        print(f"❌ Workflow failed: {result['error']}")
    
    # Test 2: Concurrent processing
    print("\n2️⃣ Testing Concurrent Processing:")
    print("-" * 35)
    
    concurrent_result = await orchestrator.concurrent_processing_test(3)
    
    print(f"   📊 Files processed: {concurrent_result['successful_processing']}/{concurrent_result['total_files']}")
    print(f"   ⏱️  Total time: {concurrent_result['total_time']:.2f}s")
    print(f"   📈 Avg time per file: {concurrent_result['average_time_per_file']:.2f}s")
    
    # Test 3: Error handling
    print("\n3️⃣ Testing Error Handling:")
    print("-" * 28)
    
    # Test invalid file type
    invalid_result = await orchestrator.process_resume_upload_and_search(
        "invalid.txt",
        b"Invalid file content",
        "Find developers"
    )
    
    if not invalid_result["success"]:
        print("   ✅ Invalid file type correctly rejected")
        print(f"      Error: {invalid_result['error']}")
    else:
        print("   ❌ Invalid file type was accepted (unexpected)")
    
    # Test 4: Performance metrics
    print("\n4️⃣ Performance Metrics Summary:")
    print("-" * 32)
    
    if result["success"]:
        workflow_results = result["results"]
        
        print(f"   📄 File processing: {workflow_results['file_processing']['processing_time']:.3f}s")
        print(f"   🔍 Search time: {workflow_results['search_results']['search_time']:.3f}s")
        print(f"   🌐 MCP execution: {workflow_results['mcp_results']['execution_time_ms']}ms")
        print(f"   🔄 Total workflow: {result['workflow_time']:.3f}s")
    
    print("\n🎉 End-to-End Streaming Workflow Testing Complete!")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_end_to_end_streaming_workflow())
        if result:
            print("\n✅ All end-to-end streaming workflow tests passed!")
        else:
            print("\n❌ Some end-to-end tests failed")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()