#!/usr/bin/env python3
"""
Test script for health endpoints
"""

import requests
import json
import time
import sys


def test_endpoint(url, endpoint_name):
    """Test a single endpoint"""
    try:
        print(f"Testing {endpoint_name}: {url}")
        start_time = time.time()
        
        response = requests.get(url, timeout=10)
        response_time = time.time() - start_time
        
        print(f"  Status: {response.status_code}")
        print(f"  Response time: {response_time:.3f}s")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ {endpoint_name} is healthy")
                if endpoint_name == "Health":
                    print(f"     Service: {data.get('service', 'unknown')}")
                    print(f"     Version: {data.get('version', 'unknown')}")
                elif endpoint_name == "Readiness":
                    print(f"     Status: {data.get('status', 'unknown')}")
                    checks = data.get('checks', {})
                    for check_name, check_status in checks.items():
                        if isinstance(check_status, dict):
                            status = check_status.get('status', 'unknown')
                        else:
                            status = check_status
                        print(f"     {check_name}: {status}")
                return True
            except json.JSONDecodeError:
                print(f"  ❌ Invalid JSON response")
                return False
        else:
            print(f"  ❌ {endpoint_name} failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ {endpoint_name} request failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ {endpoint_name} unexpected error: {e}")
        return False


def test_all_endpoints():
    """Test all health endpoints"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        ("/", "Root"),
        ("/health", "Health"),
        ("/readiness", "Readiness"),
        ("/metrics", "Metrics")
    ]
    
    print("🔍 Testing API Health Endpoints")
    print("=" * 50)
    
    results = []
    
    for path, name in endpoints:
        url = f"{base_url}{path}"
        success = test_endpoint(url, name)
        results.append((name, success))
        print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:15} {status}")
    
    print(f"\nResults: {passed}/{total} endpoints passed")
    
    if passed == total:
        print("🎉 All health endpoints are working!")
        return True
    else:
        print("⚠️  Some endpoints failed. Check server logs.")
        return False


if __name__ == "__main__":
    print("Starting health endpoint tests...")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    # Wait a moment for user to start server
    input("Press Enter when server is ready...")
    
    success = test_all_endpoints()
    sys.exit(0 if success else 1)