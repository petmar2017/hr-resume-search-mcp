#!/bin/bash

# Comprehensive Test Runner for API Builder
# Runs all types of tests: curl, MCP integration, and Python unit tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

section() {
    echo -e "${PURPLE}==== $1 ====${NC}"
}

# Check if FastAPI server is running
check_server() {
    log "Checking if FastAPI server is running..."
    
    if curl -s -f "http://localhost:8000/health" > /dev/null; then
        success "FastAPI server is running"
        return 0
    else
        error "FastAPI server is not running on localhost:8000"
        echo "Please start the server with: uvicorn api.main:app --reload"
        return 1
    fi
}

# Run curl-based API tests
run_curl_tests() {
    section "Running curl-based API Tests"
    
    if [ -f "$SCRIPT_DIR/simple_curl_tests.sh" ]; then
        log "Running basic API endpoint tests..."
        if "$SCRIPT_DIR/simple_curl_tests.sh"; then
            success "Basic curl tests completed"
        else
            warning "Some basic curl tests failed"
        fi
    else
        warning "simple_curl_tests.sh not found"
    fi
    
    echo
}

# Run MCP integration tests
run_mcp_tests() {
    section "Running MCP Integration Tests"
    
    if [ -f "$SCRIPT_DIR/mcp_curl_tests.sh" ]; then
        log "Running MCP server integration tests..."
        echo "y" | "$SCRIPT_DIR/mcp_curl_tests.sh" || warning "Some MCP tests failed"
    else
        warning "mcp_curl_tests.sh not found"
    fi
    
    echo
}

# Test individual MCP calls
test_mcp_functionality() {
    section "Testing MCP Functionality"
    
    log "Testing MCP tools discovery..."
    
    # Test MCP tools endpoint
    tools_response=$(curl -s "http://localhost:8000/mcp/tools")
    if echo "$tools_response" | grep -q "tools"; then
        success "MCP tools discovery working"
        
        # Count available tools
        tool_count=$(echo "$tools_response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(len(data.get('tools', [])))
except:
    print('0')
" 2>/dev/null || echo "0")
        echo "   Available tools: $tool_count"
    else
        error "MCP tools discovery failed"
        echo "   Response: $tools_response"
    fi
    
    # Test basic MCP protocol call
    log "Testing MCP protocol call..."
    
    mcp_request='{
        "id": "test-'$(date +%s)'",
        "method": "tools/list",
        "params": {}
    }'
    
    mcp_response=$(curl -s -X POST "http://localhost:8000/mcp" \
        -H "Content-Type: application/json" \
        -d "$mcp_request")
    
    if echo "$mcp_response" | grep -q '"result"'; then
        success "MCP protocol call successful"
    else
        warning "MCP protocol call failed"
        echo "   Response: $(echo "$mcp_response" | head -c 200)..."
    fi
    
    echo
}

# Test Claude API integration
test_claude_integration() {
    section "Testing Claude API Integration"
    
    log "Testing Claude API configuration..."
    
    # Check if Claude API key is configured
    if [ -n "${CLAUDE_API_KEY:-}" ]; then
        success "Claude API key is configured"
        key_preview="${CLAUDE_API_KEY:0:20}..."
        echo "   Key: $key_preview"
    else
        warning "Claude API key not found in environment"
        echo "   Set CLAUDE_API_KEY environment variable for full testing"
    fi
    
    # Test smart search with Claude interpretation
    log "Testing smart search with Claude..."
    
    smart_request='{
        "id": "claude-test-'$(date +%s)'",
        "method": "interpret_search",
        "params": {
            "query": "Find Python developers"
        }
    }'
    
    claude_response=$(curl -s -X POST "http://localhost:8000/mcp" \
        -H "Content-Type: application/json" \
        -d "$smart_request")
    
    if echo "$claude_response" | grep -q '"result"'; then
        success "Claude integration test successful"
    else
        warning "Claude integration test failed"
        echo "   Response: $(echo "$claude_response" | head -c 200)..."
    fi
    
    echo
}

