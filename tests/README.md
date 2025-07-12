# Tests Directory

本文件為所有測試相關說明的唯一入口，包含：
- 測試架構與檔案說明
- 如何執行/擴充/自動化測試
- XML array 格式自動化測試說明
- 核心功能測試說明

## Test Files

### `test_string_parser.py`
Tests for the UI string configuration system.
- Tests XML string loading functionality
- Tests string retrieval with fallback handling

### `test_input_conversion.py`
Tests for the input conversion mechanism.
- Tests 4-byte field expansion (12 → 00000012)
- Tests 8-byte field expansion (123 → 0000000000000123)
- Tests 1-byte field expansion (1 → 01)
- Tests empty field handling (empty → all zeros)
- Tests endianness conversion (big/little endian)
- Tests value range validation
- Tests invalid input handling
- Tests integration with model parsing
- **支援 XML array 格式自動化測試**

### `test_struct_parsing_core.py`
Tests for core struct parsing functionality without GUI.
- Tests struct definition loading from .h files
- Tests input data processing with InputFieldProcessor
- Tests struct member parsing with both endianness
- Tests padding handling in structs
- Tests mixed field sizes (char, short, int, long long)
- Tests empty input handling
- **支援 XML 配置檔案自動化測試**

## 核心功能測試 (Core Function Testing)

### 概述
`test_struct_parsing_core.py` 提供不開啟 GUI 的核心功能測試，專門測試 struct 解析的核心邏輯。

### XML 配置檔案格式
測試配置使用 `tests/data/struct_parsing_test_config.xml`：

```xml
<struct_parsing_tests>
    <test_case name="struct_a_test" 
               struct_file="test_struct_a.h" 
               description="Test struct A { char s; long long val; }">
        <input_data>
            <input index="0" value="12" unit_size="1" description="char s field"/>
            <input index="1" value="123456789ABCDEF0" unit_size="8" description="long long val field"/>
        </input_data>
        <expected_results>
            <endianness name="little">
                <member name="s" expected_value="18" expected_hex="12" description="char s = 0x12"/>
                <member name="val" expected_value="1301540292310073344" expected_hex="f0debc9a78563412" description="long long val in little endian"/>
            </endianness>
            <endianness name="big">
                <member name="s" expected_value="18" expected_hex="12" description="char s = 0x12"/>
                <member name="val" expected_value="1311768467294899696" expected_hex="123456789abcdef0" description="long long val in big endian"/>
            </endianness>
        </expected_results>
    </test_case>
</struct_parsing_tests>
```

### 配置說明
- `struct_file`: 要測試的 .h 檔案名稱（位於 tests/data/ 目錄）
- `input_data`: 每個 input 代表一個輸入框的內容
  - `index`: 輸入框索引
  - `value`: 輸入的 hex 值
  - `unit_size`: 輸入框的 byte 大小 (1, 2, 4, 8)
  - `description`: 描述
- `expected_results`: 預期結果
  - `endianness`: 分別測試 little 和 big endian
  - `member`: 每個 struct member 的預期值
    - `expected_value`: 預期的十進位值
    - `expected_hex`: 預期的 hex 表示
    - `description`: 描述

### 執行核心功能測試
```bash
# 執行所有核心功能測試
python3 -m unittest tests.test_struct_parsing_core -v

# 執行特定測試
python3 -m unittest tests.test_struct_parsing_core.TestStructParsingCore.test_struct_a_parsing -v

# 執行所有配置測試
python3 -m unittest tests.test_struct_parsing_core.TestStructParsingCore.test_all_configurations -v
```

### 擴充核心功能測試
1. 在 `tests/data/` 目錄新增 .h 檔案
2. 在 `tests/data/struct_parsing_test_config.xml` 新增 `<test_case>` 區塊
3. 設定 `struct_file`、`input_data`、`expected_results`
4. 執行測試驗證

### 測試覆蓋範圍
- ✅ **Struct 定義解析**: 從 .h 檔案載入 struct 定義
- ✅ **輸入處理**: 使用 InputFieldProcessor 處理輸入資料
- ✅ **Endianness 轉換**: 支援 little/big endian
- ✅ **Padding 處理**: 正確處理 struct padding
- ✅ **混合欄位大小**: char, short, int, long long
- ✅ **空輸入處理**: 空輸入轉換為零值
- ✅ **數值驗證**: 驗證解析結果的正確性

## XML 測試自動化與簡化

本專案支援以 XML 檔案自動化測試輸入轉換機制，且支援簡化的 array 格式：

### 範例 (簡化 array 格式)
```xml
<test_config name="4byte_test" unit_size="4" description="Test 4-byte field expansion">
    <input_values>
        <array>123,234,456,567,11</array>
    </input_values>
    <expected_results>
        <result index="0" big_endian="00000123" little_endian="23010000">123</result>
        <result index="1" big_endian="00000234" little_endian="34020000">234</result>
        <result index="2" big_endian="00000456" little_endian="56040000">456</result>
        <result index="3" big_endian="00000567" little_endian="67050000">567</result>
        <result index="4" big_endian="00000011" little_endian="11000000">11</result>
    </expected_results>
</test_config>
```
- `<array>` 內容可用逗號、空白、換行分隔，程式會自動解析。
- 舊的 `<value index=...>` 格式也可混用。

