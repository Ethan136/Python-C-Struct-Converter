#!/usr/bin/env python3
"""
C++ Struct Memory Parser - Main Application Entry Point
=======================================================

This script launches the C++ Struct Memory Parser GUI application
built with the Model-View-Presenter (MVP) architectural pattern.

Usage:
    python3 run.py
    python run.py
"""

import sys
import os
import runpy

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    runpy.run_module("src.main", run_name="__main__") 