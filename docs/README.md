# C++ Struct Memory Parser - Documentation

## Overview

This directory contains all documentation for the C++ Struct Memory Parser project, organized by category for easy navigation.

## Documentation Structure

### 📋 Core Documentation
- **[README.md](../README.md)** - Main project documentation and user guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture documentation and design patterns

### 📊 Analysis Documents
- **[input_conversion_analysis.md](analysis/input_conversion_analysis.md)** - Comprehensive analysis of the hex input conversion mechanism

### 🛠️ Development Documents
- **[string_refactor_plan.md](development/string_refactor_plan.md)** - Plan for UI string refactoring and internationalization

### 🧪 Testing Documentation
- **[tests/README.md](../tests/README.md)** - Complete testing guide and test architecture

## Quick Navigation

### For Users
1. Start with the main **[README.md](../README.md)** for installation and usage
2. Check **[examples/example.h](../examples/example.h)** for sample struct definitions

### For Developers
1. Read **[ARCHITECTURE.md](ARCHITECTURE.md)** to understand the MVP architecture
2. Review **[input_conversion_analysis.md](analysis/input_conversion_analysis.md)** for input processing details
3. Check **[tests/README.md](../tests/README.md)** for testing guidelines

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
│   ├── analysis/           # Technical analysis
│   ├── development/        # Development plans
│   └── README.md           # This file
├── examples/               # Example files
└── README.md               # Main project documentation
```

## Contributing

When adding new documentation:
1. Place analysis documents in `analysis/`
2. Place development plans in `development/`
3. Update this README.md with new entries
4. Ensure all links are working correctly 