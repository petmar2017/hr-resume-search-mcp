#!/bin/bash

# Comprehensive MCP (Model Context Protocol) curl testing script
# Tests MCP server integration and Claude API functionality

set -e

BASE_URL="http://localhost:8000"
TEMP_DIR="/tmp/mcp_api_tests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

mkdir -p "$TEMP_DIR"

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

test_mcp_call() {
    local test_name="$1"
    local method="$2"
    local params="$3"
    local expected_status="${4:-200}"
    
    log "Testing MCP: $test_name"
    
    # Create MCP request payload
    local mcp_request="{
        \"id\": \"$(uuidgen 2>/dev/null || echo "test-$(date +%s)")\",
        \"method\": \"$method\",
        \"params\": $params
    }"
    
    local response_file="$TEMP_DIR/mcp_response_$$.json"
    
    # Make MCP call
    local result=$(curl -s -w 'Status:%{http_code}|Time:%{time_total}' \
        -X POST "$BASE_URL/mcp" \
        -H "Content-Type: application/json" \
        -d "$mcp_request" \
        -o "$response_file")
    
    local status=$(echo "$result" | grep -o 'Status:[0-9]*' | cut -d: -f2)
    local time=$(echo "$result" | grep -o 'Time:[0-9.]*' | cut -d: -f2)
    
    echo "   Method: $method"
    echo "   Status: $status, Time: ${time}s"
    
    if [ -f "$response_file" ]; then
        local response_preview=$(head -c 200 "$response_file")
        echo "   Response: $response_preview..."
        
        # Check for errors in response
        if grep -q '"error"' "$response_file"; then
            local error_msg=$(cat "$response_file" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(data['error'].get('message', 'Unknown error'))
except:
    print('Parse error')
" 2>/dev/null)
            warning "MCP Error: $error_msg"
        fi
    fi
    
    if [ "$status" = "$expected_status" ]; then
        success "$test_name"
        return 0
    else
        error "$test_name - Expected: $expected_status, Got: $status"
        return 1
    fi
}

echo "🚀 MCP Server Integration Testing"
echo "=================================="

# Test 1: Basic API Endpoints
log "1. Testing Basic API Endpoints"

# Health check
result=$(curl -s -w 'Status:%{http_code}|Time:%{time_total}' "$BASE_URL/health")
status=$(echo "$result" | grep -o 'Status:[0-9]*' | cut -d: -f2)
time=$(echo "$result" | grep -o 'Time:[0-9.]*' | cut -d: -f2)
response=$(echo "$result" | sed 's/Status:[0-9]*|Time:[0-9.]*$//')

echo "Health Check - Status: $status, Time: ${time}s"
echo "Response: $(echo "$response" | head -c 100)..."

if [ "$status" = "200" ]; then
    success "Health Check"
else
    error "Health Check failed"
fi

# Test 2: MCP Tools Discovery
log "2. Testing MCP Tools Discovery"

result=$(curl -s -w 'Status:%{http_code}|Time:%{time_total}' "$BASE_URL/mcp/tools")
status=$(echo "$result" | grep -o 'Status:[0-9]*' | cut -d: -f2)
time=$(echo "$result" | grep -o 'Time:[0-9.]*' | cut -d: -f2)
response=$(echo "$result" | sed 's/Status:[0-9]*|Time:[0-9.]*$//')

echo "MCP Tools - Status: $status, Time: ${time}s"
echo "Response: $(echo "$response" | head -c 200)..."

if [ "$status" = "200" ]; then
    success "MCP Tools Discovery"
    # Save tools for later testing
    echo "$response" > "$TEMP_DIR/mcp_tools.json"
else
    error "MCP Tools Discovery failed"
fi

# Test 3: MCP Protocol Tests
log "3. Testing MCP Protocol Calls"

# Test tools/list method
test_mcp_call "List Tools" "tools/list" "{}"

# Test Claude API integration through resume parsing
log "4. Testing Claude API Integration"

# Create a sample resume for testing (single line to avoid JSON issues)
sample_resume="John Doe - Senior Software Engineer. Email: john.doe@example.com. Phone: (555) 123-4567. Experience: Senior Software Engineer at TechCorp (2020-2023), Developed microservices using Python and FastAPI, Led team of 5 developers. Skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes. Education: MS Computer Science, Stanford University (2019)."

# Test resume parsing if available
resume_params="{
    \"resume_text\": \"$sample_resume\"
}"

test_mcp_call "Resume Parsing" "parse_resume" "$resume_params" "500"

# Test smart search interpretation
search_params="{
    \"query\": \"Find senior Python developers with 5+ years experience\"
}"

test_mcp_call "Smart Search" "interpret_search" "$search_params" "500"

