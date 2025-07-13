#!/usr/bin/env python3
"""
Test Build Configuration
========================

This script tests the build configuration to ensure everything is set up correctly.
"""

import os
import sys
import importlib

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    required_modules = [
        'src.main',
        'src.model.struct_model',
        'src.view.struct_view', 
        'src.presenter.struct_presenter',
        'src.config.ui_strings'
    ]
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False
    
    return True

def test_files():
    """Test if required files exist"""
    print("\nTesting required files...")
    
    required_files = [
        'src/main.py',
        'src/config/ui_strings.xml',
        'examples/example.h',
        'CppStructParser.spec'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            return False
    
    return True

def test_pyinstaller():
    """Test if PyInstaller is available"""
    print("\nTesting PyInstaller...")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller not installed")
        return False

def main():
    """Run all tests"""
    print("Testing build configuration...\n")
    
    tests = [
        test_imports,
        test_files,
        test_pyinstaller
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ All tests passed! Build configuration is ready.")
        print("\nYou can now:")
        print("1. Run 'python build_exe.py' to build locally")
        print("2. Push to GitHub to trigger automatic build")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 