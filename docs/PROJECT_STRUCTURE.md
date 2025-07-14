# C++ Struct Memory Parser - Project Structure

## Overview

This document describes the reorganized project structure after the file organization cleanup. The project now follows a clear, logical organization that separates concerns and makes navigation easier.

## Directory Structure

```
Python C Struct Converter/
├── 📁 src/                          # Source code (MVP Architecture)
│   ├── __init__.py                  # Package initialization
│   ├── main.py                      # Application entry point
│   ├── 📁 model/                    # Model layer (Business Logic)
│   │   ├── __init__.py
│   │   ├── struct_model.py          # Core struct parsing logic (supports bitfield, padding, pointer, mixed fields)
│   │   └── STRUCT_PARSING.md        # Model documentation
│   ├── 📁 view/                     # View layer (UI Components)
│   │   ├── __init__.py
│   │   └── struct_view.py           # Tkinter GUI implementation
│   ├── 📁 presenter/                # Presenter layer (Application Logic)
│   │   ├── __init__.py
│   │   └── struct_presenter.py      # Coordination between Model and View
│   └── 📁 config/                   # Configuration layer
│       ├── __init__.py
│       ├── ui_strings.py            # String management utilities
│       └── ui_strings.xml           # Localized UI strings
├── 📁 tests/                        # Test suite (covers bitfield, padding, pointer, mixed fields, etc.)
│   ├── __init__.py
│   ├── README.md                    # Comprehensive testing documentation
│   ├── test_input_conversion.py     # Input conversion mechanism tests
│   ├── test_string_parser.py        # String parser tests
│   ├── test_config_parser.py        # DEPRECATED: 已被 XML loader 標準化方案取代
│   └── 📁 data/                     # Test data and configuration
│       └── test_config.xml          # XML test configurations
├── 📁 docs/                         # Documentation hub
│   ├── README.md                    # Documentation index and navigation
│   ├── ARCHITECTURE.md              # MVP architecture documentation
│   ├── HEX_INPUT_CONVERSION.md      # Hex input conversion documentation
│   ├── 📁 analysis/                 # Technical analysis documents
│   │   └── input_conversion_analysis.md  # Input conversion analysis
│   └── 📁 development/              # Development plans and proposals
│       └── string_refactor_plan.md  # UI string refactoring plan
├── 📁 examples/                     # Example files (example.h covers bitfield and padding)
│   └── example.h                    # Sample C++ struct definition
├── 📄 README.md                     # Main project documentation
├── 📄 PROJECT_STRUCTURE.md          # This file
├── 📄 run.py                        # Application launcher
├── 📄 run_tests.py                  # Test runner
├── 📄 setup.py                      # Package configuration
├── 📄 requirements.txt              # Python dependencies
└── 📄 .gitignore                    # Git ignore rules
```

## File Organization Principles

### 1. **Separation of Concerns**
- **Source Code** (`src/`): Follows MVP architecture with clear layer separation
- **Tests** (`tests/`): Comprehensive test suite with organized test data
- **Documentation** (`docs/`): Categorized documentation for different audiences
- **Examples** (`examples/`): Sample files for users to learn from

### 2. **Documentation Categories**
- **Core Docs**: Main README and architecture documentation
- **Analysis**: Technical deep-dive documents
- **Development**: Plans and proposals for future development
- **Testing**: Complete testing guide and test architecture

### 3. **Test Organization**
- **Test Files**: Individual test modules for different components
- **Test Data**: XML configurations and test data files
- **Test Documentation**: Comprehensive testing guide

## Key Improvements

### ✅ **Before Reorganization**
- Files scattered across root directory
- Documentation mixed with source code
- Test data mixed with test files
- No clear documentation structure

### ✅ **After Reorganization**
- **Clean Root Directory**: Only essential files remain
- **Logical Grouping**: Related files are grouped together
- **Clear Navigation**: Easy to find specific types of files
- **Better Maintainability**: Easier to add new files in appropriate locations

## File Movement Summary

| Original Location | New Location | Reason |
|------------------|--------------|---------|
| `example.h` | `examples/example.h` | Group example files together |
| `input_conversion_analysis.md` | `docs/analysis/input_conversion_analysis.md` | Categorize analysis documents |
| `docs/string_refactor_plan.md` | `docs/development/string_refactor_plan.md` | Categorize development documents |
| `tests/test_config.xml` | `tests/data/test_config.xml` | Separate test data from test code |

## Import Path Updates

The following files were updated to reflect the new file locations:

1. **`tests/test_input_conversion.py`**: Updated XML config path
2. **`tests/README.md`**: Updated XML config references
3. **`README.md`**: Updated all file path references

## Benefits of New Structure

1. **🎯 Clear Purpose**: Each directory has a specific, well-defined purpose
2. **📚 Easy Navigation**: Users can quickly find what they're looking for
3. **🔧 Better Maintenance**: Developers know where to place new files
4. **📖 Organized Documentation**: Different types of docs are properly categorized
5. **🧪 Structured Testing**: Test data is separated from test logic
6. **📦 Professional Appearance**: Project looks more organized and professional

## Usage Guidelines

### For Users
- Start with `README.md` for installation and usage
- Check `examples/example.h` for sample struct definitions
- Use `docs/README.md` to navigate documentation

### For Developers
- Place new source code in appropriate `src/` subdirectories
- Add tests to `tests/` directory
- Place test data in `tests/data/`
- Add documentation to appropriate `docs/` subdirectories

### For Contributors
- Follow the existing structure when adding new files
- Update this document if adding new directories
- Ensure all import paths are updated when moving files 