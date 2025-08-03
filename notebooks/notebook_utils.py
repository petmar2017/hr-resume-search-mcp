"""
Utility functions for Jupyter notebooks
Provides common functionality for API testing and data analysis
"""

import os
import sys
import json
import httpx
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv
from IPython.display import display, HTML, JSON
import base64
from io import BytesIO

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Configuration
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = os.getenv('API_PORT', '8000')
API_PREFIX = os.getenv('API_PREFIX', '/api/v1')
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
API_URL = f"{API_BASE_URL}{API_PREFIX}"


class APIClient:
    """Enhanced API client for testing"""
    
    def __init__(self, base_url: str = API_URL, timeout: float = 30.0):
        self.base_url = base_url
        self.client = httpx.Client(timeout=timeout)
        self.async_client = None
        self.token = None
        self.headers = {}
    
    def set_auth_token(self, token: str):
        """Set authentication token"""
        self.token = token
        self.headers['Authorization'] = f"Bearer {token}"
    
    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """GET request"""
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        return self.client.get(url, headers=self.headers, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """POST request"""
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        return self.client.post(url, headers=self.headers, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> httpx.Response:
        """PUT request"""
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        return self.client.put(url, headers=self.headers, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """DELETE request"""
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        return self.client.delete(url, headers=self.headers, **kwargs)
    
    async def async_get(self, endpoint: str, **kwargs) -> httpx.Response:
        """Async GET request"""
        if not self.async_client:
            self.async_client = httpx.AsyncClient(timeout=30.0)
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        return await self.async_client.get(url, headers=self.headers, **kwargs)
    
    async def async_post(self, endpoint: str, **kwargs) -> httpx.Response:
        """Async POST request"""
        if not self.async_client:
            self.async_client = httpx.AsyncClient(timeout=30.0)
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        return await self.async_client.post(url, headers=self.headers, **kwargs)
    
    def close(self):
        """Close client connections"""
        self.client.close()
        if self.async_client:
            asyncio.run(self.async_client.aclose())


def get_api_client(base_url: str = API_URL) -> APIClient:
    """Get configured API client"""
    return APIClient(base_url)


def authenticate(email: str, password: str, client: Optional[APIClient] = None) -> Tuple[str, APIClient]:
    """
    Authenticate and get JWT token
    
    Args:
        email: User email
        password: User password
        client: Optional API client
    
    Returns:
        Tuple of (token, client)
    """
    if not client:
        client = get_api_client()
    
    response = client.post('/auth/login', json={
        'email': email,
        'password': password
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        client.set_auth_token(token)
        return token, client
    else:
        raise Exception(f"Authentication failed: {response.text}")


def upload_resume(file_path: str, client: APIClient) -> Dict[str, Any]:
    """
    Upload a resume file
    
    Args:
        file_path: Path to resume file
        client: Authenticated API client
    
    Returns:
        Upload response data
    """
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, 'application/pdf')}
        response = client.post('/resumes/upload', files=files)
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Upload failed: {response.text}")


def search_candidates(
    query: str = None,
    filters: Dict[str, Any] = None,
    client: Optional[APIClient] = None
) -> pd.DataFrame:
    """
    Search for candidates
    
    Args:
        query: Search query
        filters: Search filters
        client: API client
    
    Returns:
        DataFrame with search results
    """
    if not client:
        client = get_api_client()
    
    params = {}
    if query:
        params['q'] = query
    if filters:
        params.update(filters)
    
    response = client.get('/search', params=params)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        return pd.DataFrame(results)
    else:
        raise Exception(f"Search failed: {response.text}")


def visualize_results(df: pd.DataFrame, chart_type: str = 'bar') -> go.Figure:
    """
    Visualize search results
    
    Args:
        df: Results DataFrame
        chart_type: Type of chart (bar, pie, scatter, etc.)
    
    Returns:
        Plotly figure
    """
    if chart_type == 'bar':
        # Skills distribution
        if 'skills' in df.columns:
            skills_data = df['skills'].explode().value_counts().head(10)
            fig = px.bar(
                x=skills_data.values,
                y=skills_data.index,
                orientation='h',
                title='Top 10 Skills',
                labels={'x': 'Count', 'y': 'Skill'}
            )
            return fig
    
    elif chart_type == 'pie':
        # Department distribution
        if 'department' in df.columns:
            dept_data = df['department'].value_counts()
            fig = px.pie(
                values=dept_data.values,
                names=dept_data.index,
                title='Department Distribution'
            )
            return fig
    
    elif chart_type == 'scatter':
        # Experience vs Match Score
        if 'experience_years' in df.columns and 'match_score' in df.columns:
            fig = px.scatter(
                df,
                x='experience_years',
                y='match_score',
                title='Experience vs Match Score',
                labels={'experience_years': 'Years of Experience', 'match_score': 'Match Score'}
            )
            return fig
    
    # Default: table view
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns)),
        cells=dict(values=[df[col] for col in df.columns])
    )])
    return fig


