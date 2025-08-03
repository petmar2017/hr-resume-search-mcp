#!/usr/bin/env python3
"""
Performance Testing Script for HR Resume Search API
Tests search endpoint response times and cache effectiveness
"""

import requests
import time
import json
import statistics
from typing import List, Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"
SEARCH_ENDPOINT = f"{BASE_URL}/api/v1/search/candidates"
METRICS_ENDPOINT = f"{BASE_URL}/metrics/summary"

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "Skills Search - Python",
        "payload": {
            "search_type": "skills_match",
            "skills": ["python", "fastapi"],
            "limit": 10,
            "offset": 0
        }
    },
    {
        "name": "Experience Search - Senior",
        "payload": {
            "search_type": "experience_match", 
            "min_experience_years": 5,
            "limit": 10,
            "offset": 0
        }
    },
    {
        "name": "Department Search - Engineering",
        "payload": {
            "search_type": "same_department",
            "departments": ["Engineering", "Software Development"],
            "limit": 10,
            "offset": 0
        }
    },
    {
        "name": "Combined Search - Senior Python Developer",
        "payload": {
            "search_type": "skills_match",
            "skills": ["python", "django", "react"],
            "min_experience_years": 3,
            "companies": ["TechCorp", "Innovate Inc"],
            "limit": 20,
            "offset": 0
        }
    }
]

def get_auth_token() -> str:
    """Get authentication token for API requests"""
    # For testing, we'll skip auth or use a test token
    # In a real scenario, you'd authenticate here
    return None

