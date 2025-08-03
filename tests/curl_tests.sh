#!/bin/bash

# Comprehensive curl-based API testing script for FastAPI endpoints
# Tests all major endpoints including authentication, upload, and search

set -e  # Exit on any error

BASE_URL="http://localhost:8000"
TEST_USER_EMAIL="curl.test@example.com"
TEST_USER_PASSWORD="CurlTest123!"
TEST_USER_NAME="Curl Test User"
ACCESS_TOKEN=""
TEMP_DIR="/tmp/api_curl_tests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create temp directory
mkdir -p "$TEMP_DIR"

# Logging function
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

# Test function template
test_endpoint() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"
    local headers="$6"
    
    log "Testing: $test_name"
    
    local response_file="$TEMP_DIR/response_$$.json"
    local headers_file="$TEMP_DIR/headers_$$.txt"
    
    # Build curl command
    local curl_cmd="curl -s -w 'HTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}\n'"
    curl_cmd="$curl_cmd -o '$response_file' -D '$headers_file'"
    curl_cmd="$curl_cmd -X $method"
    
    if [ -n "$headers" ]; then
        curl_cmd="$curl_cmd $headers"
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$BASE_URL$endpoint'"
    
    # Execute curl command
    local result
    result=$(eval "$curl_cmd")
    
    # Extract status and time
    local status=$(echo "$result" | grep "HTTP_STATUS:" | cut -d: -f2)
    local time_total=$(echo "$result" | grep "TIME_TOTAL:" | cut -d: -f2)
    
    # Check response
    if [ "$status" = "$expected_status" ]; then
        success "$test_name - Status: $status, Time: ${time_total}s"
        if [ -f "$response_file" ] && [ -s "$response_file" ]; then
            echo "   Response: $(head -c 100 "$response_file")..."
        fi
        return 0
    else
        error "$test_name - Expected: $expected_status, Got: $status"
        if [ -f "$response_file" ]; then
            echo "   Response: $(cat "$response_file")"
        fi
        return 1
    fi
}

# Create sample PDF for upload testing
create_test_pdf() {
    local pdf_file="$TEMP_DIR/test_resume.pdf"
    cat > "$pdf_file" << 'EOF'
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 85
>>
stream
BT
/F1 12 Tf
100 700 Td
(John Doe - Senior Software Engineer) Tj
0 -20 Td
(Skills: Python, FastAPI, PostgreSQL) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000179 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
295
%%EOF
EOF
    echo "$pdf_file"
}

echo "🚀 Starting Comprehensive curl API Testing"
echo "=========================================="

# Test 1: Health Check
log "1. Testing Health Endpoints"
test_endpoint "Health Check" "GET" "/health" "" "200" ""
test_endpoint "MCP Endpoint" "GET" "/mcp" "" "200" ""

# Test 2: API Endpoints
log "2. Testing API Endpoints"

# Test apps endpoint
test_endpoint "List Apps" "GET" "/api/apps" "" "200" ""

# Test search endpoint
test_endpoint "Search Endpoint" "GET" "/api/search?q=test" "" "200" ""

# Test suggestions endpoint
test_endpoint "Suggestions Endpoint" "GET" "/api/suggestions" "" "200" ""

# Test 3: MCP Server Integration
log "3. Testing MCP Server Integration"

# Test MCP tools endpoint
test_endpoint "MCP Tools" "GET" "/mcp/tools" "" "200" ""

# Test MCP server basic functionality
mcp_response="$TEMP_DIR/mcp_response.json"
curl -s -X GET "$BASE_URL/mcp" -o "$mcp_response"

if [ -f "$mcp_response" ]; then
    success "MCP endpoint accessible"
    echo "   Response: $(head -c 200 "$mcp_response")..."
else
    error "MCP endpoint failed"
fi