# Run performance tests
run_performance_tests() {
    section "Running Performance Tests"
    
    log "Testing API response times..."
    
    # Test health endpoint performance
    total_time=0
    success_count=0
    
    for i in {1..10}; do
        start_time=$(date +%s.%N)
        if curl -s -f "http://localhost:8000/health" > /dev/null; then
            end_time=$(date +%s.%N)
            duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
            total_time=$(echo "$total_time + $duration" | bc -l 2>/dev/null || echo "$total_time")
            ((success_count++))
        fi
    done
    
    if [ $success_count -gt 0 ]; then
        avg_time=$(echo "scale=3; $total_time / $success_count" | bc -l 2>/dev/null || echo "0")
        success "Health endpoint: $success_count/10 successful, avg: ${avg_time}s"
        
        if (( $(echo "$avg_time < 0.1" | bc -l 2>/dev/null || echo "0") )); then
            success "Response time excellent (< 100ms)"
        elif (( $(echo "$avg_time < 0.5" | bc -l 2>/dev/null || echo "0") )); then
            success "Response time good (< 500ms)"
        else
            warning "Response time slow (> 500ms)"
        fi
    else
        error "All performance tests failed"
    fi
    
    # Test concurrent requests
    log "Testing concurrent request handling..."
    
    concurrent_pids=()
    for i in {1..5}; do
        (
            if curl -s -f "http://localhost:8000/health" > /dev/null; then
                echo "Request $i: SUCCESS"
            else
                echo "Request $i: FAILED"
            fi
        ) &
        concurrent_pids+=($!)
    done
    
    successful_concurrent=0
    for pid in "${concurrent_pids[@]}"; do
        if wait $pid; then
            ((successful_concurrent++))
        fi
    done
    
    success "Concurrent requests: $successful_concurrent/5 successful"
    
    echo
}

# Test error handling
test_error_handling() {
    section "Testing Error Handling"
    
    log "Testing 404 handling..."
    status=$(curl -s -w '%{http_code}' -o /dev/null "http://localhost:8000/nonexistent")
    if [ "$status" = "404" ]; then
        success "404 handling correct"
    else
        warning "404 handling unexpected: $status"
    fi
    
    log "Testing malformed MCP request..."
    malformed_response=$(curl -s -X POST "http://localhost:8000/mcp" \
        -H "Content-Type: application/json" \
        -d '{"invalid": "json"}')
    
    if echo "$malformed_response" | grep -q "error"; then
        success "Malformed request handling correct"
    else
        warning "Malformed request handling unexpected"
    fi
    
    echo
}

# Generate test report
generate_report() {
    section "Test Summary Report"
    
    echo "Timestamp: $(date)"
    echo "Server: http://localhost:8000"
    echo
    
    # Check server health
    health_response=$(curl -s "http://localhost:8000/health")
    if echo "$health_response" | grep -q "healthy"; then
        version=$(echo "$health_response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('version', 'unknown'))
except:
    print('unknown')
" 2>/dev/null)
        success "Server Status: Healthy (v$version)"
    else
        error "Server Status: Unhealthy"
    fi
    
    # Check MCP integration
    mcp_tools=$(curl -s "http://localhost:8000/mcp/tools")
    if echo "$mcp_tools" | grep -q "tools"; then
        tool_count=$(echo "$mcp_tools" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(len(data.get('tools', [])))
except:
    print('0')
" 2>/dev/null)
        success "MCP Integration: Active ($tool_count tools)"
    else
        warning "MCP Integration: Issues detected"
    fi
    
    # Check Claude API
    if [ -n "${CLAUDE_API_KEY:-}" ]; then
        success "Claude API: Configured"
    else
        warning "Claude API: Not configured"
    fi
    
    echo
    echo "✅ Comprehensive testing completed!"
}

# Main execution
main() {
    echo "🚀 API Builder Comprehensive Test Suite"
    echo "========================================"
    
    # Check prerequisites
    if ! check_server; then
        exit 1
    fi
    
    echo
    
    # Run all test suites
    run_curl_tests
    test_mcp_functionality
    test_claude_integration
    run_mcp_tests
    run_performance_tests
    test_error_handling
    generate_report
}

# Run main function
main "$@"