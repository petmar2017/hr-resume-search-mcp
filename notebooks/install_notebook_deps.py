#!/usr/bin/env python3
"""
Install notebook dependencies for Python 3.12
Works with system-managed Python environments
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("📦 Installing Notebook Dependencies for Python 3.12")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        print("   Please use Python 3.11+ (3.12 recommended)")
        sys.exit(1)
    
    print(f"✅ Using Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Core packages needed for notebooks
    packages = [
        "jupyter",
        "notebook",
        "ipykernel",
        "ipywidgets",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn", 
        "plotly",
        "httpx",
        "python-dotenv",
        "rich",  # Optional but nice to have
    ]
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("\n⚠️ Not in a virtual environment!")
        print("   System Python detected - using --user flag")
        print("\n   Recommended: Create a virtual environment:")
        print("   python3.12 -m venv notebook_env")
        print("   source notebook_env/bin/activate")
        print("")
        
        response = input("Continue with --user installation? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
        
        pip_args = ["--user"]
    else:
        print("✅ Virtual environment detected")
        pip_args = []
    
    # Install packages
    failed = []
    for package in packages:
        print(f"\n📦 Installing {package}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + pip_args + [package, "-q"],
                stdout=subprocess.DEVNULL
            )
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {package}")
            failed.append(package)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Installation Summary")
    print("=" * 60)
    
    if not failed:
        print("✅ All packages installed successfully!")
        
        # Install Jupyter kernel
        print("\n🔧 Installing Jupyter kernel...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "ipykernel", "install",
                "--user", "--name", f"python{sys.version_info.major}{sys.version_info.minor}",
                "--display-name", f"Python {sys.version_info.major}.{sys.version_info.minor} (HR API)"
            ])
            print("✅ Jupyter kernel installed")
        except:
            print("⚠️ Could not install Jupyter kernel")
        
        print("\n🎉 Setup complete!")
        print("\nTo use the notebooks:")
        print("1. Start Jupyter: jupyter notebook")
        print(f"2. Select kernel: Python {sys.version_info.major}.{sys.version_info.minor} (HR API)")
        
    else:
        print(f"⚠️ Some packages failed to install: {', '.join(failed)}")
        print("\nTry installing them manually:")
        for pkg in failed:
            print(f"   pip install {pkg}")

if __name__ == "__main__":
    main()