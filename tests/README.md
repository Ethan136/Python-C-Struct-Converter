# Tests Directory

本文件為所有測試相關說明的唯一入口，包含：
- 測試架構與檔案說明
- 如何執行/擴充/自動化測試
- XML array 格式自動化測試說明

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
1. 在 `tests/test_config.xml` 新增 `<test_config>` 區塊，設定 `unit_size`、`input_values`（可用 array）、`expected_results`。
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

# Or use the test runner
python3 run_tests.py --test test_input_conversion
python3 run_tests.py --test test_string_parser
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