# C++ Struct Memory Parser (GUI Version - MVP Architecture)

This project provides a graphical user interface (GUI) tool built with Python and Tkinter to parse the memory layout of a C++ struct. It has been refactored to follow the Model-View-Presenter (MVP) architectural pattern for better modularity, maintainability, and testability.

## Architecture: Model-View-Presenter (MVP)

- **Model (`src/model/`)**: Contains the core business logic, data structures, and data manipulation. It's independent of the UI.
  - `struct_model.py`: Handles parsing C++ struct definitions, calculating memory layouts (including padding), and interpreting raw hexadecimal data based on endianness.

- **View (`src/view/`)**: Responsible for displaying the user interface and handling user interactions. It's passive and doesn't contain any business logic.
  - `struct_view.py`: Implements the Tkinter GUI elements and methods to update the display and retrieve user input.

- **Presenter (`src/presenter/`)**: Acts as an intermediary between the Model and the View. It handles user events from the View, retrieves data from the Model, and updates the View accordingly. It contains the application's presentation logic.
  - `struct_presenter.py`: Manages the flow of data and events between `StructModel` and `StructView`.

- **Configuration (`src/config/`)**: Manages application configuration and internationalization.
  - `ui_strings.py`: String management utilities
  - `ui_strings.xml`: Localized UI strings

## Project Structure

```
├── src/                      # Source code
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Application entry point
│   ├── model/                # Model layer (business logic)
│   │   ├── __init__.py
│   │   ├── struct_model.py
│   │   └── STRUCT_PARSING.md
│   ├── view/                 # View layer (UI)
│   │   ├── __init__.py
│   │   └── struct_view.py
│   ├── presenter/            # Presenter layer (coordination)
│   │   ├── __init__.py
│   │   └── struct_presenter.py
│   └── config/               # Configuration layer
│       ├── __init__.py
│       ├── ui_strings.py
│       └── ui_strings.xml
├── tests/                    # Test files
│   ├── __init__.py
│   ├── README.md             # Test documentation
│   ├── test_string_parser.py
│   └── test_input_conversion.py
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md
│   └── string_refactor_plan.md
├── example.h                 # Example C++ struct file
├── run.py                    # Application launcher
├── run_tests.py              # Test runner
├── setup.py                  # Package configuration
├── requirements.txt          # Dependencies
├── input_conversion_analysis.md  # Input conversion analysis
└── README.md                 # This file
```

## Features

- **Graphical User Interface**: Easy-to-use window for all operations.
- **File Browser**: Select C++ header (`.h`) files directly from your file system.
- **Automatic Layout Calculation**: Parses a C++ `struct` definition and automatically calculates:
  - The size and alignment of each member.
  - The required memory padding between members.
  - The final total size of the struct.
- **Chunked Hexadecimal Data Input**: Allows inputting hex data in user-defined chunks (1, 4, or 8 bytes) for better readability and ease of entry.
- **Auto-Padding Hex Input**: Automatically pads shorter hexadecimal inputs with leading zeros to match the expected chunk size (e.g., `12` in a 4-byte field becomes `00000012`).
- **Configurable Byte Order**: Choose between Little Endian and Big Endian for data interpretation.
- **Clear Results Display**: Shows the parsed values for each member in both decimal and hexadecimal formats.

## Input Conversion Mechanism

The application implements a robust input conversion mechanism that handles various input scenarios:

### Field Expansion
- **4-byte fields**: Input `12` → Expands to `00000012` → Applies endianness
- **8-byte fields**: Input `123` → Expands to `0000000000000123` → Applies endianness
- **1-byte fields**: Input `1` → Expands to `01` → Applies endianness

### Empty Field Handling
- Empty 1/4/8 byte fields are automatically treated as all zeros
- Ensures consistent behavior regardless of user input completeness

### Endianness Support
- **Big Endian**: Most significant byte first
- **Little Endian**: Least significant byte first
- Consistent application across all field sizes

For detailed analysis, see [input_conversion_analysis.md](input_conversion_analysis.md).

## Requirements

- **Python 3.7+**: The script is written for Python 3.
- **Tkinter**: The GUI is built using the `tkinter` library, which is standard in most Python installations. If it's missing (which can happen on some macOS or Linux minimal installs), you may need to install it separately.

  For macOS, if you encounter errors, you can install `python-tk` via Homebrew:
  ```bash
  brew install python-tk
  ```

## Installation

### Option 1: Direct Run
```bash
# Clone or download the repository
cd "Python C Struct Converter"

# Run the application
python3 run.py
# or
python run.py
```

### Option 2: Install as Package
```bash
# Install the package
pip install -e .

# Run the application
python3 run.py
```

## How to Use

1. **Launch the Application**:
   ```bash
   python3 run.py
   ```

2. **Load a Struct Definition**:
   - The application window will appear.
   - Click the **"Browse..."** button.
   - Select a C++ header file (e.g., the `example.h` located in the project root) that contains a valid `struct` definition.

3. **Review the Layout**:
   - Once loaded, the "Struct Layout" area will display the parsed information: the struct's total size, alignment, and the offset, size, and type of each member.

4. **Input Hex Data**:
   - Choose your preferred "Input Unit Size" (1, 4, or 8 Bytes) and "Byte Order" (Little Endian or Big Endian).
   - The application will show how many hexadecimal characters are expected based on the struct's total size.
   - Fill in the generated input fields with your hexadecimal data. Shorter inputs will be automatically padded with leading zeros.

5. **Parse and View Results**:
   - Click the **"Parse Data"** button.
   - The "Parsed Values" area will populate with a table showing each member's name, its parsed value, and its original raw hex representation.

## Example File

An `example.h` file is included in the project root to demonstrate the functionality with a struct that requires memory padding.

## Development

### Running Tests
```bash
# Run all tests
python3 -m unittest discover tests -v

# Run specific test module
python3 -m unittest tests.test_input_conversion -v
python3 -m unittest tests.test_string_parser -v

# Use the test runner
python3 run_tests.py
python3 run_tests.py --test test_input_conversion

# Run from tests directory
cd tests
python3 -m unittest test_input_conversion -v
```

### Test Coverage
The test suite covers:
- ✅ Input conversion mechanism (field expansion, endianness, validation)
- ✅ String parser functionality
- ✅ Model integration
- ✅ Error handling and edge cases

For detailed test information, see [tests/README.md](tests/README.md).

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Architecture Benefits

1. **Maintainability**: Clear separation of concerns makes code easier to understand and modify
2. **Testability**: Each layer can be unit tested independently
3. **Reusability**: Model can be reused with different UI frameworks
4. **Scalability**: Easy to add new features without affecting existing code
5. **Team Development**: Different developers can work on different layers

For detailed architecture information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).