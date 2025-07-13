#!/usr/bin/env python3
"""
Build Multi-Platform Executable Script
======================================

This script builds executables for the C++ Struct Memory Parser
using PyInstaller for both macOS and Windows.

Usage:
    python packing/build.py [--target macos|windows|all]
"""

import os
import sys
import subprocess
import shutil
import platform
import argparse

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_platform_spec():
    """Get the appropriate spec file for current platform"""
    current_platform = platform.system().lower()
    if current_platform == "darwin":
        return "packing/CppStructParser-macos.spec"
    elif current_platform == "windows":
        return "packing/CppStructParser-windows.spec"
    else:
        raise ValueError(f"Unsupported platform: {current_platform}")

def get_executable_name():
    """Get the expected executable name for current platform"""
    current_platform = platform.system().lower()
    if current_platform == "darwin":
        return "CppStructParser"
    elif current_platform == "windows":
        return "CppStructParser.exe"
    else:
        return "CppStructParser"

def build_executable(spec_file, platform_name):
    """Build executable using specified spec file"""
    print(f"Building {platform_name} executable...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build the executable
    print(f"Running PyInstaller with {spec_file}...")
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller", spec_file
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        exe_name = get_executable_name()
        print(f"✅ {platform_name} build successful!")
        print(f"Executable created at: {os.path.abspath(f'dist/{exe_name}')}")
        return True
    else:
        print(f"❌ {platform_name} build failed!")
        print("Error output:")
        print(result.stderr)
        return False

def main():
    """Build executables for supported platforms"""
    parser = argparse.ArgumentParser(description="Build multi-platform executables")
    parser.add_argument("--target", choices=["macos", "windows", "all"], 
                       default="all", help="Target platform to build for")
    args = parser.parse_args()
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    current_platform = platform.system().lower()
    print(f"Current platform: {current_platform}")
    
    success = True
    
    if args.target == "all":
        try:
            spec_file = get_platform_spec()
        except ValueError as e:
            print(e)
            print("Skipping build on unsupported platform.")
            return

        platform_name = "macOS" if current_platform == "darwin" else "Windows"
        success = build_executable(spec_file, platform_name)
        
        # If on macOS, also try to build Windows version (if possible)
        if current_platform == "darwin" and os.path.exists("packing/CppStructParser-windows.spec"):
            print("\n" + "="*50)
            print("Note: Building Windows version on macOS may not work properly.")
            print("For proper Windows builds, use GitHub Actions or a Windows machine.")
            print("="*50)
            
    elif args.target == "macos":
        if current_platform == "darwin":
            success = build_executable("packing/CppStructParser-macos.spec", "macOS")
        else:
            print("❌ Cannot build macOS executable on non-macOS platform")
            success = False
            
    elif args.target == "windows":
        if current_platform == "windows":
            success = build_executable("packing/CppStructParser-windows.spec", "Windows")
        else:
            print("❌ Cannot build Windows executable on non-Windows platform")
            success = False
    
    if success:
        print("\n🎉 Build completed successfully!")
        # List created executables
        if os.path.exists("dist"):
            print("Created executables:")
            for item in os.listdir("dist"):
                print(f"  - dist/{item}")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 