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
├── src/                      # Source code (MVP Architecture)
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Application entry point
│   ├── model/                # Model layer (business logic)
│   │   ├── __init__.py
│   │   ├── struct_model.py           # Core struct logic
│   │   ├── struct_parser.py          # Struct parsing utilities
│   │   ├── layout.py                 # Layout calculation
│   │   ├── input_field_processor.py  # Input field processing
│   │   ├── STRUCT_PARSING.md         # Model documentation
│   │   └── README.md
│   ├── view/                 # View layer (UI)
│   │   ├── __init__.py
│   │   ├── struct_view.py
│   │   ├── GUI_DEVELOPER_GUIDE.md
│   │   └── README.md
│   ├── presenter/            # Presenter layer (coordination)
│   │   ├── __init__.py
│   │   ├── struct_presenter.py
│   │   ├── PRESENTER_DEVELOPER_GUIDE.md
│   │   └── README.md
│   └── config/               # Configuration layer
│       ├── __init__.py
│       ├── ui_strings.py
│       ├── ui_strings.xml
│       └── README.md
├── examples/                 # Example files
│   ├── example.h             # Example C++ struct file
│   └── README.md
├── docs/                     # Documentation
│   ├── README.md
│   ├── PROJECT_STRUCTURE.md
│   ├── ARCHITECTURE.md
│   ├── analysis/
│   │   └── input_conversion_analysis.md
│   └── development/
│       ├── string_refactor_plan.md
│       └── ... (other dev/design docs)
├── tests/                    # Test files & automation
│   ├── __init__.py
│   ├── README.md
│   ├── data/                 # XML test configs, .h files
│   │   ├── test_config.xml
│   │   └── ... (other XML/.h)
│   ├── test_string_parser.py
│   ├── test_input_conversion.py
│   ├── test_struct_model.py
│   ├── test_struct_view.py
│   ├── test_manual_struct_v3_integration.py
│   ├── test_struct_model_v3.py
│   ├── test_struct_view_padding.py
│   ├── base_xml_test_loader.py
│   ├── xml_manual_struct_loader.py
│   ├── xml_input_conversion_loader.py
│   ├── xml_input_field_processor_loader.py
│   ├── xml_struct_model_loader.py
│   └── ... (integration/refactor/mock tests)
├── packing/                  # Build/packaging scripts
│   ├── build.py
│   ├── executable_tester.py
│   ├── CppStructParser-windows.spec
│   ├── CppStructParser-macos.spec
│   └── README.md
├── .github/workflows/        # GitHub Actions workflows
│   ├── build-windows-exe.yml
│   ├── release.yml
│   └── pr-check.yml
├── run.py                    # Application launcher
├── run_tests.py              # Test runner
├── run_all_tests.py          # Cross-platform test runner (separates GUI/non-GUI tests)
├── build_exe.py              # Local build script
├── test_build.py             # Build configuration test
├── CppStructParser.spec      # PyInstaller specification
├── setup.py                  # Package configuration
├── requirements.txt          # Dependencies
├── DEPLOYMENT.md             # Deployment guide
├── .gitignore                # Git ignore rules
├── .venv/                    # Python virtual environment (not versioned)
├── dist/                     # Build output (not versioned)
├── build/                    # Build temp files (not versioned)
└── README.md                 # This file
```

- 各子資料夾皆有 README 或開發者指南，詳細說明模組職責與擴充方式。
- `tests/` 內含完整自動化測試、XML loader、integration/refactor/mock 測試，`data/` 內有多份 XML 測資與 .h 範例。
- `packing/` 目錄包含打包/測試腳本與 spec。
- `.venv/`、`dist/`、`build/`、`.gitignore` 為輔助/產物目錄。

## Developer Guides

- [src/view/GUI_DEVELOPER_GUIDE.md](src/view/GUI_DEVELOPER_GUIDE.md): GUI 元件結構、事件流程與擴充指引
- [src/presenter/PRESENTER_DEVELOPER_GUIDE.md](src/presenter/PRESENTER_DEVELOPER_GUIDE.md): Presenter 事件流、狀態管理、錯誤處理設計
- [src/model/input_field_processor.py](src/model/input_field_processor.py): Input 處理 API 與用法（見檔案開頭 docstring）
- **Pragma pack TDD 實作與測試覆蓋：**
  - `src/model/layout.py` 已支援 `pack_alignment` 參數，對應 `#pragma pack` 行為。
  - `tests/utils/test_pack_alignment_placeholder.py` 有單元測試驗證 pack_alignment=1 行為。
  - 詳細設計與進度請見 `docs/development/v5_pragma_pack.md`。

## Example Files

- [examples/README.md](examples/README.md): 範例檔案格式、用途與擴充方式

## Features

- **Graphical User Interface**: Easy-to-use window for all operations.
- **File Browser**: Select C++ header (`.h`) files directly from your file system.
- **Automatic Layout Calculation**: Parses a C++ `struct` definition and automatically calculates:
  - The size and alignment of each member.
  - The required memory padding between members.
  - The final total size of the struct.
  - **Supports `#pragma pack` (pack_alignment) for alignment control.**
