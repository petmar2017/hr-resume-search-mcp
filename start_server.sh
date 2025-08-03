#!/bin/bash

# Start HR Resume Search MCP API Server
# Ensures Python 3.12 venv is used

echo "Starting HR Resume Search MCP API Server..."

# Kill any existing server
pkill -f uvicorn 2>/dev/null || true

# Activate Python 3.12 venv
source .venv/bin/activate

# Verify Python version
python_version=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$python_version" != "3.12" ]; then
    echo "Error: Python 3.12 required, found $python_version"
    exit 1
fi

echo "Using Python $(python --version)"

# Start server
echo "Starting FastAPI server on http://localhost:8000..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload