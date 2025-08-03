#!/usr/bin/env python3
"""
MCP Server for API Builder
Provides tools for API development, testing, and documentation
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import HR tools
from .hr_tools import register_hr_tools

# Initialize MCP server
app = Server("hr-resume-search-mcp")

# Configuration
API_BASE_PATH = Path(__file__).parent.parent / "api"
TEMPLATES_PATH = Path(__file__).parent / "templates"
DOCS_PATH = Path(__file__).parent.parent / "docs"

# Ensure directories exist
API_BASE_PATH.mkdir(parents=True, exist_ok=True)
TEMPLATES_PATH.mkdir(parents=True, exist_ok=True)
DOCS_PATH.mkdir(parents=True, exist_ok=True)


# ==================== API Tools ====================

@app.tool()
async def get_api_status() -> Dict[str, Any]:
    """
    Check API health status and configuration.
    Returns current API status, active endpoints, and system health.
    """
    try:
        # Check if FastAPI server is running
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000/health")
                api_status = "running" if response.status_code == 200 else "error"
            except:
                api_status = "offline"
        
        # Count existing endpoints
        endpoint_files = list((API_BASE_PATH / "routers").glob("*.py")) if (API_BASE_PATH / "routers").exists() else []
        
        return {
            "status": api_status,
            "timestamp": datetime.now().isoformat(),
            "endpoints_count": len(endpoint_files),
            "api_path": str(API_BASE_PATH),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.tool()
async def create_endpoint(
    path: str,
    method: str = "GET",
    description: str = "",
    request_body: Optional[str] = None,
    response_model: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a new FastAPI endpoint with boilerplate code.
    
    Args:
        path: API endpoint path (e.g., "/users/{user_id}")
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        description: Endpoint description for documentation
        request_body: Optional request body model name
        response_model: Optional response model name
        tags: Optional list of tags for API grouping
    
    Returns:
        Generated endpoint code and file location
    """
    try:
        # Validate method
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        method = method.upper()
        if method not in valid_methods:
            return {"error": f"Invalid method. Must be one of {valid_methods}"}
        
        # Generate endpoint code
        imports = ["from fastapi import APIRouter, HTTPException, Depends, status\n"]
        if request_body:
            imports.append(f"from ..models import {request_body}\n")
        if response_model:
            imports.append(f"from ..models import {response_model}\n")
        imports.append("from typing import List, Optional\n")
        imports.append("from datetime import datetime\n\n")
        
        # Generate router name from path
        router_name = path.strip("/").split("/")[0].replace("-", "_")
        
        code = "".join(imports)
        code += f"router = APIRouter()\n\n"
        
        # Generate function name
        func_name = f"{method.lower()}_{router_name}"
        if "{" in path:
            # Handle path parameters
            func_name += "_by_id"
        
        # Generate function signature
        code += f'@router.{method.lower()}("{path}"'
        if tags:
            code += f', tags={tags}'
        if description:
            code += f', description="{description}"'
        if response_model:
            code += f', response_model={response_model}'
        code += ")\n"
        
        # Generate function
        code += f"async def {func_name}("
        
        # Add path parameters
        if "{" in path:
            import re
            params = re.findall(r'\{(\w+)\}', path)
            for param in params:
                code += f"{param}: str, "
        
        # Add request body
        if request_body and method in ["POST", "PUT", "PATCH"]:
            code += f"body: {request_body}, "
        
        # Remove trailing comma and space
        if code.endswith(", "):
            code = code[:-2]
        
        code += "):\n"
        code += f'    """\n'
        code += f'    {description or "Endpoint for " + path}\n'
        code += f'    """\n'
        
        # Add basic implementation
        if method == "GET":
            code += "    # TODO: Implement data retrieval logic\n"
            code += "    return {'message': 'GET endpoint not yet implemented'}\n"
        elif method == "POST":
            code += "    # TODO: Implement creation logic\n"
            code += "    return {'message': 'POST endpoint not yet implemented', 'status': 'created'}\n"
        elif method == "PUT":
            code += "    # TODO: Implement update logic\n"
            code += "    return {'message': 'PUT endpoint not yet implemented', 'status': 'updated'}\n"
        elif method == "DELETE":
            code += "    # TODO: Implement deletion logic\n"
            code += "    return {'message': 'DELETE endpoint not yet implemented', 'status': 'deleted'}\n"
        elif method == "PATCH":
            code += "    # TODO: Implement partial update logic\n"
            code += "    return {'message': 'PATCH endpoint not yet implemented', 'status': 'patched'}\n"
        
        # Save to file
        routers_path = API_BASE_PATH / "routers"
        routers_path.mkdir(exist_ok=True)
        
        file_path = routers_path / f"{router_name}.py"
        
        # If file exists, append to it
        if file_path.exists():
            with open(file_path, 'a') as f:
                f.write("\n\n" + code)
        else:
            with open(file_path, 'w') as f:
                f.write(code)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "endpoint": f"{method} {path}",
            "function_name": func_name,
            "code": code
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.tool()
async def create_model(
    name: str,
    fields: Dict[str, str],
    base_model: str = "BaseModel",
    description: str = ""
) -> Dict[str, Any]:
    """
    Generate a Pydantic model for API requests/responses.
    
    Args:
        name: Model class name
        fields: Dictionary of field names and types (e.g., {"name": "str", "age": "int"})
        base_model: Base class to inherit from (default: BaseModel)
        description: Model description for documentation
    
    Returns:
        Generated model code and file location
    """
    try:
        # Generate model code
        code = "from pydantic import BaseModel, Field, validator\n"
        code += "from typing import Optional, List, Dict, Any\n"
        code += "from datetime import datetime\n"
        code += "from enum import Enum\n\n"
        
        if description:
            code += f'"""{description}"""\n\n'
        
        code += f"class {name}({base_model}):\n"
        if description:
            code += f'    """{description}"""\n'
        
        # Add fields
        for field_name, field_type in fields.items():
            # Handle optional fields
            if field_type.startswith("Optional["):
                code += f"    {field_name}: {field_type} = None\n"
            else:
                code += f"    {field_name}: {field_type}\n"
        
        # Add model config
        code += "\n    class Config:\n"
        code += "        json_schema_extra = {\n"
        code += f'            "example": {{\n'
        
        # Generate example values
        for field_name, field_type in fields.items():
            example_value = {
                "str": '"example"',
                "int": "123",
                "float": "123.45",
                "bool": "True",
                "datetime": '"2024-01-01T00:00:00"',
                "List[str]": '["item1", "item2"]',
                "Dict[str, Any]": '{"key": "value"}'
            }.get(field_type.replace("Optional[", "").replace("]", ""), '"example"')
            
            code += f'                "{field_name}": {example_value},\n'
        
        code += "            }\n"
        code += "        }\n"
        
        # Save to file
        models_path = API_BASE_PATH / "models"
        models_path.mkdir(exist_ok=True)
        
        file_path = models_path / f"{name.lower()}.py"
        
        with open(file_path, 'w') as f:
            f.write(code)
        
        # Update __init__.py
        init_path = models_path / "__init__.py"
        if init_path.exists():
            with open(init_path, 'a') as f:
                f.write(f"from .{name.lower()} import {name}\n")
        else:
            with open(init_path, 'w') as f:
                f.write(f"from .{name.lower()} import {name}\n")
        
        return {
            "success": True,
            "file_path": str(file_path),
            "model_name": name,
            "fields": fields,
            "code": code
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== Testing Tools ====================

@app.tool()
async def generate_test(
    endpoint_path: str,
    test_type: str = "unit",
    test_cases: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate test cases for API endpoints.
    
    Args:
        endpoint_path: API endpoint to test (e.g., "/users/{user_id}")
        test_type: Type of test (unit, integration, e2e)
        test_cases: Optional list of specific test cases to generate
    
    Returns:
        Generated test code and file location
    """
    try:
        # Generate test code
        code = "import pytest\n"
        code += "from fastapi.testclient import TestClient\n"
        code += "from httpx import AsyncClient\n"
        code += "import asyncio\n"
        code += "from unittest.mock import patch, MagicMock\n\n"
        
        # Generate test class name
        test_class = endpoint_path.strip("/").replace("/", "_").replace("{", "").replace("}", "").replace("-", "_")
        
        code += f"class Test{test_class.title()}:\n"
        code += f'    """Tests for {endpoint_path} endpoint"""\n\n'
        
        # Generate setup method
        code += "    @pytest.fixture\n"
        code += "    def client(self):\n"
        code += "        from main import app\n"
        code += "        return TestClient(app)\n\n"
        
        # Generate test methods
        if test_cases:
            for i, test_case in enumerate(test_cases):
                method = test_case.get("method", "GET")
                expected_status = test_case.get("expected_status", 200)
                description = test_case.get("description", f"Test {method} {endpoint_path}")
                
                code += f"    def test_{method.lower()}_{test_class}_{i}(self, client):\n"
                code += f'        """Test: {description}"""\n'
                code += f'        response = client.{method.lower()}("{endpoint_path}"'
                
                if test_case.get("body"):
                    code += f', json={test_case["body"]}'
                if test_case.get("params"):
                    code += f', params={test_case["params"]}'
                
                code += ")\n"
                code += f"        assert response.status_code == {expected_status}\n"
                
                if test_case.get("expected_response"):
                    code += f"        assert response.json() == {test_case['expected_response']}\n"
                
                code += "\n"
        else:
            # Generate default test cases
            code += f"    def test_get_{test_class}_success(self, client):\n"
            code += f'        """Test successful GET request to {endpoint_path}"""\n'
            code += f'        response = client.get("{endpoint_path}")\n'
            code += "        assert response.status_code == 200\n\n"
            
            code += f"    def test_get_{test_class}_not_found(self, client):\n"
            code += f'        """Test 404 response for {endpoint_path}"""\n'
            code += f'        response = client.get("{endpoint_path}/nonexistent")\n'
            code += "        assert response.status_code == 404\n\n"
        
        # Save to file
        tests_path = API_BASE_PATH / "tests"
        tests_path.mkdir(exist_ok=True)
        
        file_path = tests_path / f"test_{test_class}.py"
        
        with open(file_path, 'w') as f:
            f.write(code)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "test_type": test_type,
            "endpoint": endpoint_path,
            "test_count": len(test_cases) if test_cases else 2,
            "code": code
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== Documentation Tools ====================

@app.tool()
async def generate_api_docs(
    format: str = "markdown",
    include_examples: bool = True
) -> Dict[str, Any]:
    """
    Generate API documentation from existing endpoints.
    
    Args:
        format: Documentation format (markdown, openapi, postman)
        include_examples: Whether to include example requests/responses
    
    Returns:
        Generated documentation content and file location
    """
    try:
        # Scan for existing endpoints
        routers_path = API_BASE_PATH / "routers"
        endpoints = []
        
        if routers_path.exists():
            for file in routers_path.glob("*.py"):
                with open(file, 'r') as f:
                    content = f.read()
                    # Parse endpoints from file (simplified)
                    import re
                    pattern = r'@router\.(\w+)\("([^"]+)"'
                    matches = re.findall(pattern, content)
                    for method, path in matches:
                        endpoints.append({
                            "method": method.upper(),
                            "path": path,
                            "file": file.name
                        })
        
        if format == "markdown":
            doc = "# API Documentation\n\n"
            doc += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            doc += "## Endpoints\n\n"
            
            for endpoint in endpoints:
                doc += f"### {endpoint['method']} {endpoint['path']}\n\n"
                doc += f"**File**: `{endpoint['file']}`\n\n"
                
                if include_examples:
                    doc += "#### Example Request\n\n"
                    doc += "```bash\n"
                    doc += f"curl -X {endpoint['method']} http://localhost:8000{endpoint['path']}\n"
                    doc += "```\n\n"
                    doc += "#### Example Response\n\n"
                    doc += "```json\n"
                    doc += "{\n"
                    doc += '  "status": "success",\n'
                    doc += '  "data": {}\n'
                    doc += "}\n"
                    doc += "```\n\n"
            
            # Save documentation
            doc_path = DOCS_PATH / "api_documentation.md"
            with open(doc_path, 'w') as f:
                f.write(doc)
            
            return {
                "success": True,
                "file_path": str(doc_path),
                "format": format,
                "endpoints_documented": len(endpoints),
                "content": doc[:500] + "..." if len(doc) > 500 else doc
            }
            
        elif format == "openapi":
            # Generate OpenAPI JSON
            openapi = {
                "openapi": "3.0.0",
                "info": {
                    "title": "API Builder Generated API",
                    "version": "1.0.0",
                    "description": "Auto-generated API documentation"
                },
                "paths": {}
            }
            
            for endpoint in endpoints:
                if endpoint['path'] not in openapi['paths']:
                    openapi['paths'][endpoint['path']] = {}
                
                openapi['paths'][endpoint['path']][endpoint['method'].lower()] = {
                    "summary": f"{endpoint['method']} {endpoint['path']}",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    }
                }
            
            # Save OpenAPI spec
            doc_path = DOCS_PATH / "openapi.json"
            with open(doc_path, 'w') as f:
                json.dump(openapi, f, indent=2)
            
            return {
                "success": True,
                "file_path": str(doc_path),
                "format": format,
                "endpoints_documented": len(endpoints),
                "spec": openapi
            }
        
        else:
            return {
                "success": False,
                "error": f"Unsupported format: {format}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== Database Tools ====================

@app.tool()
async def create_migration(
    name: str,
    operations: List[str]
) -> Dict[str, Any]:
    """
    Generate database migration files.
    
    Args:
        name: Migration name/description
        operations: List of migration operations (e.g., ["create_table users", "add_column email"])
    
    Returns:
        Generated migration file and instructions
    """
    try:
        from datetime import datetime
        
        # Generate migration filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name.lower().replace(' ', '_')}.py"
        
        # Generate migration code
        code = '"""' + f'\n{name}\n' + '"""\n\n'
        code += "from alembic import op\n"
        code += "import sqlalchemy as sa\n\n"
        
        code += "def upgrade():\n"
        code += '    """Apply migration"""\n'
        
        for operation in operations:
            if operation.startswith("create_table"):
                table_name = operation.split()[1] if len(operation.split()) > 1 else "table"
                code += f"    op.create_table(\n"
                code += f"        '{table_name}',\n"
                code += f"        sa.Column('id', sa.Integer(), primary_key=True),\n"
                code += f"        sa.Column('created_at', sa.DateTime(), nullable=False),\n"
                code += f"        sa.Column('updated_at', sa.DateTime(), nullable=False)\n"
                code += f"    )\n"
            elif operation.startswith("add_column"):
                parts = operation.split()
                column_name = parts[1] if len(parts) > 1 else "column"
                table_name = parts[2] if len(parts) > 2 else "table"
                code += f"    op.add_column('{table_name}', sa.Column('{column_name}', sa.String(), nullable=True))\n"
            elif operation.startswith("drop_table"):
                table_name = operation.split()[1] if len(operation.split()) > 1 else "table"
                code += f"    op.drop_table('{table_name}')\n"
            else:
                code += f"    # TODO: Implement {operation}\n"
        
        code += "\n"
        code += "def downgrade():\n"
        code += '    """Revert migration"""\n'
        
        # Generate reverse operations
        for operation in reversed(operations):
            if operation.startswith("create_table"):
                table_name = operation.split()[1] if len(operation.split()) > 1 else "table"
                code += f"    op.drop_table('{table_name}')\n"
            elif operation.startswith("add_column"):
                parts = operation.split()
                column_name = parts[1] if len(parts) > 1 else "column"
                table_name = parts[2] if len(parts) > 2 else "table"
                code += f"    op.drop_column('{table_name}', '{column_name}')\n"
            elif operation.startswith("drop_table"):
                table_name = operation.split()[1] if len(operation.split()) > 1 else "table"
                code += f"    # TODO: Recreate table '{table_name}'\n"
            else:
                code += f"    # TODO: Revert {operation}\n"
        
        # Save migration file
        migrations_path = API_BASE_PATH / "migrations"
        migrations_path.mkdir(exist_ok=True)
        
        file_path = migrations_path / filename
        with open(file_path, 'w') as f:
            f.write(code)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "migration_name": name,
            "operations": operations,
            "code": code
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== Utility Tools ====================

@app.tool()
async def validate_api_structure() -> Dict[str, Any]:
    """
    Validate the API project structure and identify missing components.
    
    Returns:
        Validation results and recommendations
    """
    try:
        issues = []
        recommendations = []
        
        # Check required directories
        required_dirs = ["routers", "models", "tests", "migrations"]
        for dir_name in required_dirs:
            dir_path = API_BASE_PATH / dir_name
            if not dir_path.exists():
                issues.append(f"Missing directory: {dir_name}")
                recommendations.append(f"Create {dir_name} directory")
        
        # Check for main.py
        main_path = API_BASE_PATH / "main.py"
        if not main_path.exists():
            issues.append("Missing main.py file")
            recommendations.append("Create FastAPI application entry point")
        
        # Check for requirements.txt
        req_path = API_BASE_PATH / "requirements.txt"
        if not req_path.exists():
            issues.append("Missing requirements.txt")
            recommendations.append("Create requirements file with dependencies")
        
        # Check for .env file
        env_path = API_BASE_PATH / ".env"
        if not env_path.exists():
            issues.append("Missing .env file")
            recommendations.append("Create environment configuration file")
        
        # Check for tests
        tests_path = API_BASE_PATH / "tests"
        if tests_path.exists():
            test_files = list(tests_path.glob("test_*.py"))
            if not test_files:
                issues.append("No test files found")
                recommendations.append("Add test files for endpoints")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "structure": {
                "has_main": main_path.exists(),
                "has_requirements": req_path.exists(),
                "has_env": env_path.exists(),
                "has_tests": tests_path.exists() and len(list(tests_path.glob("test_*.py"))) > 0
            }
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


@app.tool()
async def list_available_tools() -> Dict[str, List[Dict[str, str]]]:
    """
    List all available MCP tools and their descriptions.
    
    Returns:
        Dictionary of tool categories and their tools
    """
    return {
        "api_tools": [
            {
                "name": "get_api_status",
                "description": "Check API health status and configuration"
            },
            {
                "name": "create_endpoint",
                "description": "Generate a new FastAPI endpoint with boilerplate code"
            },
            {
                "name": "create_model",
                "description": "Generate a Pydantic model for API requests/responses"
            }
        ],
        "testing_tools": [
            {
                "name": "generate_test",
                "description": "Generate test cases for API endpoints"
            }
        ],
        "documentation_tools": [
            {
                "name": "generate_api_docs",
                "description": "Generate API documentation from existing endpoints"
            }
        ],
        "database_tools": [
            {
                "name": "create_migration",
                "description": "Generate database migration files"
            }
        ],
        "utility_tools": [
            {
                "name": "validate_api_structure",
                "description": "Validate the API project structure"
            },
            {
                "name": "list_available_tools",
                "description": "List all available MCP tools"
            }
        ]
    }


# ==================== Main Entry Point ====================

async def main():
    """Main entry point for the MCP server."""
    try:
        # Initialize server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except KeyboardInterrupt:
        print("\nMCP Server shutting down...")
    except Exception as e:
        print(f"Error running MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())