- **Bitfield Support**: Full support for C/C++ bitfield members (e.g., `int a : 1;`) with proper packing and storage unit alignment.
- **Manual Struct Definition**: Define structs directly in the GUI with a single value input field (no dynamic multi-column editing). The manual struct tab now only provides a single struct member value input, matching the original simple design.
- **Chunked Hexadecimal Data Input**: Allows inputting hex data in user-defined chunks (1, 4, or 8 bytes) for better readability and ease of entry.
- **Auto-Padding Hex Input**: Automatically pads shorter hexadecimal inputs with leading zeros to match the expected chunk size (e.g., `12` in a 4-byte field becomes `00000012`).
- **Configurable Byte Order**: Choose between Little Endian and Big Endian for data interpretation.
- **Clear Results Display**: Shows the parsed values for each member in both decimal and hexadecimal formats.
- **Struct Export**: Export manually defined structs to C header files with proper bitfield syntax.
- **Unified Parsing Logic**: Both `.H file tab` and `Manual Struct tab` use the same underlying parsing engine (`parse_struct_bytes`) for consistent results and maintainable code.
- **TDD-Driven Development**: Comprehensive test coverage with 31 automated tests covering GUI operations, parsing logic, display functionality, padding, and bitfield handling.
- **Real-time Size Display**: Each struct member shows its actual memory size in the editing table, helping users understand memory layout.
- **Debug Tab**: A dedicated Debug tab is always visible in the tab bar for all users. This tab allows inspection of cache, LRU, and auto-refresh status directly from the GUI, with no restrictions or hidden mode.

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
   - **All members will be automatically aligned and padded according to C++ standard struct alignment rules.**
   - The layout and final struct size will match what a C++ compiler would produce for the same member types and order.
   - **The manual struct page now only displays the standard struct layout (ttk.Treeview) at the bottom, showing each member and all inserted paddings/offsets in real time. The previous custom memory layout table has been removed. This behavior is fully verified by automated tests.**

4. **Export to Header**:
   - Export the manually defined struct to a C header file with proper bitfield syntax.

> **Note:** Manual struct mode now fully supports C++-style alignment and padding. All members are automatically aligned and padded as in C++.

## Recent Improvements

### Input Validation Enhancement (2024)
- **Robust Error Handling**: The application now gracefully handles invalid input in the struct size field (e.g., non-numeric characters like "把6")
- **Crash Prevention**: Prevents application crashes when users enter unexpected data types
- **Safe Defaults**: Automatically converts invalid inputs to safe default values (0) without throwing exceptions
- **TDD Implementation**: All improvements are thoroughly tested using Test-Driven Development methodology

For detailed technical information about recent improvements, see [docs/development/v3_define_struct_input2_design_plan.md](docs/development/v3_define_struct_input2_design_plan.md).

## Example File

An `examples/example.h` file is included with the project that contains sample struct definitions for testing.

## Automatic Deployment

This project includes GitHub Actions for automatic Windows .exe file generation:

### Quick Start
1. **Push to GitHub**: Any push to `main` or `master` branch triggers automatic build
2. **Download Artifact**: Find the built .exe file in the Actions tab
3. **Create Release**: Push a tag (e.g., `v1.0.g`) to automatically create a release with downloadable .exe

### Local Testing
```bash
# Test build configuration
python test_build.py

# Build locally
python build_exe.py
```

### Deployment Options
- **Continuous Build**: Every push creates a new build artifact
- **Release Build**: Tag-based releases with automatic GitHub Release creation
- **Local Build**: Use `build_exe.py` for local testing

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## XML 驅動測試架構

本專案所有核心測試（struct model、input conversion、input field processor 等）皆已標準化為 XML 驅動架構，具備以下優點：

- **高維護性**：測試資料集中於 `tests/data/`，易於擴充與管理
- **自動化**：所有測試自動讀取 XML 配置，無需修改 Python 測試程式
- **一致性**：各模組 loader 皆繼承 `BaseXMLTestLoader`，可彈性擴充 schema
- **易於擴充**：只需新增/編輯 XML 檔案，即可快速擴充測試案例

### 如何撰寫/擴充 XML 測試

1. 於 `tests/data/` 新增或擴充 XML 檔案（如 `test_struct_model_config.xml`）
2. 依照 loader 支援的 schema 新增 `<test_case>` 或 `<test_config>` 區塊
3. 測試程式會自動讀取所有 config 並驗證，無需改動 Python 程式

詳細教學與 schema 範例，請見 [`tests/README.md`](tests/README.md) 的「如何撰寫與擴充 XML 驅動測試」章節。

## Struct Member Format Notice (v4+)

> **Important:**
> - Starting from v4, this project **only supports the new struct member format**:
>   - Each member must have: `type`, `name`, and (optionally) `bit_size` (for bitfields).
>   - The legacy format (with `byte_size`, `_convert_legacy_member`, or any backward compatibility logic) is **no longer supported** in any part of the codebase, GUI, or tests.
>   - All parsing, validation, and export logic is unified on the new format, fully matching C++ struct/bitfield layout and alignment rules.
> - If you have old data or scripts using the legacy format, please migrate to the new format before upgrading.

For migration details and rationale, see [`docs/development/v4_data_type_refactor.md`](docs/development/v4_data_type_refactor.md).

## Test Import Convention (for Local & CI/CD)

All test files should:
- Add the `src` directory to `sys.path` at the top of the test file:
  ```python
  import sys, os
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
  ```
- Use **absolute imports** (never relative imports):
  ```python
  from src.model.struct_model import StructModel
  from src.model.struct_parser import parse_struct_definition_ast
  ```
- Do **not** use relative imports (e.g., `from ..model import ...` or `from . import ...`).

This ensures that tests run correctly both locally and in GitHub Actions CI/CD, regardless of the working directory or test runner.

## v6 Checklist 與 CI/CD 驗證
- v6 checklist 狀態請見 `v6_parallel_dev_checklist.yaml`，每次合併/PR 前請同步更新。
- 合併策略與流程請見 [docs/merge_policy.md](docs/merge_policy.md)。
- CI/CD 會自動執行 pytest、contract test、tools/check_checklist.py，未全綠不得合併。
- 本地可用 `python tools/check_checklist.py` 驗證 checklist 狀態。
