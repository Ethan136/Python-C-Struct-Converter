#!/usr/bin/env python3
"""
Test runner for C++ Struct Memory Parser
========================================

This script runs all tests or specific test modules.
"""

import sys
import os
import unittest
import argparse

def run_all_tests():
    """Run all tests in the tests directory"""
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Discover and run all tests (ensure proper package top-level)
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir=start_dir, pattern='test_*.py', top_level_dir=project_root)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_specific_test(test_module):
    """Run a specific test module"""
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Import and run the specific test module
    test_path = os.path.join(project_root, 'tests', f'{test_module}.py')
    if not os.path.exists(test_path):
        print(f"Error: Test module '{test_module}' not found at {test_path}")
        return False
    
    # Load and run the test (treat tests as a package)
    pkg_name = f"tests.{test_module}" if not test_module.startswith('tests.') else test_module
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(pkg_name)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    parser = argparse.ArgumentParser(description='Run tests for C++ Struct Memory Parser')
    parser.add_argument('--test', '-t', 
                       help='Run specific test module (e.g., test_input_conversion)')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Run all tests (default)')
    
    args = parser.parse_args()
    
    if args.test:
        print(f"Running specific test: {args.test}")
        success = run_specific_test(args.test)
    else:
        print("Running all tests...")
        success = run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 