def generate_report(
    test_results: Dict[str, Any],
    output_file: str = None
) -> str:
    """
    Generate test report
    
    Args:
        test_results: Dictionary of test results
        output_file: Optional output file path
    
    Returns:
        HTML report
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate statistics
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results.values() if r.get('success', False))
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Generate HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 5px; }}
            .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
            .metric {{ background: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; }}
            .metric-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
            .success {{ color: #4CAF50; }}
            .failure {{ color: #f44336; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #f5f5f5; }}
            .test-passed {{ background: #E8F5E9; }}
            .test-failed {{ background: #FFEBEE; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>API Test Report</h1>
            <p>Generated: {timestamp}</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div>Total Tests</div>
                <div class="metric-value">{total_tests}</div>
            </div>
            <div class="metric">
                <div>Passed</div>
                <div class="metric-value success">{passed_tests}</div>
            </div>
            <div class="metric">
                <div>Failed</div>
                <div class="metric-value failure">{failed_tests}</div>
            </div>
            <div class="metric">
                <div>Success Rate</div>
                <div class="metric-value">{success_rate:.1f}%</div>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for test_name, result in test_results.items():
        status = "✅ Passed" if result.get('success', False) else "❌ Failed"
        response_time = f"{result.get('response_time', 0):.3f}s"
        details = result.get('message', '')
        row_class = "test-passed" if result.get('success', False) else "test-failed"
        
        html += f"""
                <tr class="{row_class}">
                    <td>{test_name}</td>
                    <td>{status}</td>
                    <td>{response_time}</td>
                    <td>{details}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(html)
    
    return html


def test_endpoint(
    endpoint: str,
    method: str = 'GET',
    data: Dict[str, Any] = None,
    expected_status: int = 200,
    client: Optional[APIClient] = None
) -> Dict[str, Any]:
    """
    Test a single endpoint
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        data: Request data
        expected_status: Expected status code
        client: API client
    
    Returns:
        Test result dictionary
    """
    if not client:
        client = get_api_client()
    
    start_time = datetime.now()
    
    try:
        if method.upper() == 'GET':
            response = client.get(endpoint, params=data)
        elif method.upper() == 'POST':
            response = client.post(endpoint, json=data)
        elif method.upper() == 'PUT':
            response = client.put(endpoint, json=data)
        elif method.upper() == 'DELETE':
            response = client.delete(endpoint)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': response.status_code == expected_status,
            'status_code': response.status_code,
            'expected_status': expected_status,
            'response_time': response_time,
            'response_data': response.json() if response.content else None,
            'message': 'OK' if response.status_code == expected_status else f"Expected {expected_status}, got {response.status_code}"
        }
    
    except Exception as e:
        return {
            'success': False,
            'status_code': None,
            'expected_status': expected_status,
            'response_time': (datetime.now() - start_time).total_seconds(),
            'response_data': None,
            'message': str(e)
        }


async def load_test(
    endpoint: str,
    num_requests: int = 100,
    concurrent: int = 10,
    client: Optional[APIClient] = None
) -> pd.DataFrame:
    """
    Perform load testing on an endpoint
    
    Args:
        endpoint: API endpoint
        num_requests: Total number of requests
        concurrent: Number of concurrent requests
        client: API client
    
    Returns:
        DataFrame with load test results
    """
    if not client:
        client = get_api_client()
    
    results = []
    
    async def make_request(index: int):
        start_time = datetime.now()
        try:
            response = await client.async_get(endpoint)
            response_time = (datetime.now() - start_time).total_seconds()
            results.append({
                'request_id': index,
                'timestamp': start_time,
                'response_time': response_time,
                'status_code': response.status_code,
                'success': response.status_code == 200
            })
        except Exception as e:
            results.append({
                'request_id': index,
                'timestamp': start_time,
                'response_time': (datetime.now() - start_time).total_seconds(),
                'status_code': None,
                'success': False,
                'error': str(e)
            })
    
    # Run requests in batches
    for i in range(0, num_requests, concurrent):
        batch = [make_request(j) for j in range(i, min(i + concurrent, num_requests))]
        await asyncio.gather(*batch)
    
    return pd.DataFrame(results)


def display_metrics_dashboard(metrics: Dict[str, Any]):
    """
    Display a metrics dashboard
    
    Args:
        metrics: Dictionary of metrics to display
    """
    html = """
    <div style="background: #f0f0f0; padding: 20px; border-radius: 10px;">
        <h2 style="color: #333; margin-bottom: 20px;">📊 Metrics Dashboard</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
    """
    
    for key, value in metrics.items():
        # Determine color based on metric type
        if 'error' in key.lower() or 'fail' in key.lower():
            color = '#f44336'
        elif 'success' in key.lower() or 'pass' in key.lower():
            color = '#4CAF50'
        else:
            color = '#2196F3'
        
        # Format value
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        elif isinstance(value, bool):
            formatted_value = "Yes" if value else "No"
        else:
            formatted_value = str(value)
        
        html += f"""
            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="color: #666; font-size: 0.9em; margin-bottom: 5px;">
                    {key.replace('_', ' ').title()}
                </div>
                <div style="color: {color}; font-size: 1.5em; font-weight: bold;">
                    {formatted_value}
                </div>
            </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    display(HTML(html))


def create_sample_resume_data() -> Dict[str, Any]:
    """
    Create sample resume data for testing
    
    Returns:
        Sample resume dictionary
    """
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "location": "New York, NY",
        "summary": "Experienced software engineer with 5+ years in full-stack development",
        "experience": [
            {
                "company": "Tech Corp",
                "position": "Senior Software Engineer",
                "department": "Engineering",
                "desk": "Platform Team",
                "start_date": "2020-01-01",
                "end_date": None,
                "description": "Leading platform development initiatives"
            },
            {
                "company": "StartupXYZ",
                "position": "Software Engineer",
                "department": "Product",
                "desk": "Backend Team",
                "start_date": "2018-06-01",
                "end_date": "2019-12-31",
                "description": "Developed scalable backend services"
            }
        ],
        "skills": ["Python", "JavaScript", "Docker", "AWS", "PostgreSQL"],
        "education": [
            {
                "institution": "University of Technology",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "graduation_date": "2018-05-01"
            }
        ]
    }


# Export all utilities
__all__ = [
    'APIClient',
    'get_api_client',
    'authenticate',
    'upload_resume',
    'search_candidates',
    'visualize_results',
    'generate_report',
    'test_endpoint',
    'load_test',
    'display_metrics_dashboard',
    'create_sample_resume_data',
    'API_URL',
    'API_BASE_URL'
]