### 如何擴充
1. 在 `tests/data/test_config.xml` 新增 `<test_config>` 區塊，設定 `unit_size`、`input_values`（可用 array）、`expected_results`。
2. 不需改動 Python 測試程式，會自動讀取所有 config 並驗證。

### 執行測試
```bash
cd tests
python3 -m unittest test_input_conversion -v
```
或在專案根目錄：
```bash
python3 run_tests.py --test test_input_conversion
```

### 測試結果
- 支援 array 格式的 XML 測試已通過。
- 你可以自由設計任何 1/4/8 byte、任意格數、任意數值的自動化測試。

## Running Tests

### Run All Tests
```bash
# From project root
python3 -m unittest discover tests -v

# Or use the test runner
python3 run_tests.py
```

### Run Specific Test Module
```bash
# From project root
python3 -m unittest tests.test_input_conversion -v
python3 -m unittest tests.test_string_parser -v
python3 -m unittest tests.test_struct_parsing_core -v

# Or use the test runner
python3 run_tests.py --test test_input_conversion
python3 run_tests.py --test test_string_parser
python3 run_tests.py --test test_struct_parsing_core
```

### Run Specific Test Method
```bash
# From project root
python3 -m unittest tests.test_input_conversion.TestInputConversion.test_4byte_field_expansion -v
```

### Run Tests from Tests Directory
```bash
cd tests
python3 -m unittest test_input_conversion -v
python3 -m unittest test_string_parser -v
python3 -m unittest test_struct_parsing_core -v
```

## Test Coverage

The tests cover the following areas:

### Input Conversion Mechanism (`test_input_conversion.py`)
- ✅ **4-byte field expansion**: Input `12` → Expand to `00000012`
- ✅ **8-byte field expansion**: Input `123` → Expand to `0000000000000123`
- ✅ **1-byte field expansion**: Input `1` → Expand to `01`
- ✅ **Empty field handling**: Empty fields → All zeros
- ✅ **Big endian conversion**: Correct byte ordering
- ✅ **Little endian conversion**: Correct byte ordering
- ✅ **Value range validation**: Prevents overflow
- ✅ **Invalid input handling**: Rejects non-hex characters
- ✅ **Model integration**: Works with struct parsing

### String Parser (`test_string_parser.py`)
- ✅ **XML loading**: Loads UI strings from XML files
- ✅ **String retrieval**: Gets strings with fallback handling

### Core Struct Parsing (`test_struct_parsing_core.py`)
- ✅ **Struct definition loading**: Loads struct definitions from .h files
- ✅ **Input processing**: Processes input data with InputFieldProcessor
- ✅ **Endianness handling**: Supports both little and big endian
- ✅ **Padding handling**: Correctly handles struct padding
- ✅ **Mixed field sizes**: Supports char, short, int, long long
- ✅ **Empty input handling**: Converts empty inputs to zero values
- ✅ **Value validation**: Validates parsed results against expected values

## Test Structure

All tests follow the standard Python `unittest` framework:

```python
import unittest

class TestClassName(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def tearDown(self):
        """Clean up test fixtures"""
        pass
    
    def test_specific_functionality(self):
        """Test description"""
        # Test implementation
        self.assertEqual(expected, actual)
```

## Adding New Tests

To add new tests:

1. Create a new file `test_<module_name>.py` in the `tests/` directory
2. Follow the existing naming convention and structure
3. Use descriptive test method names starting with `test_`
4. Include proper setup and teardown methods if needed
5. Add comprehensive docstrings explaining what each test does

## Test Requirements

- All tests must pass before merging code changes
- Tests should be comprehensive and cover edge cases
- Tests should be independent and not rely on external state
- Tests should clean up after themselves (use `tearDown` methods)
- Tests should provide clear error messages when they fail

## Continuous Integration

These tests are designed to be run in CI/CD pipelines. The test runner (`run_tests.py`) provides a simple interface for automated testing environments. 

# 測試說明

本測試套件涵蓋：
- struct 解析、記憶體佈局、bitfield、padding、pointer、混合欄位
- hex 資料解析（含 endianness、padding、bitfield、pointer、bool、short input 等）
- input field processor 的所有功能（pad_hex_input, process_input_field, convert_to_raw_bytes, is_supported_field_size），含正常與異常情境
- config/ui_strings.py 的 get_string，驗證 key 存在與不存在時的行為
- GUI 與 Presenter wiring、錯誤處理、UI 狀態
- 測試資料與範例 struct 覆蓋多種結構

所有 public API 均有單元測試，並涵蓋異常/邊界情境。 