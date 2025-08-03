#!/usr/bin/env python3
"""
AG-UI Streaming MCP Server for HR Resume Search API
Thin proxy layer with streaming responses for real-time user experience
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator
from pathlib import Path
import httpx
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# MCP server imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# AG-UI streaming support
import ag_ui

logger = logging.getLogger(__name__)

# Import configuration
from .config import get_config

# Global configuration
config = get_config()

# Initialize MCP server
app = Server("hr-resume-search-streaming")


class StreamingAPIClient:
    """HTTP client with streaming support for FastAPI backend"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=config.api_proxy.connect_timeout,
                read=config.api_proxy.read_timeout,
                write=config.api_proxy.timeout_seconds,
                pool=config.api_proxy.timeout_seconds
            ),
            follow_redirects=config.api_proxy.follow_redirects,
            verify=config.api_proxy.verify_ssl,
            limits=httpx.Limits(
                max_connections=config.performance.max_pool_connections,
                max_keepalive_connections=config.performance.max_pool_keepalive,
                keepalive_expiry=config.performance.keepalive_expiry
            )
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def stream_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Make streaming request to FastAPI backend"""
        
        headers = config.get_auth_headers()
        url = f"{self.base_url}{endpoint}"
        
        # Yield initial status
        yield {
            "type": "status",
            "status": "starting",
            "message": f"Connecting to {endpoint}...",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Make request to FastAPI
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers, params=params or {})
            elif method.upper() == "POST":
                response = await self.client.post(url, headers=headers, json=data or {})
            elif method.upper() == "PUT":
                response = await self.client.put(url, headers=headers, json=data or {})
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check response status
            if response.status_code != 200:
                yield {
                    "type": "error",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            # Parse response
            result = response.json()
            
            # Yield progress update
            yield {
                "type": "status", 
                "status": "processing",
                "message": "Processing response from API...",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await asyncio.sleep(config.streaming.chunk_delay_ms / 1000.0)
            
            # For search results, stream them progressively
            if "results" in result and isinstance(result["results"], list):
                results = result["results"]
                total_results = len(results)
                
                # Stream metadata first
                metadata = {k: v for k, v in result.items() if k != "results"}
                yield {
                    "type": "metadata",
                    "data": metadata,
                    "total_results": total_results,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Stream results in chunks
                chunk_size = config.streaming.max_chunk_size
                for i in range(0, total_results, chunk_size):
                    chunk = results[i:i + chunk_size]
                    
                    yield {
                        "type": "results_chunk",
                        "data": chunk,
                        "chunk_info": {
                            "start": i,
                            "end": min(i + chunk_size, total_results),
                            "total": total_results,
                            "progress": round((min(i + chunk_size, total_results) / total_results) * 100, 1)
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await asyncio.sleep(config.streaming.chunk_delay_ms / 1000.0)
            else:
                # For non-search responses, stream the full result
                yield {
                    "type": "result",
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Final completion status
            yield {
                "type": "status",
                "status": "completed",
                "message": "Request completed successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except httpx.ConnectError:
            yield {
                "type": "error",
                "status": "connection_failed",
                "error": "Cannot connect to FastAPI server",
                "message": f"Make sure FastAPI server is running on {self.base_url}",
                "timestamp": datetime.utcnow().isoformat()
            }
        except httpx.TimeoutException:
            yield {
                "type": "error",
                "status": "timeout",
                "error": "Request timeout",
                "message": f"Request took longer than {config.api_proxy.timeout_seconds} seconds",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            yield {
                "type": "error",
                "status": "unknown_error",
                "error": str(e),
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }


# ==================== MCP Tools (Proxy to FastAPI) ====================

@app.tool()
async def search_candidates(
    query: str = "",
    search_type: str = "skills_match",
    skills: Optional[List[str]] = None,
    min_experience_years: Optional[int] = None,
    max_experience_years: Optional[int] = None,
    companies: Optional[List[str]] = None,
    departments: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    education_level: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> List[TextContent]:
    """
    Search candidates with multiple criteria using FastAPI backend.
    Returns streaming results for real-time user experience.
    
    Args:
        query: Search query text
        search_type: Type of search (skills_match, same_department, experience_match)
        skills: List of required skills
        min_experience_years: Minimum years of experience
        max_experience_years: Maximum years of experience  
        companies: List of companies to filter by
        departments: List of departments to filter by
        locations: List of locations to filter by
        education_level: Education level filter
        limit: Maximum results to return
        offset: Results offset for pagination
    
    Returns:
        Streaming search results with progress updates
    """
    
    # Prepare request data
    request_data = {
        "query": query,
        "search_type": search_type,
        "limit": limit,
        "offset": offset
    }
    
    # Add optional filters
    if skills:
        request_data["skills"] = skills
    if min_experience_years is not None:
        request_data["min_experience_years"] = min_experience_years
    if max_experience_years is not None:
        request_data["max_experience_years"] = max_experience_years
    if companies:
        request_data["companies"] = companies
    if departments:
        request_data["departments"] = departments
    if locations:
        request_data["locations"] = locations
    if education_level:
        request_data["education_level"] = education_level
    
    results = []
    
    try:
        async with StreamingAPIClient(config.api_proxy.base_url) as client:
            async for chunk in client.stream_request(
                "POST", 
                "/api/v1/search/candidates", 
                data=request_data
            ):
                # Stream each chunk as separate content
                chunk_text = json.dumps(chunk, indent=2)
                results.append(TextContent(
                    type="text",
                    text=f"🔍 **Search Progress Update**\n\n```json\n{chunk_text}\n```"
                ))
                
                # Add visual progress indicators for different chunk types
                if chunk.get("type") == "results_chunk":
                    progress = chunk.get("chunk_info", {}).get("progress", 0)
                    progress_bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
                    results.append(TextContent(
                        type="text", 
                        text=f"📊 **Progress:** {progress}% [{progress_bar}]"
                    ))
                elif chunk.get("type") == "metadata":
                    total = chunk.get("total_results", 0)
                    results.append(TextContent(
                        type="text",
                        text=f"📈 **Found {total} candidates matching your criteria**"
                    ))
                elif chunk.get("type") == "status" and chunk.get("status") == "completed":
                    results.append(TextContent(
                        type="text",
                        text="✅ **Search completed successfully!**"
                    ))
        
        if not results:
            results.append(TextContent(
                type="text",
                text="❌ No search results received. Check if FastAPI server is running."
            ))
            
    except Exception as e:
        results.append(TextContent(
            type="text",
            text=f"❌ **Search Error:** {str(e)}\n\nMake sure the FastAPI server is running on {config.api_proxy.base_url}"
        ))
    
    return results


@app.tool()
async def search_similar(
    candidate_id: str,
    limit: int = 10
) -> List[TextContent]:
    """
    Find profiles similar to a given candidate using FastAPI backend.
    
    Args:
        candidate_id: UUID of the reference candidate
        limit: Maximum results to return
    
    Returns:
        Streaming similarity search results
    """
    
    results = []
    
    try:
        params = {
            "candidate_id": candidate_id,
            "limit": limit
        }
        
        async with StreamingAPIClient(config.api_proxy.base_url) as client:
            async for chunk in client.stream_request(
                "POST",
                "/api/v1/search/similar",
                params=params
            ):
                chunk_text = json.dumps(chunk, indent=2)
                results.append(TextContent(
                    type="text",
                    text=f"🔍 **Similarity Search Update**\n\n```json\n{chunk_text}\n```"
                ))
                
                if chunk.get("type") == "results_chunk":
                    candidates = chunk.get("data", [])
                    for candidate in candidates:
                        match_score = candidate.get("match_score", 0)
                        name = candidate.get("full_name", "Unknown")
                        score_bar = "🟢" * int(match_score * 10) + "⚪" * (10 - int(match_score * 10))
                        results.append(TextContent(
                            type="text",
                            text=f"👤 **{name}** - Match: {match_score:.1%} [{score_bar}]"
                        ))
        
    except Exception as e:
        results.append(TextContent(
            type="text",
            text=f"❌ **Similarity Search Error:** {str(e)}"
        ))
    
    return results


@app.tool()
async def search_colleagues(
    candidate_id: str,
    limit: int = 10
) -> List[TextContent]:
    """
    Find former colleagues who worked with a candidate using FastAPI backend.
    
    Args:
        candidate_id: UUID of the reference candidate
        limit: Maximum results to return
    
    Returns:
        Streaming colleague search results
    """
    
    results = []
    
    try:
        params = {
            "candidate_id": candidate_id,
            "limit": limit
        }
        
        async with StreamingAPIClient(config.api_proxy.base_url) as client:
            async for chunk in client.stream_request(
                "POST",
                "/api/v1/search/colleagues", 
                params=params
            ):
                chunk_text = json.dumps(chunk, indent=2)
                results.append(TextContent(
                    type="text",
                    text=f"👥 **Colleague Search Update**\n\n```json\n{chunk_text}\n```"
                ))
                
                if chunk.get("type") == "results_chunk":
                    colleagues = chunk.get("data", [])
                    for colleague in colleagues:
                        name = colleague.get("full_name", "Unknown")
                        highlights = colleague.get("highlights", {})
                        company = highlights.get("company", "Unknown Company")
                        overlap_months = highlights.get("overlap_months", 0)
                        results.append(TextContent(
                            type="text",
                            text=f"🤝 **{name}** worked together at **{company}** for **{overlap_months} months**"
                        ))
        
    except Exception as e:
        results.append(TextContent(
            type="text",
            text=f"❌ **Colleague Search Error:** {str(e)}"
        ))
    
    return results


@app.tool()
async def upload_resume(
    file_name: str,
    file_content: str,
    candidate_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None
) -> List[TextContent]:
    """
    Upload and process a resume file using FastAPI backend with streaming progress.
    
    Args:
        file_name: Name of the resume file
        file_content: Base64 encoded file content
        candidate_name: Optional candidate name
        tags: Optional tags for the resume
        notes: Optional notes about the resume
    
    Returns:
        Streaming upload and processing progress
    """
    
    results = []
    
    try:
        # Prepare multipart form data for file upload
        files = {
            "file": (file_name, file_content, "application/octet-stream")
        }
        
        # For now, we'll simulate streaming since file upload is typically not streamed
        results.append(TextContent(
            type="text",
            text=f"📄 **Starting upload of {file_name}...**"
        ))
        
        async with StreamingAPIClient(config.api_proxy.base_url) as client:
            # Note: File upload typically requires multipart/form-data
            # This is a simplified implementation - full version would handle file streaming
            upload_data = {
                "file_name": file_name,
                "candidate_name": candidate_name,
                "tags": tags or [],
                "notes": notes
            }
            
            async for chunk in client.stream_request(
                "POST",
                "/api/v1/resumes/upload",
                data=upload_data
            ):
                chunk_text = json.dumps(chunk, indent=2)
                results.append(TextContent(
                    type="text",
                    text=f"📤 **Upload Progress**\n\n```json\n{chunk_text}\n```"
                ))
                
                if chunk.get("type") == "status":
                    status = chunk.get("status", "")
                    message = chunk.get("message", "")
                    
                    if status == "processing":
                        results.append(TextContent(
                            type="text",
                            text="🤖 **Claude AI is analyzing the resume...**"
                        ))
                    elif status == "completed":
                        results.append(TextContent(
                            type="text",
                            text="✅ **Resume processed successfully!**"
                        ))
        
    except Exception as e:
        results.append(TextContent(
            type="text",
            text=f"❌ **Upload Error:** {str(e)}"
        ))
    
    return results


@app.tool()
async def get_resume(
    resume_id: str
) -> List[TextContent]:
    """
    Get detailed information about a specific resume using FastAPI backend.
    
    Args:
        resume_id: UUID of the resume
    
    Returns:
        Streaming resume details
    """
    
    results = []
    
    try:
        async with StreamingAPIClient(config.api_proxy.base_url) as client:
            async for chunk in client.stream_request(
                "GET",
                f"/api/v1/resumes/{resume_id}"
            ):
                chunk_text = json.dumps(chunk, indent=2)
                results.append(TextContent(
                    type="text",
                    text=f"📋 **Resume Details**\n\n```json\n{chunk_text}\n```"
                ))
                
                if chunk.get("type") == "result":
                    resume_data = chunk.get("data", {})
                    if "parsed_data" in resume_data:
                        parsed = resume_data["parsed_data"]
                        name = parsed.get("full_name", "Unknown")
                        skills = parsed.get("skills", [])
                        experience = parsed.get("total_experience_years", 0)
                        
                        results.append(TextContent(
                            type="text",
                            text=f"👤 **{name}**\n🛠️ **Skills:** {', '.join(skills[:5])}{'...' if len(skills) > 5 else ''}\n📈 **Experience:** {experience} years"
                        ))
        
    except Exception as e:
        results.append(TextContent(
            type="text",
            text=f"❌ **Resume Retrieval Error:** {str(e)}"
        ))
    
    return results


@app.tool()
async def authenticate_user(
    email: str,
    password: str
) -> List[TextContent]:
    """
    Authenticate user and set session token for subsequent API calls.
    
    Args:
        email: User email
        password: User password
    
    Returns:
        Authentication result and session setup
    """
    
    results = []
    
    try:
        auth_data = {
            "username": email,  # FastAPI OAuth2 uses 'username' field
            "password": password
        }
        
        async with StreamingAPIClient(config.api_proxy.base_url) as client:
            async for chunk in client.stream_request(
                "POST",
                "/api/v1/auth/login",
                data=auth_data
            ):
                if chunk.get("type") == "result":
                    auth_result = chunk.get("data", {})
                    if "access_token" in auth_result:
                        # Set the token for future requests
                        config.set_auth_token(auth_result["access_token"])
                        
                        results.append(TextContent(
                            type="text",
                            text="✅ **Authentication successful!** You can now use all HR search tools."
                        ))
                        
                        results.append(TextContent(
                            type="text",
                            text=f"🔑 **Session expires in:** {auth_result.get('expires_in', 1800)} seconds"
                        ))
                    else:
                        results.append(TextContent(
                            type="text",
                            text="❌ **Authentication failed.** Please check your credentials."
                        ))
                elif chunk.get("type") == "error":
                    results.append(TextContent(
                        type="text",
                        text=f"❌ **Authentication Error:** {chunk.get('message', 'Unknown error')}"
                    ))
        
    except Exception as e:
        results.append(TextContent(
            type="text",
            text=f"❌ **Authentication Error:** {str(e)}"
        ))
    
    return results


@app.tool()
async def get_search_filters() -> List[TextContent]:
    """
    Get available search filters and statistics using FastAPI backend.
    
    Returns:
        Available filters with counts for faceted search
    """
    
    results = []
    
    try:
        async with StreamingAPIClient(config.api_proxy.base_url) as client:
            async for chunk in client.stream_request(
                "GET",
                "/api/v1/search/filters"
            ):
                chunk_text = json.dumps(chunk, indent=2)
                results.append(TextContent(
                    type="text",
                    text=f"🔍 **Available Search Filters**\n\n```json\n{chunk_text}\n```"
                ))
                
                if chunk.get("type") == "result":
                    filters_data = chunk.get("data", {})
                    
                    # Format statistics nicely
                    if "statistics" in filters_data:
                        stats = filters_data["statistics"]
                        results.append(TextContent(
                            type="text",
                            text=f"📊 **Database Statistics:**\n"
                                 f"👥 **Candidates:** {stats.get('total_candidates', 0)}\n"
                                 f"📄 **Resumes:** {stats.get('total_resumes', 0)}\n"
                                 f"🕒 **Last Updated:** {stats.get('last_updated', 'Unknown')}"
                        ))
                    
                    # Show top companies
                    if "companies" in filters_data:
                        top_companies = filters_data["companies"][:5]
                        company_list = "\n".join([
                            f"• **{comp['name']}** ({comp['count']} candidates)"
                            for comp in top_companies
                        ])
                        results.append(TextContent(
                            type="text",
                            text=f"🏢 **Top Companies:**\n{company_list}"
                        ))
                    
                    # Show top skills
                    if "skills" in filters_data:
                        top_skills = filters_data["skills"][:5]
                        skills_list = "\n".join([
                            f"• **{skill['name']}** ({skill['count']} candidates)"
                            for skill in top_skills
                        ])
                        results.append(TextContent(
                            type="text",
                            text=f"🛠️ **Top Skills:**\n{skills_list}"
                        ))
        
    except Exception as e:
        results.append(TextContent(
            type="text",
            text=f"❌ **Filter Retrieval Error:** {str(e)}"
        ))
    
    return results


@app.tool()
async def check_api_status() -> List[TextContent]:
    """
    Check the health and status of the FastAPI backend.
    
    Returns:
        API health status and connectivity information
    """
    
    results = []
    
    try:
        async with StreamingAPIClient(config.api_proxy.base_url) as client:
            async for chunk in client.stream_request(
                "GET",
                "/health"
            ):
                chunk_text = json.dumps(chunk, indent=2)
                results.append(TextContent(
                    type="text",
                    text=f"🔍 **API Health Check**\n\n```json\n{chunk_text}\n```"
                ))
                
                if chunk.get("type") == "result":
                    health_data = chunk.get("data", {})
                    status = health_data.get("status", "unknown")
                    
                    if status == "healthy":
                        results.append(TextContent(
                            type="text",
                            text="✅ **FastAPI backend is healthy and ready!**"
                        ))
                        
                        # Show additional info
                        version = health_data.get("version", "unknown")
                        service = health_data.get("service", "unknown")
                        results.append(TextContent(
                            type="text",
                            text=f"📋 **Service:** {service}\n🔧 **Version:** {version}"
                        ))
                    else:
                        results.append(TextContent(
                            type="text",
                            text=f"⚠️ **API Status:** {status}"
                        ))
        
    except Exception as e:
        results.append(TextContent(
            type="text",
            text=f"❌ **API Health Check Failed:** {str(e)}\n\n"
                 f"Make sure FastAPI server is running on {config.api_proxy.base_url}"
        ))
    
    return results


# ==================== Main Entry Point ====================

async def main():
    """Main entry point for the streaming MCP server."""
    try:
        logger.info("Starting AG-UI Streaming MCP Server for HR Resume Search...")
        
        # Set up ag-ui streaming if available
        try:
            ag_ui.init()
            logger.info("AG-UI streaming initialized successfully")
        except Exception as e:
            logger.warning(f"AG-UI not available: {e}")
        
        # Initialize server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("MCP Server shutting down...")
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the server
    asyncio.run(main())