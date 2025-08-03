#!/bin/bash
# Setup script for Jupyter notebooks with Python 3.12

echo "🚀 Setting up Jupyter notebooks for HR Resume Search API"
echo "========================================================="

# Check for Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 is required but not found!"
    echo "Please install Python 3.12 first:"
    echo "  brew install python@3.12  # macOS"
    echo "  apt install python3.12    # Ubuntu/Debian"
    exit 1
fi

echo "✅ Python 3.12 found: $(python3.12 --version)"

# Create virtual environment with Python 3.12
echo ""
echo "📦 Creating virtual environment with Python 3.12..."
python3.12 -m venv notebook_env

# Activate virtual environment
source notebook_env/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo ""
echo "📦 Installing notebook requirements..."
pip install -r requirements.txt

# Install Jupyter kernel for Python 3.12
echo ""
echo "🔧 Installing Jupyter kernel for Python 3.12..."
python -m ipykernel install --user --name python312 --display-name "Python 3.12 (HR API)"

# Create notebook utils if not exists
if [ ! -f "notebook_utils.py" ]; then
    echo ""
    echo "📝 Creating notebook_utils.py..."
    cat > notebook_utils.py << 'EOF'
"""
Utility functions for HR Resume Search API notebooks
Compatible with Python 3.12+
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.12+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"⚠️ Python {version.major}.{version.minor}.{version.micro} - Please use Python 3.12+")
        return False

def setup_path():
    """Add parent directory to path for imports"""
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    return parent_dir

def import_with_fallback(module_name, pip_name=None):
    """Import module with fallback installation"""
    try:
        return __import__(module_name)
    except ImportError:
        pip_name = pip_name or module_name
        print(f"Installing {pip_name}...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "-q"])
        return __import__(module_name)

# Auto-check on import
if __name__ != "__main__":
    check_python_version()
EOF
fi

# Test imports
echo ""
echo "🧪 Testing imports..."
python3.12 -c "
import sys
print(f'Python version: {sys.version}')

try:
    import jupyter
    import notebook
    import ipywidgets
    import matplotlib
    import seaborn
    import plotly
    import httpx
    import pandas
    import numpy
    print('✅ All core imports successful!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('Please run: pip install -r requirements.txt')
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To use the notebooks:"
echo "1. Start Jupyter: jupyter notebook"
echo "2. Select kernel: Python 3.12 (HR API)"
echo "3. Or run directly: python3.12 -m notebook"
echo ""
echo "Virtual environment created in: ./notebook_env"
echo "Activate it with: source notebook_env/bin/activate"