def make_search_request(payload: Dict[str, Any], token: str = None) -> Dict[str, Any]:
    """Make a search request and measure response time"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    start_time = time.time()
    try:
        response = requests.post(SEARCH_ENDPOINT, json=payload, headers=headers, timeout=10)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response_time_ms": response_time,
                "total_results": data.get("total_results", 0),
                "results_count": len(data.get("results", [])),
                "processing_time_ms": data.get("processing_time_ms", 0),
                "data": data
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "response_time_ms": response_time
            }
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "error": str(e),
            "response_time_ms": (end_time - start_time) * 1000
        }

def test_cache_effectiveness(payload: Dict[str, Any], repetitions: int = 5) -> Dict[str, Any]:
    """Test cache effectiveness by repeating the same search"""
    response_times = []
    processing_times = []
    
    print(f"Testing cache effectiveness with {repetitions} repetitions...")
    
    for i in range(repetitions):
        result = make_search_request(payload)
        if result["success"]:
            response_times.append(result["response_time_ms"])
            processing_times.append(result["processing_time_ms"])
            cache_status = "HIT" if result["processing_time_ms"] < 50 else "MISS"
            print(f"  Request {i+1}: {result['response_time_ms']:.1f}ms (processing: {result['processing_time_ms']:.1f}ms) [{cache_status}]")
        else:
            print(f"  Request {i+1}: FAILED - {result['error']}")
        
        time.sleep(0.5)  # Small delay between requests
    
    if response_times:
        return {
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "min_processing_time": min(processing_times),
            "max_processing_time": max(processing_times),
            "avg_processing_time": statistics.mean(processing_times),
            "cache_improvement": max(processing_times) - min(processing_times) if len(processing_times) > 1 else 0
        }
    else:
        return {"error": "No successful requests"}

def get_current_metrics() -> Dict[str, Any]:
    """Get current metrics from the API"""
    try:
        response = requests.get(METRICS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def run_performance_tests():
    """Run comprehensive performance tests"""
    print("🚀 HR Resume Search API - Performance Testing")
    print("=" * 60)
    
    # Get baseline metrics
    print("\n📊 Baseline Metrics:")
    baseline_metrics = get_current_metrics()
    if "error" not in baseline_metrics:
        print(f"  Total metrics tracked: {baseline_metrics.get('total_metrics', 'Unknown')}")
        print(f"  Generated at: {baseline_metrics.get('generated_at', 'Unknown')}")
    else:
        print(f"  Error getting metrics: {baseline_metrics['error']}")
    
    # Test authentication (skip for now)
    auth_token = get_auth_token()
    
    print(f"\n🎯 Testing {len(TEST_SCENARIOS)} search scenarios...")
    
    all_results = []
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n📋 Test {i}: {scenario['name']}")
        print("-" * 40)
        
        # Single request test
        result = make_search_request(scenario["payload"], auth_token)
        if result["success"]:
            print(f"✅ Success: {result['response_time_ms']:.1f}ms response time")
            print(f"   Processing time: {result['processing_time_ms']:.1f}ms")
            print(f"   Results found: {result['total_results']}")
            print(f"   Results returned: {result['results_count']}")
            
            # Test cache effectiveness  
            cache_test = test_cache_effectiveness(scenario["payload"], 3)
            if "error" not in cache_test:
                print(f"   Cache improvement: {cache_test['cache_improvement']:.1f}ms")
                print(f"   Avg response time: {cache_test['avg_response_time']:.1f}ms")
                
            all_results.append({
                "scenario": scenario["name"],
                "success": True,
                "response_time_ms": result["response_time_ms"],
                "processing_time_ms": result["processing_time_ms"],
                "total_results": result["total_results"],
                "cache_test": cache_test
            })
        else:
            print(f"❌ Failed: {result['error']}")
            print(f"   Response time: {result['response_time_ms']:.1f}ms")
            all_results.append({
                "scenario": scenario["name"],
                "success": False,
                "error": result["error"],
                "response_time_ms": result["response_time_ms"]
            })
    
    # Performance Summary
    print(f"\n📈 Performance Summary")
    print("=" * 60)
    
    successful_tests = [r for r in all_results if r["success"]]
    if successful_tests:
        response_times = [r["response_time_ms"] for r in successful_tests]
        processing_times = [r["processing_time_ms"] for r in successful_tests]
        
        print(f"Total tests: {len(TEST_SCENARIOS)}")
        print(f"Successful tests: {len(successful_tests)}")
        print(f"Failed tests: {len(TEST_SCENARIOS) - len(successful_tests)}")
        print()
        print("Response Time Statistics:")
        print(f"  Minimum: {min(response_times):.1f}ms")
        print(f"  Maximum: {max(response_times):.1f}ms")
        print(f"  Average: {statistics.mean(response_times):.1f}ms")
        print(f"  Median: {statistics.median(response_times):.1f}ms")
        print()
        print("Processing Time Statistics:")
        print(f"  Minimum: {min(processing_times):.1f}ms")
        print(f"  Maximum: {max(processing_times):.1f}ms")
        print(f"  Average: {statistics.mean(processing_times):.1f}ms")
        print(f"  Median: {statistics.median(processing_times):.1f}ms")
        
        # Performance Assessment
        print(f"\n🎯 Performance Assessment:")
        target_response_time = 200  # 200ms target
        avg_response_time = statistics.mean(response_times)
        
        if avg_response_time <= target_response_time:
            print(f"✅ EXCELLENT: Average response time ({avg_response_time:.1f}ms) meets <{target_response_time}ms target")
        elif avg_response_time <= target_response_time * 1.5:
            print(f"⚠️ GOOD: Average response time ({avg_response_time:.1f}ms) is close to {target_response_time}ms target")
        else:
            print(f"❌ NEEDS IMPROVEMENT: Average response time ({avg_response_time:.1f}ms) exceeds {target_response_time}ms target")
        
        # Cache effectiveness
        cache_improvements = [r["cache_test"].get("cache_improvement", 0) for r in successful_tests if "cache_test" in r]
        if cache_improvements and any(ci > 10 for ci in cache_improvements):
            avg_cache_improvement = statistics.mean([ci for ci in cache_improvements if ci > 0])
            print(f"✅ CACHE EFFECTIVE: Average improvement of {avg_cache_improvement:.1f}ms with caching")
        else:
            print(f"⚠️ CACHE NEEDS REVIEW: Limited cache effectiveness observed")
    else:
        print("❌ NO SUCCESSFUL TESTS - Please check API connectivity and authentication")
    
    # Get final metrics
    print(f"\n📊 Final Metrics:")
    final_metrics = get_current_metrics()
    if "error" not in final_metrics:
        print(f"  Metrics collected during test: {final_metrics.get('total_metrics', 'Unknown')}")
    else:
        print(f"  Error getting final metrics: {final_metrics['error']}")

if __name__ == "__main__":
    run_performance_tests()