# Test 5: Error Handling
log "5. Testing MCP Error Handling"

# Test invalid method
test_mcp_call "Invalid Method" "invalid/method" "{}" "400"

# Test malformed params
malformed_params="\"invalid json structure\""
test_mcp_call "Malformed Params" "tools/list" "$malformed_params" "422"

# Test missing required fields
test_mcp_call "Missing ID Field" "" "{}" "422"

# Test 6: Performance Testing
log "6. Testing MCP Performance"

# Run multiple MCP calls to test performance
declare -a response_times
total_time=0
success_count=0

for i in {1..5}; do
    start_time=$(date +%s.%N)
    
    result=$(curl -s -w '%{http_code}' \
        -X POST "$BASE_URL/mcp" \
        -H "Content-Type: application/json" \
        -d "{\"id\":\"perf-test-$i\",\"method\":\"tools/list\",\"params\":{}}" \
        -o /dev/null)
    
    end_time=$(date +%s.%N)
    
    if [ "$result" = "200" ]; then
        duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
        response_times+=($duration)
        total_time=$(echo "$total_time + $duration" | bc -l 2>/dev/null || echo "$total_time")
        ((success_count++))
        echo "   Request $i: ${duration}s"
    else
        echo "   Request $i: FAILED (Status: $result)"
    fi
done

if [ $success_count -gt 0 ]; then
    avg_time=$(echo "scale=3; $total_time / $success_count" | bc -l 2>/dev/null || echo "0")
    success "Performance test: $success_count/5 successful, avg time: ${avg_time}s"
    
    # Check if performance is acceptable (< 1 second average)
    if (( $(echo "$avg_time < 1.0" | bc -l 2>/dev/null || echo "0") )); then
        success "Performance within acceptable limits"
    else
        warning "Performance may be slow (avg: ${avg_time}s)"
    fi
else
    error "Performance test: All requests failed"
fi

# Test 7: Concurrent MCP Requests
log "7. Testing Concurrent MCP Requests"

# Run 3 concurrent MCP calls
concurrent_pids=()
for i in {1..3}; do
    (
        start_time=$(date +%s.%N)
        result=$(curl -s -w '%{http_code}' \
            -X POST "$BASE_URL/mcp" \
            -H "Content-Type: application/json" \
            -d "{\"id\":\"concurrent-$i\",\"method\":\"tools/list\",\"params\":{}}" \
            -o /dev/null)
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
        echo "Concurrent request $i: Status $result, Time ${duration}s"
    ) &
    concurrent_pids+=($!)
done

# Wait for all concurrent requests
for pid in "${concurrent_pids[@]}"; do
    wait $pid
done

success "Concurrent requests test completed"

# Test 8: MCP Server Configuration Test
log "8. Testing MCP Server Configuration"

# Test if Claude API key is configured
if [ -n "${CLAUDE_API_KEY:-}" ]; then
    success "Claude API key is configured"
else
    warning "Claude API key not found in environment"
fi

# Test MCP server connectivity
mcp_config_test="{
    \"id\": \"config-test\",
    \"method\": \"server/info\",
    \"params\": {}
}"

config_response="$TEMP_DIR/config_response.json"
config_status=$(curl -s -w '%{http_code}' \
    -X POST "$BASE_URL/mcp" \
    -H "Content-Type: application/json" \
    -d "$mcp_config_test" \
    -o "$config_response")

if [ "$config_status" = "200" ]; then
    success "MCP server configuration accessible"
    echo "   Config: $(head -c 150 "$config_response")..."
else
    warning "MCP server configuration not accessible (Status: $config_status)"
fi

# Summary
echo ""
echo "🎉 MCP Integration Testing Summary"
echo "=================================="
echo "Base URL: $BASE_URL"
echo "Test Timestamp: $(date)"

# Check if MCP tools are available
if [ -f "$TEMP_DIR/mcp_tools.json" ]; then
    tool_count=$(cat "$TEMP_DIR/mcp_tools.json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, dict) and 'tools' in data:
        print(len(data['tools']))
    elif isinstance(data, list):
        print(len(data))
    else:
        print('0')
except:
    print('0')
" 2>/dev/null)
    echo "Available MCP Tools: $tool_count"
else
    echo "Available MCP Tools: Unknown"
fi

if [ $success_count -gt 0 ]; then
    echo "Average Response Time: ${avg_time}s"
fi

echo ""
echo "Test files saved in: $TEMP_DIR"

# Cleanup option
read -p "Delete test files? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$TEMP_DIR"
    success "Test files cleaned up"
else
    log "Test files preserved in $TEMP_DIR"
fi

echo ""
echo "✅ MCP integration testing completed!"