# Packing Directory

This directory contains all build and packaging related files for the C++ Struct Memory Parser project.

## Files

- `build.py` - Multi-platform build script
- `test_executable.py` - Executable testing script
- `CppStructParser-macos.spec` - PyInstaller spec for macOS
- `CppStructParser-windows.spec` - PyInstaller spec for Windows

## Usage

### Building Executables

```bash
# Build for current platform
python packing/build.py --target all

# Build macOS executable (on macOS only)
python packing/build.py --target macos

# Build Windows executable (on Windows only)
python packing/build.py --target windows
```

### Testing Executables

```bash
# Test all available executables
python packing/test_executable.py --target all

# Test macOS executable
python packing/test_executable.py --target macos

# Test Windows executable
python packing/test_executable.py --target windows
```

## Spec Files

The spec files are PyInstaller configuration files that define:
- Entry point (`../src/main.py`)
- Required data files (config, model, examples)
- Hidden imports (tkinter modules)
- Build settings for each platform

## Notes

- All paths in spec files are relative to the project root
- The build script automatically detects the current platform
- Executables are created in the `dist/` directory at project root
- GitHub Actions uses these same spec files for automated builds 