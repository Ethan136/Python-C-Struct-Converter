# C++ Struct Memory Parser - Documentation

## Overview

This directory contains all documentation for the C++ Struct Memory Parser project, organized by category for easy navigation.

## Documentation Structure

### 📋 Core Documentation
- **[README.md](../README.md)** - Main project documentation and user guide
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Project structure and organization guide

### 🏗️ Architecture Documents
- **[MVP_ARCHITECTURE_COMPLETE.md](architecture/MVP_ARCHITECTURE_COMPLETE.md)** - Complete MVP architecture guide with component comparisons
- **[STRUCT_PARSING.md](architecture/STRUCT_PARSING.md)** - Detailed struct parsing mechanism documentation

### 📊 Analysis Documents
- **[INPUT_CONVERSION_COMPLETE.md](analysis/INPUT_CONVERSION_COMPLETE.md)** - Comprehensive input conversion mechanism guide

### 🛠️ Development Documents
- **[string_refactor_plan.md](development/string_refactor_plan.md)** - Plan for UI string refactoring and internationalization

### 🧪 Testing Documentation
- **[tests/README.md](../tests/README.md)** - Complete testing guide and test architecture

## Quick Navigation

### For Users
1. Start with the main **[README.md](../README.md)** for installation and usage
2. Check **[examples/example.h](../examples/example.h)** for sample struct definitions

### For Developers
1. Read **[MVP_ARCHITECTURE_COMPLETE.md](architecture/MVP_ARCHITECTURE_COMPLETE.md)** to understand the complete MVP architecture
2. Review **[STRUCT_PARSING.md](architecture/STRUCT_PARSING.md)** for struct parsing details
3. Check **[INPUT_CONVERSION_COMPLETE.md](analysis/INPUT_CONVERSION_COMPLETE.md)** for input processing details
4. Follow **[tests/README.md](../tests/README.md)** for testing guidelines

### For Contributors
1. Review **[string_refactor_plan.md](development/string_refactor_plan.md)** for UI improvements
2. Follow the testing guidelines in **[tests/README.md](../tests/README.md)**

## Project Structure

```
├── src/                      # Source code (MVP architecture)
│   ├── model/               # Business logic
│   ├── view/                # UI components
│   ├── presenter/           # Application logic
│   └── config/              # Configuration
├── tests/                   # Test suite
│   ├── data/               # Test configuration files
│   └── README.md           # Testing documentation
├── docs/                    # Documentation (this directory)
│   ├── architecture/       # Architecture and design documents
│   ├── analysis/           # Technical analysis
│   ├── development/        # Development plans
│   └── README.md           # This file
├── examples/               # Example files
└── README.md               # Main project documentation
```

## Document Categories

### 🏗️ Architecture Documents (`architecture/`)
- **MVP_ARCHITECTURE_COMPLETE.md**: Complete guide to MVP architecture, component responsibilities, and design patterns
- **STRUCT_PARSING.md**: Detailed explanation of C++ struct parsing mechanism

### 📊 Analysis Documents (`analysis/`)
- **INPUT_CONVERSION_COMPLETE.md**: Comprehensive guide to hex input conversion process and requirements

### 🛠️ Development Documents (`development/`)
- **string_refactor_plan.md**: Plan for UI string refactoring and internationalization

## Contributing

When adding new documentation:
1. Place architecture documents in `architecture/`
2. Place analysis documents in `analysis/`
3. Place development plans in `development/`
4. Update this README.md with new entries
5. Ensure all links are working correctly 