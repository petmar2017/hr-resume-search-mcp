#!/usr/bin/env python3
"""
Python MCP Client Example for HR Resume Search

This example demonstrates how to integrate with the HR Resume Search MCP server
using Python for various client applications.

Features:
- Async/sync MCP server communication
- Error handling and retry logic
- Response streaming and caching
- Performance metrics tracking
- Real-world usage examples
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
import uuid

# MCP imports
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import Tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MCPCallResult:
    """Result from MCP tool call"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time: float = 0.0
    tool_name: str = ""
    call_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ClientConfig:
    """MCP client configuration"""
    server_command: str = "python"
    server_args: List[str] = field(default_factory=lambda: ["-m", "mcp_server.server"])
    server_env: Dict[str, str] = field(default_factory=dict)
    connection_timeout: float = 30.0
    call_timeout: float = 60.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes


class HRResumeMCPClient:
    """Professional MCP client for HR Resume Search integration"""
    
    def __init__(self, config: ClientConfig = None):
        self.config = config or ClientConfig()
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self.call_history: List[MCPCallResult] = []
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.is_connected = False
        self._connection_lock = asyncio.Lock()
        
    async def connect(self) -> bool:
        """Connect to MCP server with error handling and retries"""
        async with self._connection_lock:
            if self.is_connected:
                return True
                
            for attempt in range(self.config.retry_attempts):
                try:
                    logger.info(f"Connecting to MCP server (attempt {attempt + 1}/{self.config.retry_attempts})")
                    
                    # Configure server parameters
                    server_params = {
                        "command": self.config.server_command,
                        "args": self.config.server_args,
                        "env": self.config.server_env
                    }
                    
                    # Start server and create session
                    async with stdio_client(server_params) as (read, write):
                        async with ClientSession(read, write) as session:
                            self.session = session
                            
                            # Initialize with timeout
                            await asyncio.wait_for(
                                session.initialize(),
                                timeout=self.config.connection_timeout
                            )
                            
                            # List available tools
                            tools_result = await session.list_tools()
                            self.tools = tools_result.tools
                            
                            self.is_connected = True
                            logger.info(f"✅ Connected! Found {len(self.tools)} tools")
                            
                            # Log available tools
                            for tool in self.tools:
                                logger.debug(f"Available tool: {tool.name} - {tool.description}")
                            
                            return True
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Connection attempt {attempt + 1} timed out")
                except Exception as e:
                    logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
            
            logger.error("Failed to connect to MCP server after all attempts")
            return False
    
    async def disconnect(self):
        """Gracefully disconnect from MCP server"""
        async with self._connection_lock:
            if self.session:
                try:
                    # Session will be closed automatically
                    self.session = None
                    self.is_connected = False
                    logger.info("Disconnected from MCP server")
                except Exception as e:
                    logger.error(f"Error during disconnection: {e}")
    
    def _get_cache_key(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Generate cache key for tool call"""
        cache_data = {"tool": tool_name, "args": arguments}
        return json.dumps(cache_data, sort_keys=True)
    
    def _is_cache_valid(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item is still valid"""
        if not self.config.enable_caching:
            return False
        
        cached_time = datetime.fromisoformat(cached_item["timestamp"])
        expiry_time = cached_time + timedelta(seconds=self.config.cache_ttl)
        return datetime.now() < expiry_time
    
    async def call_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any] = None,
        use_cache: bool = True
    ) -> MCPCallResult:
        """Call MCP tool with comprehensive error handling and caching"""
        
        if not self.is_connected:
            if not await self.connect():
                return MCPCallResult(
                    success=False,
                    error="Failed to connect to MCP server",
                    tool_name=tool_name
                )
        
        arguments = arguments or {}
        start_time = time.time()
        call_id = str(uuid.uuid4())[:8]
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(tool_name, arguments)
            if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):\n                logger.debug(f"[{call_id}] Using cached result for {tool_name}")
                cached_result = self.cache[cache_key]["result"]
                return MCPCallResult(
                    success=True,
                    result=cached_result,
                    response_time=0.001,  # Cache hit
                    tool_name=tool_name,
                    call_id=call_id
                )
        
        # Execute tool call with retries
        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(f"[{call_id}] Calling tool: {tool_name} (attempt {attempt + 1})")
                
                # Call tool with timeout
                result = await asyncio.wait_for(
                    self.session.call_tool(tool_name, arguments),
                    timeout=self.config.call_timeout
                )
                
                response_time = time.time() - start_time
                
                # Create result object
                call_result = MCPCallResult(
                    success=True,
                    result=result.content[0].text if result.content else None,
                    response_time=response_time,
                    tool_name=tool_name,
                    call_id=call_id
                )
                
                # Cache successful result
                if use_cache and self.config.enable_caching:
                    cache_key = self._get_cache_key(tool_name, arguments)
                    self.cache[cache_key] = {
                        "result": call_result.result,
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Track call history
                self.call_history.append(call_result)
                
                logger.info(f"✅ [{call_id}] Tool executed successfully in {response_time:.3f}s")
                return call_result
                
            except asyncio.TimeoutError:
                logger.warning(f"[{call_id}] Tool call timed out (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"[{call_id}] Tool call failed (attempt {attempt + 1}): {e}")
            
            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay)
        
        # All attempts failed
        response_time = time.time() - start_time
        call_result = MCPCallResult(
            success=False,
            error=f"Tool call failed after {self.config.retry_attempts} attempts",
            response_time=response_time,
            tool_name=tool_name,
            call_id=call_id
        )
        
        self.call_history.append(call_result)
        return call_result
    
    async def search_similar_resumes(
        self, 
        candidate_name: Optional[str] = None,
        candidate_id: Optional[str] = None,
        similarity_criteria: Optional[List[str]] = None
    ) -> MCPCallResult:
        """Find resumes similar to a given candidate"""
        arguments = {}
        
        if candidate_name:
            arguments["candidate_name"] = candidate_name
        if candidate_id:
            arguments["candidate_id"] = candidate_id
        if similarity_criteria:
            arguments["similarity_criteria"] = similarity_criteria
        
        return await self.call_tool("search_similar_resumes", arguments)
    
    async def search_by_department(
        self,
        department_name: str,
        company_name: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> MCPCallResult:
        """Find candidates who worked in a specific department"""
        arguments = {"department_name": department_name}
        
        if company_name:
            arguments["company_name"] = company_name
        if date_range:
            arguments["date_range"] = date_range
        
        return await self.call_tool("search_by_department", arguments)
    
    async def find_colleagues(
        self,
        candidate_name: Optional[str] = None,
        candidate_id: Optional[str] = None,
        company_filter: Optional[str] = None
    ) -> MCPCallResult:
        """Find people who worked with a specific candidate"""
        arguments = {}
        
        if candidate_name:
            arguments["candidate_name"] = candidate_name
        if candidate_id:
            arguments["candidate_id"] = candidate_id
        if company_filter:
            arguments["company_filter"] = company_filter
        
        return await self.call_tool("find_colleagues", arguments)
    
    async def smart_query_resumes(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> MCPCallResult:
        """Execute intelligent natural language queries"""
        arguments = {
            "query": query,
            "limit": limit
        }
        
        if filters:
            arguments["filters"] = filters
        
        return await self.call_tool("smart_query_resumes", arguments)
    
    async def analyze_resume_network(
        self,
        candidate_ids: List[str],
        relationship_depth: int = 2
    ) -> MCPCallResult:
        """Analyze professional network relationships"""
        arguments = {
            "candidate_ids": candidate_ids,
            "relationship_depth": relationship_depth
        }
        
        return await self.call_tool("analyze_resume_network", arguments)
    
    async def get_resume_statistics(self) -> MCPCallResult:
        """Get statistics about the resume database"""
        return await self.call_tool("get_resume_statistics")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        if not self.call_history:
            return {"error": "No call history available"}
        
        successful_calls = [call for call in self.call_history if call.success]
        failed_calls = [call for call in self.call_history if not call.success]
        
        response_times = [call.response_time for call in successful_calls]
        
        return {
            "total_calls": len(self.call_history),
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "success_rate": len(successful_calls) / len(self.call_history) * 100,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "cache_hits": len([k for k, v in self.cache.items() if self._is_cache_valid(v)]),
            "tools_used": list(set(call.tool_name for call in self.call_history))
        }
    
    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        logger.info("Response cache cleared")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        return [tool.name for tool in self.tools]


# ==================== Usage Examples ====================

async def example_basic_usage():
    """Basic usage example"""
    print("🔧 Basic MCP Client Usage Example")
    print("==================================\n")
    
    # Create client with custom configuration
    config = ClientConfig(
        server_args=["-m", "mcp_server.server"],
        connection_timeout=30.0,
        enable_caching=True
    )
    
    client = HRResumeMCPClient(config)
    
    try:
        # Connect to server
        if await client.connect():
            print(f"✅ Connected! Available tools: {client.get_available_tools()}")
            
            # Example 1: Search similar resumes
            print("\n🔍 Example 1: Search Similar Resumes")
            result = await client.search_similar_resumes(
                candidate_name="John Doe",
                similarity_criteria=["skills", "department", "company"]
            )
            
            if result.success:
                print(f"✅ Found similar candidates in {result.response_time:.3f}s")
                data = json.loads(result.result) if isinstance(result.result, str) else result.result
                print(f"   Total matches: {data.get('total_matches', 0)}")
            else:
                print(f"❌ Search failed: {result.error}")
            
            # Example 2: Department search
            print("\n🏢 Example 2: Department Search")
            result = await client.search_by_department(
                department_name="Engineering",
                company_name="TechCorp"
            )
            
            if result.success:
                print(f"✅ Department search completed in {result.response_time:.3f}s")
            else:
                print(f"❌ Department search failed: {result.error}")
            
            # Example 3: Smart natural language query
            print("\n🧠 Example 3: Smart Query")
            result = await client.smart_query_resumes(
                query="Find me Python developers with 5+ years experience in fintech",
                limit=5
            )
            
            if result.success:
                print(f"✅ Smart query completed in {result.response_time:.3f}s")
            else:
                print(f"❌ Smart query failed: {result.error}")
            
            # Display performance metrics
            print("\n📊 Performance Metrics:")
            metrics = client.get_performance_metrics()
            for key, value in metrics.items():
                print(f"   {key}: {value}")
        
        else:
            print("❌ Failed to connect to MCP server")
    
    finally:
        await client.disconnect()


async def example_advanced_usage():
    """Advanced usage with error handling and streaming"""
    print("\n🚀 Advanced MCP Client Usage Example")
    print("====================================\n")
    
    client = HRResumeMCPClient()
    
    try:
        # Connect with retry logic
        connected = await client.connect()
        if not connected:
            print("❌ Could not establish connection")
            return
        
        # Example: Network analysis with progress tracking
        print("🕸️ Professional Network Analysis")
        
        candidate_ids = ["candidate_001", "candidate_002", "candidate_003"]
        result = await client.analyze_resume_network(
            candidate_ids=candidate_ids,
            relationship_depth=2
        )
        
        if result.success:
            print(f"✅ Network analysis completed in {result.response_time:.3f}s")
            
            # Parse and display results
            data = json.loads(result.result) if isinstance(result.result, str) else result.result
            if data and data.get('success'):
                stats = data.get('network_stats', {})
                print(f"   Total connections: {stats.get('total_connections', 0)}")
                print(f"   Clusters found: {stats.get('clusters_found', 0)}")
                print(f"   Avg connections per person: {stats.get('average_connections_per_person', 0)}")
        
        # Example: Batch operations with caching
        print("\n📦 Batch Operations with Caching")
        
        departments = ["Engineering", "Product", "Sales", "Marketing"]
        results = []
        
        for dept in departments:
            result = await client.search_by_department(dept)
            results.append((dept, result))
            print(f"   {dept}: {'✅' if result.success else '❌'} ({result.response_time:.3f}s)")
        
        # Example: Performance monitoring
        print("\n📊 Performance Summary:")
        metrics = client.get_performance_metrics()
        print(f"   Success Rate: {metrics['success_rate']:.1f}%")
        print(f"   Average Response Time: {metrics['avg_response_time']:.3f}s")
        print(f"   Cache Hits: {metrics['cache_hits']}")
        print(f"   Tools Used: {', '.join(metrics['tools_used'])}")
    
    finally:
        await client.disconnect()


def sync_wrapper_example():
    """Synchronous wrapper for easier integration"""
    print("\n🔄 Synchronous Wrapper Example")
    print("==============================\n")
    
    class SyncMCPClient:
        """Synchronous wrapper for the async MCP client"""
        
        def __init__(self, config: ClientConfig = None):
            self.async_client = HRResumeMCPClient(config)
            self.loop = None
        
        def _run_async(self, coro):
            """Run async coroutine in sync context"""
            if self.loop is None:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            
            return self.loop.run_until_complete(coro)
        
        def connect(self) -> bool:
            return self._run_async(self.async_client.connect())
        
        def disconnect(self):
            return self._run_async(self.async_client.disconnect())
        
        def search_similar_resumes(self, candidate_name: str, **kwargs) -> MCPCallResult:
            return self._run_async(
                self.async_client.search_similar_resumes(candidate_name, **kwargs)
            )
        
        def smart_query(self, query: str, **kwargs) -> MCPCallResult:
            return self._run_async(
                self.async_client.smart_query_resumes(query, **kwargs)
            )
        
        def get_performance_metrics(self) -> Dict[str, Any]:
            return self.async_client.get_performance_metrics()
    
    # Usage example
    sync_client = SyncMCPClient()
    
    try:
        if sync_client.connect():
            print("✅ Sync client connected")
            
            result = sync_client.smart_query(
                "Find data scientists with machine learning experience"
            )
            
            if result.success:
                print(f"✅ Query successful: {result.response_time:.3f}s")
            else:
                print(f"❌ Query failed: {result.error}")
            
            metrics = sync_client.get_performance_metrics()
            print(f"📊 Metrics: {metrics['success_rate']:.1f}% success rate")
        
        else:
            print("❌ Sync client connection failed")
    
    finally:
        sync_client.disconnect()


# ==================== Main Execution ====================

async def main():
    """Main execution function"""
    print("🎯 HR Resume Search MCP Client Examples")
    print("=======================================\n")
    
    # Run examples
    await example_basic_usage()
    await example_advanced_usage()
    
    # Run sync example
    sync_wrapper_example()
    
    print("\n🎉 All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())