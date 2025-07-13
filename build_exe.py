#!/usr/bin/env python3
"""
Build Windows Executable Script
===============================

This script builds a Windows .exe file for the C++ Struct Memory Parser
using PyInstaller.

Usage:
    python build_exe.py
"""

import os
import sys
import subprocess
import shutil

def main():
    """Build the Windows executable"""
    print("Building Windows executable...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Build the executable
    print("Running PyInstaller...")
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller", "CppStructParser.spec"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Build successful!")
        print(f"Executable created at: {os.path.abspath('dist/CppStructParser.exe')}")
    else:
        print("❌ Build failed!")
        print("Error output:")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 