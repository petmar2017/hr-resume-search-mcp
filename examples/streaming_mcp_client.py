#!/usr/bin/env python3
"""
Streaming MCP Client Example for HR Resume Search
Demonstrates real-time streaming responses with AG-UI integration
"""

import asyncio
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
from pathlib import Path
from dataclasses import dataclass
import uuid

# MCP imports
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import Tool, TextContent

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    print("Install rich for better output: pip install rich")
    RICH_AVAILABLE = False

# Configure console
console = Console() if RICH_AVAILABLE else None


@dataclass
class StreamingResult:
    """Container for streaming results"""
    tool_name: str
    chunks: List[str]
    metadata: Dict[str, Any]
    start_time: float
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def chunk_count(self) -> int:
        return len(self.chunks)


class StreamingMCPClient:
    """MCP Client with real-time streaming support for AG-UI"""
    
    def __init__(self, show_progress: bool = True):
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self.is_connected = False
        self.show_progress = show_progress
        self.results_cache: Dict[str, StreamingResult] = {}
        
    async def connect(self) -> bool:
        """Connect to streaming MCP server"""
        try:
            if RICH_AVAILABLE and self.show_progress:
                console.print("[bold cyan]🔄 Connecting to MCP Streaming Server...[/bold cyan]")
            
            server_params = {
                "command": "python",
                "args": ["-m", "mcp_server.ag_ui_server"],
                "env": {
                    "PYTHONPATH": str(Path(__file__).parent.parent),
                    "FASTAPI_BASE_URL": "http://localhost:8000",
                    "MCP_STREAMING_ENABLED": "true",
                    "MCP_CHUNK_DELAY_MS": "50",
                    "MCP_PROGRESS_INDICATORS": "true",
                    "LOG_LEVEL": "INFO"
                }
            }
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    
                    # Initialize session
                    await session.initialize()
                    
                    # List available tools
                    tools_result = await session.list_tools()
                    self.tools = tools_result.tools
                    
                    self.is_connected = True
                    
                    if RICH_AVAILABLE:
                        console.print(f"[bold green]✅ Connected! Found {len(self.tools)} tools[/bold green]")
                        
                        # Display available tools
                        table = Table(title="Available Tools", show_header=True)
                        table.add_column("Tool Name", style="cyan")
                        table.add_column("Description", style="white")
                        
                        for tool in self.tools:
                            table.add_row(tool.name, tool.description[:60] + "...")
                        
                        console.print(table)
                    else:
                        print(f"✅ Connected! Found {len(self.tools)} tools")
                        for tool in self.tools:
                            print(f"  - {tool.name}: {tool.description[:60]}...")
                    
                    return True
                    
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[bold red]❌ Connection failed: {e}[/bold red]")
            else:
                print(f"❌ Connection failed: {e}")
            return False
    
    async def stream_tool_call(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """Call tool and yield streaming chunks"""
        
        if not self.is_connected:
            raise RuntimeError("Not connected to MCP server")
        
        result = StreamingResult(
            tool_name=tool_name,
            chunks=[],
            metadata={"arguments": arguments or {}},
            start_time=time.time()
        )
        
        try:
            # Call the tool
            response = await self.session.call_tool(tool_name, arguments or {})
            
            # Process streaming response
            if response.content:
                for content in response.content:
                    if hasattr(content, 'text'):
                        # Split into lines for streaming effect
                        lines = content.text.split('\n')
                        for line in lines:
                            if line.strip():
                                result.chunks.append(line)
                                yield line
                                
                                # Small delay for streaming effect
                                await asyncio.sleep(0.05)
            
            result.end_time = time.time()
            self.results_cache[f"{tool_name}_{datetime.now().isoformat()}"] = result
            
        except Exception as e:
            yield f"❌ Error calling {tool_name}: {e}"
            result.metadata["error"] = str(e)
            result.end_time = time.time()
    
    async def search_candidates_streaming(
        self,
        query: str,
        skills: List[str] = None,
        min_experience: int = None,
        max_experience: int = None,
        limit: int = 10
    ):
        """Search candidates with real-time streaming results"""
        
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[bold cyan]🔍 Searching: {query}[/bold cyan]",
                title="Streaming Search"
            ))
        else:
            print(f"\n🔍 Searching: {query}")
            print("=" * 60)
        
        arguments = {
            "query": query,
            "search_type": "smart_query",
            "limit": limit
        }
        
        if skills:
            arguments["skills"] = skills
        if min_experience is not None:
            arguments["min_experience_years"] = min_experience
        if max_experience is not None:
            arguments["max_experience_years"] = max_experience
        
        # Track progress
        chunks_received = 0
        candidates_found = []
        
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Processing search...", total=100)
                
                async for chunk in self.stream_tool_call("search_candidates", arguments):
                    chunks_received += 1
                    
                    # Parse chunk for display
                    if "Found" in chunk:
                        progress.update(task, advance=20, description="[green]Analyzing candidates...")
                    elif "Match Score:" in chunk:
                        # Extract candidate info
                        console.print(f"  {chunk}")
                        progress.update(task, advance=10)
                    elif "completed" in chunk.lower():
                        progress.update(task, completed=100, description="[bold green]Search complete!")
                    else:
                        console.print(f"  {chunk}")
                        progress.update(task, advance=5)
        else:
            async for chunk in self.stream_tool_call("search_candidates", arguments):
                print(f"  {chunk}")
                chunks_received += 1
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold green]✅ Received {chunks_received} streaming chunks[/bold green]")
        else:
            print(f"\n✅ Received {chunks_received} streaming chunks")
    
    async def upload_resume_streaming(
        self,
        file_path: str,
        candidate_name: str = None
    ):
        """Upload resume with streaming progress updates"""
        
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[bold cyan]📄 Uploading: {file_path}[/bold cyan]",
                title="Resume Processing"
            ))
        else:
            print(f"\n📄 Uploading: {file_path}")
            print("=" * 60)
        
        # Read file (simulate)
        file_content = f"<simulated file content for {file_path}>"
        
        arguments = {
            "file_name": Path(file_path).name,
            "file_content": file_content,
            "candidate_name": candidate_name or "Unknown"
        }
        
        stages_completed = 0
        
        async for chunk in self.stream_tool_call("upload_resume", arguments):
            stages_completed += 1
            
            if RICH_AVAILABLE:
                # Color code different stages
                if "Upload" in chunk:
                    console.print(f"[blue]📤 {chunk}[/blue]")
                elif "Claude AI" in chunk:
                    console.print(f"[yellow]🤖 {chunk}[/yellow]")
                elif "complete" in chunk.lower():
                    console.print(f"[bold green]✅ {chunk}[/bold green]")
                else:
                    console.print(f"  {chunk}")
            else:
                print(f"  {chunk}")
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold green]✅ Completed {stages_completed} processing stages[/bold green]")
        else:
            print(f"\n✅ Completed {stages_completed} processing stages")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from cached results"""
        if not self.results_cache:
            return {"message": "No operations performed yet"}
        
        total_chunks = sum(r.chunk_count for r in self.results_cache.values())
        total_duration = sum(r.duration for r in self.results_cache.values())
        avg_chunk_rate = total_chunks / total_duration if total_duration > 0 else 0
        
        return {
            "total_operations": len(self.results_cache),
            "total_chunks_received": total_chunks,
            "total_duration_seconds": round(total_duration, 2),
            "avg_chunks_per_second": round(avg_chunk_rate, 2),
            "tools_used": list(set(r.tool_name for r in self.results_cache.values()))
        }


# ==================== Usage Examples ====================

async def example_streaming_search():
    """Example: Streaming candidate search"""
    print("\n" + "="*80)
    print("🚀 STREAMING SEARCH DEMONSTRATION")
    print("="*80)
    
    client = StreamingMCPClient(show_progress=True)
    
    # Connect to server
    if not await client.connect():
        return
    
    # Perform streaming search
    await client.search_candidates_streaming(
        query="Python developer with FastAPI and Docker experience",
        skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        min_experience=3,
        max_experience=8,
        limit=5
    )
    
    # Show performance stats
    stats = client.get_performance_stats()
    
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]📊 Performance Statistics:[/bold cyan]")
        for key, value in stats.items():
            console.print(f"  {key}: [yellow]{value}[/yellow]")
    else:
        print("\n📊 Performance Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


async def example_resume_upload():
    """Example: Streaming resume upload"""
    print("\n" + "="*80)
    print("📄 STREAMING RESUME UPLOAD DEMONSTRATION")
    print("="*80)
    
    client = StreamingMCPClient(show_progress=True)
    
    # Connect to server
    if not await client.connect():
        return
    
    # Upload resume with streaming progress
    await client.upload_resume_streaming(
        file_path="john_doe_resume.pdf",
        candidate_name="John Doe"
    )
    
    # Show performance stats
    stats = client.get_performance_stats()
    
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]📊 Upload Statistics:[/bold cyan]")
        for key, value in stats.items():
            console.print(f"  {key}: [yellow]{value}[/yellow]")
    else:
        print("\n📊 Upload Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


async def example_real_time_monitoring():
    """Example: Real-time system monitoring"""
    print("\n" + "="*80)
    print("📊 REAL-TIME MONITORING DEMONSTRATION")
    print("="*80)
    
    client = StreamingMCPClient(show_progress=True)
    
    # Connect to server
    if not await client.connect():
        return
    
    # Check API status
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]🔥 System Health Check[/bold cyan]")
    else:
        print("\n🔥 System Health Check")
    
    async for chunk in client.stream_tool_call("check_api_status"):
        if RICH_AVAILABLE:
            if "✅" in chunk:
                console.print(f"[green]{chunk}[/green]")
            elif "❌" in chunk:
                console.print(f"[red]{chunk}[/red]")
            else:
                console.print(chunk)
        else:
            print(chunk)
    
    # Get search filters with streaming
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]📋 Available Search Filters[/bold cyan]")
    else:
        print("\n📋 Available Search Filters")
    
    async for chunk in client.stream_tool_call("get_search_filters"):
        if RICH_AVAILABLE:
            console.print(f"  {chunk}")
        else:
            print(f"  {chunk}")


async def main():
    """Main execution function"""
    
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold magenta]🎯 HR Resume Search - Streaming MCP Client Demo[/bold magenta]\n" +
            "[cyan]Real-time streaming with AG-UI integration[/cyan]",
            title="Welcome"
        ))
    else:
        print("\n🎯 HR Resume Search - Streaming MCP Client Demo")
        print("Real-time streaming with AG-UI integration")
        print("="*60)
    
    # Run examples
    try:
        # Example 1: Streaming search
        await example_streaming_search()
        await asyncio.sleep(1)
        
        # Example 2: Resume upload
        await example_resume_upload()
        await asyncio.sleep(1)
        
        # Example 3: System monitoring
        await example_real_time_monitoring()
        
        if RICH_AVAILABLE:
            console.print("\n[bold green]🎉 All demonstrations completed successfully![/bold green]")
        else:
            print("\n🎉 All demonstrations completed successfully!")
        
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[yellow]⚠️ Demonstration interrupted by user[/yellow]")
        else:
            print("\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        else:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("This example requires Python 3.8 or higher")
        sys.exit(1)
    
    # Run the examples
    asyncio.run(main())