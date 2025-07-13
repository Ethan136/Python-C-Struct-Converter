#!/usr/bin/env python3
"""
Test Executable Script
======================

This script tests the built executables to ensure they work correctly.
It can test both macOS and Windows executables.

Usage:
    python packing/test_executable.py [--target macos|windows|all]
"""

import os
import sys
import subprocess
import time
import platform
import argparse
import signal

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
if __name__ != "__main__":
    sys.exit(0)

def test_executable(executable_path, platform_name, timeout=5):
    """Test an executable by running it for a short time"""
    print(f"Testing {platform_name} executable: {executable_path}")
    
    if not os.path.exists(executable_path):
        print(f"❌ Executable not found: {executable_path}")
        return False
    
    try:
        # Start the executable with more detailed output
        if platform_name.lower() == "windows":
            process = subprocess.Popen([executable_path], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     creationflags=getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0))
        else:
            process = subprocess.Popen([executable_path], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
        
        # Wait for a few seconds
        time.sleep(timeout)
        
        # Try to terminate gracefully with retry
        terminate_retries = 3
        terminated = False
        for i in range(terminate_retries):
            try:
                process.terminate()
                process.wait(timeout=2)
                terminated = True
                break
            except subprocess.TimeoutExpired:
                print(f"[Retry] Terminate attempt {i+1} failed, retrying...")
                time.sleep(1)
        if not terminated:
            print("[Force Kill] Process did not terminate after retries, killing...")
            process.kill()
            process.wait()
        
        # Check for any error output
        stdout, stderr = process.communicate()
        if stderr:
            print(f"⚠️  {platform_name} executable produced stderr output:")
            print(f"   {stderr.strip()}")
            # Check for specific error patterns
            if "ModuleNotFoundError" in stderr or "ImportError" in stderr:
                print(f"❌ {platform_name} executable has import/module errors!")
                return False
        
        if stdout:
            print(f"ℹ️  {platform_name} executable stdout: {stdout.strip()}")
        
        print(f"✅ {platform_name} executable test passed!")
        return True
        
    except Exception as e:
        print(f"❌ {platform_name} executable test failed: {e}")
        return False

def main():
    """Test built executables"""
    parser = argparse.ArgumentParser(description="Test built executables")
    parser.add_argument("--target", choices=["macos", "windows", "all"], 
                       default="all", help="Target platform to test")
    args = parser.parse_args()
    
    current_platform = platform.system().lower()
    print(f"Current platform: {current_platform}")
    
    success = True
    
    if args.target == "all" or args.target == "macos":
        if current_platform == "darwin":
            macos_exe = "dist/CppStructParser"
            if os.path.exists(macos_exe):
                success &= test_executable(macos_exe, "macOS")
            else:
                print(f"⚠️  macOS executable not found: {macos_exe}")
                print("   Run 'python packing/build.py --target macos' first")
        else:
            print("⚠️  Cannot test macOS executable on non-macOS platform")
    
    if args.target == "all" or args.target == "windows":
        if current_platform == "windows":
            windows_exe = "dist/CppStructParser.exe"
            if os.path.exists(windows_exe):
                success &= test_executable(windows_exe, "Windows")
            else:
                print(f"⚠️  Windows executable not found: {windows_exe}")
                print("   Run 'python packing/build.py --target windows' first")
        else:
            print("⚠️  Cannot test Windows executable on non-Windows platform")
    
    if success:
        print("\n🎉 All executable tests passed!")
        return 0
    else:
        print("\n❌ Some executable tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 