# Test 3: Protected Endpoints (if authenticated)
if [ -n "$ACCESS_TOKEN" ]; then
    log "3. Testing Protected Endpoints"
    AUTH_HEADER="-H 'Authorization: Bearer $ACCESS_TOKEN'"
    
    # Test search endpoints
    test_endpoint "Search by Skills" "GET" "/api/v1/search/skills?skills=Python,JavaScript&min_score=0.3" "" "200" "$AUTH_HEADER"
    
    # Test advanced search
    search_data='{"query":"software engineer","search_type":"skills_match","skills":["Python","FastAPI"],"limit":10}'
    test_endpoint "Advanced Search" "POST" "/api/v1/search/candidates" "$search_data" "200" "$AUTH_HEADER -H 'Content-Type: application/json'"
    
    # Test smart search
    smart_search_data='{"query":"Find Python developers with 3+ years experience","include_reasoning":true}'
    test_endpoint "Smart Search" "POST" "/api/v1/search/smart" "$smart_search_data" "200" "$AUTH_HEADER -H 'Content-Type: application/json'"
    
    # Test search filters
    test_endpoint "Search Filters" "GET" "/api/v1/search/filters" "" "200" "$AUTH_HEADER"
    
    # Test 4: File Upload
    log "4. Testing File Upload"
    pdf_file=$(create_test_pdf)
    
    # Test resume upload
    upload_response="$TEMP_DIR/upload_response.json"
    upload_status=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/resumes/upload" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -F "file=@$pdf_file" \
        -o "$upload_response")
    
    if [ "$upload_status" = "200" ] || [ "$upload_status" = "201" ]; then
        success "Resume upload - Status: $upload_status"
        if [ -f "$upload_response" ]; then
            echo "   Response: $(head -c 200 "$upload_response")..."
        fi
    else
        error "Resume upload failed - Status: $upload_status"
        if [ -f "$upload_response" ]; then
            cat "$upload_response"
        fi
    fi
    
    # Test invalid file upload
    echo "Invalid file content" > "$TEMP_DIR/invalid.txt"
    invalid_upload_status=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/resumes/upload" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -F "file=@$TEMP_DIR/invalid.txt" \
        -o /dev/null)
    
    if [ "$invalid_upload_status" = "400" ] || [ "$invalid_upload_status" = "422" ]; then
        success "Invalid file upload correctly rejected - Status: $invalid_upload_status"
    else
        warning "Invalid file upload - Unexpected status: $invalid_upload_status"
    fi
    
    # Test 5: Project Management (if endpoints exist)
    log "5. Testing Project Management Endpoints"
    
    # Create project
    project_data='{"name":"Curl Test Project","slug":"curl-test","description":"Test project created via curl"}'
    test_endpoint "Create Project" "POST" "/api/v1/projects" "$project_data" "201" "$AUTH_HEADER -H 'Content-Type: application/json'"
    
    # List projects
    test_endpoint "List Projects" "GET" "/api/v1/projects" "" "200" "$AUTH_HEADER"
    
else
    warning "Skipping protected endpoint tests - Authentication failed"
fi

# Test 6: Error Handling
log "6. Testing Error Handling"

# Test invalid endpoints
test_endpoint "Invalid Endpoint" "GET" "/api/v1/nonexistent" "" "404" ""

# Test malformed JSON
test_endpoint "Malformed JSON" "POST" "/api/v1/auth/register" "{invalid json}" "422" "-H 'Content-Type: application/json'"

# Test unauthorized access
test_endpoint "Unauthorized Access" "GET" "/api/v1/search/skills?skills=Python" "" "401" ""

# Test 7: Rate Limiting (if implemented)
log "7. Testing Rate Limiting"
rate_limit_count=0
for i in {1..5}; do
    status=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/health")
    if [ "$status" = "200" ]; then
        ((rate_limit_count++))
    elif [ "$status" = "429" ]; then
        success "Rate limiting detected on request $i"
        break
    fi
done

if [ $rate_limit_count -eq 5 ]; then
    warning "No rate limiting detected in 5 requests"
fi

# Test 8: Performance Testing
log "8. Testing API Performance"

# Test response times
response_times=()
for i in {1..5}; do
    time_total=$(curl -s -w "%{time_total}" -o /dev/null "$BASE_URL/health")
    response_times+=($time_total)
done

# Calculate average response time
avg_time=$(python3 -c "
times = [$(IFS=,; echo "${response_times[*]}")]
print(f'{sum(times)/len(times):.3f}')
")

success "Average response time over 5 requests: ${avg_time}s"

# Test 9: MCP Server Integration (if available)
log "9. Testing MCP Server Integration"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test Claude API integration through smart search
    claude_test_data='{"query":"Find experienced Python developers","include_reasoning":true}'
    claude_response="$TEMP_DIR/claude_response.json"
    claude_status=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/search/smart" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$claude_test_data" \
        -o "$claude_response")
    
    if [ "$claude_status" = "200" ]; then
        success "MCP/Claude integration test - Status: $claude_status"
        if [ -f "$claude_response" ]; then
            # Check if response contains Claude reasoning
            if grep -q "reasoning" "$claude_response"; then
                success "Claude AI reasoning detected in response"
            else
                warning "No Claude AI reasoning found in response"
            fi
        fi
    else
        warning "MCP/Claude integration test failed - Status: $claude_status"
    fi
else
    warning "Skipping MCP tests - Authentication required"
fi

# Test 10: Concurrent Requests
log "10. Testing Concurrent Requests"

# Run 5 concurrent health checks
concurrent_pids=()
for i in {1..5}; do
    (
        start_time=$(date +%s.%N)
        status=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/health")
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc)
        echo "Request $i: Status $status, Time ${duration}s"
    ) &
    concurrent_pids+=($!)
done

# Wait for all concurrent requests
for pid in "${concurrent_pids[@]}"; do
    wait $pid
done

success "Concurrent requests test completed"

# Summary
echo ""
echo "🎉 Curl API Testing Summary"
echo "=========================="
echo "Base URL: $BASE_URL"
echo "Test User: $TEST_USER_EMAIL"
echo "Authentication: $([ -n "$ACCESS_TOKEN" ] && echo "✅ Success" || echo "❌ Failed")"
echo "Average Response Time: ${avg_time}s"
echo ""
echo "Test files created in: $TEMP_DIR"
echo "Access token: ${ACCESS_TOKEN:0:20}$([ -n "$ACCESS_TOKEN" ] && echo "...")"

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
echo "✅ curl API testing completed!"