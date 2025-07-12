#!/usr/bin/env python3
"""
Setup script for C++ Struct Memory Parser
=========================================

A GUI tool for parsing C++ struct memory layouts using MVP architecture.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cpp-struct-parser",
    version="1.0.0",
    author="C++ Struct Parser Team",
    description="A GUI tool for parsing C++ struct memory layouts using MVP architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
    ],
    python_requires=">=3.7",
    install_requires=[
        "tkinter",  # Usually included with Python
    ],
    entry_points={
        "console_scripts": [
            "cpp-struct-parser=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "config": ["*.xml"],
    },
) 