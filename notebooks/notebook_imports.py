"""
Standard imports for HR Resume Search API notebooks
Python 3.12+ compatible
"""

import sys
import os
from pathlib import Path

# Ensure Python 3.12+
if sys.version_info < (3, 12):
    print(f"⚠️ Warning: Python {sys.version_info.major}.{sys.version_info.minor} detected.")
    print("Notebooks are optimized for Python 3.12+")
    print("Some features may not work correctly.")

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Standard library imports
import asyncio
import json
import time
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, AsyncGenerator
import uuid
import base64

# Install helper function
def safe_import(module_name, package_name=None):
    """Safely import a module, installing if necessary"""
    package_name = package_name or module_name
    try:
        return __import__(module_name)
    except ImportError:
        print(f"⚠️ {package_name} not installed")
        print(f"   Please install with: pip install {package_name}")
        print(f"   Or run: ./setup_notebooks.sh")
        return None

# Third-party imports with graceful fallback
try:
    import httpx
except ImportError:
    httpx = safe_import("httpx")
    if httpx is None:
        print("   httpx is required for API calls")

try:
    import pandas as pd
except ImportError:
    pandas = safe_import("pandas")
    if pandas:
        pd = pandas
    else:
        pd = None
        print("   pandas is required for data analysis")

try:
    import numpy as np
except ImportError:
    numpy = safe_import("numpy")
    if numpy:
        np = numpy
    else:
        np = None
        print("   numpy is required for numerical computations")

# Visualization imports
try:
    import matplotlib
    import matplotlib.pyplot as plt
    # Use non-interactive backend for notebooks
    matplotlib.use('Agg')
    plt.style.use('default')  # Use default style
except ImportError:
    matplotlib = safe_import("matplotlib")
    if matplotlib:
        import matplotlib.pyplot as plt
        matplotlib.use('Agg')
    else:
        plt = None
        print("   matplotlib is required for plotting")

try:
    import seaborn as sns
    sns.set_theme()
    sns.set_palette("husl")
except ImportError:
    seaborn = safe_import("seaborn")
    if seaborn:
        sns = seaborn
        sns.set_theme()
    else:
        sns = None
        print("   seaborn is required for advanced visualizations")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except ImportError:
    plotly = safe_import("plotly")
    if plotly:
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
    else:
        go = None
        px = None
        make_subplots = None
        print("   plotly is required for interactive visualizations")

# IPython imports
try:
    from IPython.display import display, HTML, JSON, Markdown, clear_output, Image
except ImportError:
    print("⚠️ IPython not available - some display features may not work")
    # Create dummy functions
    def display(*args, **kwargs):
        print(*args)
    def HTML(content):
        return content
    def JSON(data):
        return json.dumps(data, indent=2)
    def Markdown(content):
        return content
    def clear_output(**kwargs):
        pass
    class Image:
        def __init__(self, *args, **kwargs):
            pass

try:
    import ipywidgets as widgets
    from ipywidgets import interact, interactive, fixed, IntSlider
except ImportError:
    ipywidgets = safe_import("ipywidgets")
    if ipywidgets:
        widgets = ipywidgets
        from ipywidgets import interact, interactive, fixed, IntSlider
    else:
        widgets = None
        interact = None
        interactive = None
        fixed = None
        IntSlider = None
        print("   ipywidgets is required for interactive widgets")

# Environment
try:
    from dotenv import load_dotenv
    load_dotenv('../.env')
except ImportError:
    dotenv = safe_import("python-dotenv", "python-dotenv")
    if dotenv:
        from dotenv import load_dotenv
        load_dotenv('../.env')
    else:
        load_dotenv = None
        print("   python-dotenv is required for environment variables")

# MCP imports (may not be available in all environments)
try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    print("ℹ️ MCP client not available - install with: pip install mcp")
    MCP_AVAILABLE = False
    # Create dummy classes
    class ClientSession:
        pass
    class stdio_client:
        pass

print(f"✅ Imports loaded successfully!")
print(f"📍 Python version: {sys.version}")
print(f"📍 Working directory: {Path.cwd()}")

# Export commonly used items
__all__ = [
    'asyncio', 'json', 'time', 'datetime', 'timedelta',
    'Dict', 'List', 'Any', 'Optional', 'AsyncGenerator',
    'Path', 'uuid', 'base64',
    'httpx', 'pd', 'np', 'plt', 'sns', 'go', 'px', 'make_subplots',
    'display', 'HTML', 'JSON', 'Markdown', 'clear_output', 'Image',
    'widgets', 'interact', 'interactive', 'fixed', 'IntSlider',
    'load_dotenv', 'os',
    'ClientSession', 'stdio_client', 'MCP_AVAILABLE'
]