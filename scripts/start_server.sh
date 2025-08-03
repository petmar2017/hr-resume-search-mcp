#!/bin/bash

# Start HR Resume Search MCP API Server
# Ensures Python 3.12 venv is used

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting HR Resume Search MCP API Server..."
echo "Project root: $PROJECT_ROOT"

# Kill any existing server
pkill -f uvicorn 2>/dev/null || true

# Change to project root
cd "$PROJECT_ROOT"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Creating Python 3.12 virtual environment..."
    uv venv --python /opt/homebrew/bin/python3.12
    uv pip install -r requirements.txt -r requirements-dev.txt
fi

# Use venv directly without pyenv interference
echo "Using Python from .venv..."
.venv/bin/python --version

# Start server with venv python
echo "Starting FastAPI server on http://localhost:8000..."
exec .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload