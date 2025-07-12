# C++ Struct Memory Parser (GUI Version - MVP Architecture)

This project provides a graphical user interface (GUI) tool built with Python and Tkinter to parse the memory layout of a C++ struct. It has been refactored to follow the Model-View-Presenter (MVP) architectural pattern for better modularity, maintainability, and testability.

## Architecture: Model-View-Presenter (MVP)

- **Model (`src/model/`)**: Contains the core business logic, data structures, and data manipulation. It's independent of the UI.
  - `struct_model.py`: Handles parsing C++ struct definitions, calculating memory layouts (including padding), and interpreting raw hexadecimal data based on endianness.
  - **Supports bitfield members** (e.g., `int a : 1;`) with proper packing and storage unit alignment.
  - **Manual struct definition** with byte/bit size validation and export functionality.

- **View (`src/view/`)**: Responsible for displaying the user interface and handling user interactions. It's passive and doesn't contain any business logic.
  - `struct_view.py`: Implements the Tkinter GUI elements and methods to update the display and retrieve user input.
  - **Real-time remaining space display** showing available bits/bytes in manual struct mode.

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
├── examples/                  # Example files
│   └── example.h             # Example C++ struct file
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md
│   ├── analysis/
│   │   └── input_conversion_analysis.md  # Input conversion analysis
│   └── development/
│       └── string_refactor_plan.md
├── tests/                    # Test files
│   ├── __init__.py
│   ├── README.md             # Test documentation
│   ├── data/
│   │   └── test_config.xml   # Test configuration
│   ├── test_string_parser.py
│   └── test_input_conversion.py
├── run.py                    # Application launcher
├── run_tests.py              # Test runner
├── run_all_tests.py          # Cross-platform test runner (separates GUI/non-GUI tests)
├── setup.py                  # Package configuration
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Features

- **Graphical User Interface**: Easy-to-use window for all operations.
- **File Browser**: Select C++ header (`.h`) files directly from your file system.
- **Automatic Layout Calculation**: Parses a C++ `struct` definition and automatically calculates:
  - The size and alignment of each member.
  - The required memory padding between members.
  - The final total size of the struct.
- **Bitfield Support**: Full support for C/C++ bitfield members (e.g., `int a : 1;`) with proper packing and storage unit alignment.
- **Manual Struct Definition**: Define structs directly in the GUI with byte/bit size validation and real-time remaining space display.
- **Chunked Hexadecimal Data Input**: Allows inputting hex data in user-defined chunks (1, 4, or 8 bytes) for better readability and ease of entry.
- **Auto-Padding Hex Input**: Automatically pads shorter hexadecimal inputs with leading zeros to match the expected chunk size (e.g., `12` in a 4-byte field becomes `00000012`).
- **Configurable Byte Order**: Choose between Little Endian and Big Endian for data interpretation.
- **Clear Results Display**: Shows the parsed values for each member in both decimal and hexadecimal formats.
- **Struct Export**: Export manually defined structs to C header files with proper bitfield syntax.

## Bitfield Support

The application fully supports C/C++ bitfield members with the following features:

### Bitfield Parsing
- Parses bitfield declarations like `int a : 1;` from C++ header files
- Supports multiple bitfields in the same storage unit with proper bit offset calculation
- Handles bitfield packing across storage unit boundaries

### Manual Bitfield Definition
- Define bitfields directly in the GUI with byte/bit size specification
- Real-time validation ensuring total bit size matches struct size
- Automatic bit offset calculation and storage unit management

### Memory Layout
- Bitfields are packed according to C/C++ standards
- Storage units are aligned according to type alignment rules
- Mixed bitfield and regular member support

### Data Parsing
- Correctly extracts bitfield values from hex data considering endianness
- Handles bitfield values that span multiple bytes
- Supports all basic types: int, unsigned int, char, unsigned char

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

For detailed analysis, see [docs/analysis/input_conversion_analysis.md](docs/analysis/input_conversion_analysis.md).

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
   - Select a C++ header file (e.g., the `examples/example.h` located in the project) that contains a valid `struct` definition.

3. **Review the Layout**:
   - Once loaded, the "Struct Layout" area will display the parsed information: the struct's total size, alignment, and the offset, size, and type of each member.
   - Bitfield members will show additional information including bit offset and bit size.

4. **Input Hex Data**:
   - Choose your preferred "Input Unit Size" (1, 4, or 8 Bytes) and "Byte Order" (Little Endian or Big Endian).
   - The application will show how many hexadecimal characters are expected based on the struct's total size.
   - Fill in the generated input fields with your hexadecimal data. Shorter inputs will be automatically padded with leading zeros.

5. **Parse and View Results**:
   - Click the **"Parse Data"** button.
   - The "Parsed Values" area will populate with a table showing each member's name, its parsed value, and its original raw hex representation.

### Manual Struct Definition

1. **Switch to Manual Mode**:
   - Use the tab interface to switch to "Manual Struct Definition" mode.

2. **Set Struct Size**:
   - Enter the total size of the struct in bytes.

3. **Add Members**:
   - Add struct members with name, byte size, and bit size.
   - The interface will show real-time remaining space and validation.

4. **Export to Header**:
   - Export the manually defined struct to a C header file with proper bitfield syntax.

## Example File

An `examples/example.h` file is included in the project to demonstrate the functionality with a struct that requires memory padding and includes bitfield members.

## Development

For all test-related documentation, including how to run, extend, and automate tests (including XML array input), please see:

👉 [tests/README.md](tests/README.md)

### 測試自動化入口

推薦使用專案根目錄的 `run_all_tests.py` 腳本進行所有測試：

```bash
python run_all_tests.py
```
- 此腳本會自動分開執行 GUI 測試與非 GUI 測試，並彙總結果，適用於 Windows、macOS、Linux。
- 詳細說明請見：[docs/development/run_all_tests_usage.md](docs/development/run_all_tests_usage.md)

### Test-Driven Development (TDD)

The project follows TDD principles with comprehensive test coverage:

- **Unit Tests**: All core functionality is unit tested with pytest
- **Integration Tests**: End-to-end testing of struct parsing and data conversion
- **GUI Tests**: Tkinter interface testing (automatically skipped in headless environments)
- **XML Configuration Tests**: Automated testing using XML configuration files

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

## Recent Updates

### Bitfield and Padding Support
- Complete bitfield parsing and layout calculation
- Manual struct definition with byte/bit size validation
- Real-time remaining space display
- Struct export functionality with proper C syntax

### Validation and Testing
- Comprehensive validation logic for struct definitions
- TDD approach with extensive test coverage
- Cross-platform test automation
- GUI and non-GUI test separation

### Memory Layout Improvements
- Bit-level padding calculation for future alignment support
- Improved struct size validation
- Enhanced bitfield packing across storage units