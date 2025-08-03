#!/bin/bash

# Simple curl-based API testing for actual FastAPI endpoints
# Tests the endpoints that actually exist in the current API

# Don't exit on failures - continue testing other endpoints

BASE_URL="http://localhost:8000"
TEMP_DIR="/tmp/simple_api_tests"

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

# Test function
test_api() {
    local name="$1"
    local endpoint="$2"
    local method="${3:-GET}"
    local data="$4"
    
    log "Testing: $name"
    
    local curl_cmd="curl -s -w 'Status:%{http_code}|Time:%{time_total}'"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl_cmd="$curl_cmd -X POST -H 'Content-Type: application/json' -d '$data'"
    fi
    
    local result=$(eval "$curl_cmd '$BASE_URL$endpoint'")
    local response=$(echo "$result" | sed 's/Status:[0-9]*|Time:[0-9.]*$//')
    local status=$(echo "$result" | grep -o 'Status:[0-9]*' | cut -d: -f2)
    local time=$(echo "$result" | grep -o 'Time:[0-9.]*' | cut -d: -f2)
    
    echo "   Status: $status, Time: ${time}s"
    echo "   Response: $(echo "$response" | head -c 100)..."
    
    if [ "$status" = "200" ]; then
        success "$name"
        return 0
    else
        error "$name - Status: $status"
        # Don't exit on failure - continue with other tests
        return 0
    fi
}

echo "🚀 Simple API Testing"
echo "====================="

# Test 1: Health Check
test_api "Health Check" "/health"

# Test 2: MCP Endpoints
# Note: /mcp endpoint requires POST with proper JSON body
test_api "MCP Tools" "/mcp/tools"

# Test 3: API Endpoints
test_api "Apps List" "/api/apps"
test_api "Search" "/api/search" "POST" '{"query":"test"}'
test_api "Search with Query" "/api/search" "POST" '{"query":"python"}'
test_api "Suggestions" "/api/suggestions"

# Test 4: Performance Testing
log "Performance Testing (5 requests)"
total_time=0
success_count=0

for i in {1..5}; do
    result=$(curl -s -w '%{time_total}' -o /dev/null "$BASE_URL/health")
    if [ $? -eq 0 ]; then
        total_time=$(echo "$total_time + $result" | bc -l 2>/dev/null || echo "$total_time")
        ((success_count++))
    fi
done

if [ $success_count -gt 0 ]; then
    avg_time=$(echo "scale=3; $total_time / $success_count" | bc -l 2>/dev/null || echo "0")
    success "Performance test: $success_count/5 successful, avg time: ${avg_time}s"
else
    error "Performance test: All requests failed"
fi

# Test 5: Error Handling
test_api "Invalid Endpoint" "/nonexistent"

echo ""
echo "✅ Simple API testing completed!"

# Cleanup
rm -rf "$TEMP_DIR"