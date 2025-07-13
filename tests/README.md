# Tests Directory

本文件為所有測試相關說明的唯一入口，包含：
- 測試架構與檔案說明
- 如何執行/擴充/自動化測試
- XML array 格式自動化測試說明
- 核心功能測試說明
- Bitfield 與手動 struct 定義測試
- TDD 測試流程說明

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

### `test_input_field_processor.py`
Tests for the InputFieldProcessor module.
- Tests hex input padding functionality
- Tests raw byte conversion with endianness
- Tests complete input processing pipeline
- Tests error handling and edge cases
- Tests supported field size validation

### `test_struct_parsing.py` *(新增)*
Tests for struct parsing and layout calculation.
- Tests struct definition parsing (parse_struct_definition)
- Tests bitfield parsing and validation
- Tests pointer type handling
- Tests unsigned type support
- Tests LayoutCalculator class functionality
- Tests memory layout calculation with padding
- Tests bitfield layout calculation

### `test_struct_model_integration.py` *(新增)*
Tests for StructModel integration functionality.
- Tests StructModel initialization and state management
- Tests struct loading from files
- Tests hex data parsing with various scenarios
- Tests endianness handling
- Tests bitfield data extraction
- Tests boolean and pointer value parsing
- Tests padding handling in parsed data
- Tests short input handling and zero padding

### `test_struct_parsing_core.py`
Tests for core struct parsing functionality without GUI.
- Tests struct definition loading from .h files
- Tests input data processing with InputFieldProcessor
- Tests struct member parsing with both endianness
- Tests padding handling in structs
- Tests mixed field sizes (char, short, int, long long)
- Tests empty input handling
- **支援 XML 配置檔案自動化測試**

### `test_struct_model.py` *(大幅擴充)*
Tests for core struct model functionality with comprehensive coverage.
- **Bitfield Support Tests**:
  - Tests bitfield parsing from C++ struct definitions
  - Tests bitfield layout calculation with storage units
  - Tests bitfield data extraction from hex data
  - Tests bitfield packing across storage unit boundaries
  - Tests mixed bitfield and regular member handling
- **Manual Struct Definition Tests**:
  - Tests manual struct creation and validation
  - Tests byte/bit size merging and compatibility
  - Tests manual layout calculation without padding
  - Tests struct export to C header files
- **Validation Logic Tests**:
  - Tests struct definition validation
  - Tests member field validation
  - Tests layout consistency validation
  - Tests error handling and edge cases
- **Legacy Compatibility Tests**:
  - Tests length field to bit_size conversion
  - Tests backward compatibility with old data formats

### `test_struct_manual_integration.py` *(新增)*
Tests for manual struct definition integration functionality.
- Tests complete manual struct creation workflow
- Tests validation feedback and error handling
- Tests real-time remaining space calculation
- Tests struct export functionality
- Tests integration between manual and file-based struct loading

### `test_gui_input_validation.py`
Tests for GUI input validation and length limiting.
- Tests hex character validation
- Tests input length limiting
- Tests control key handling
- Tests auto-focus removal verification
- Tests input validation binding

### `test_struct_view.py` *(大幅擴充)*
Tests for GUI view functionality with TDD approach.
- Tests UI component initialization
- Tests presenter wiring
- Tests error message display
- Tests bitfield display in parsed values
- Tests struct layout display with bitfield info
- **Manual Struct Definition GUI Tests**:
  - Tests tab switching between file loading and manual definition
  - Tests dynamic member table functionality
  - Tests real-time remaining space display
  - Tests validation feedback in GUI
  - Tests export functionality triggers
- **TDD Tests for Remaining Space Display**:
  - Tests correct display of remaining bits/bytes
  - Tests dynamic updates when members are added/removed
  - Tests validation state display
  - Tests edge cases (empty struct, full struct, partial fill)

### `test_config_parser.py`
Tests for XML configuration parsing.
- Tests XML configuration file loading
- Tests configuration validation
- Tests test case extraction from XML

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
- ✅ **Bitfield 支援**: 完整的 bitfield 解析與處理
- ✅ **手動 struct 定義**: 手動建立與驗證 struct

## Bitfield 測試 (Bitfield Testing)

### 概述
專案新增完整的 bitfield 支援測試，涵蓋 C/C++ bitfield 語法的所有方面。

> **Note:** Manual struct mode does not support padding; all members are tightly packed. GUI tests are automatically skipped in headless environments.

### 測試範圍
- **Bitfield 解析**: 測試 `int a : 1;` 語法解析
- **Storage Unit 管理**: 測試 bitfield 在 storage unit 內的分配
- **Bit Offset 計算**: 測試 bitfield 在 storage unit 內的 bit offset
- **跨 Storage Unit**: 測試 bitfield 跨越 storage unit 邊界
- **混合成員**: 測試 bitfield 與普通成員混用的情況
- **資料提取**: 測試從 hex 資料中正確提取 bitfield 值

### 執行 Bitfield 測試
```bash
# 執行所有 bitfield 相關測試
python3 -m unittest tests.test_struct_model.TestStructModel.test_bitfield_* -v

# 執行特定 bitfield 測試
python3 -m unittest tests.test_struct_model.TestStructModel.test_bitfield_parsing -v
python3 -m unittest tests.test_struct_model.TestStructModel.test_bitfield_layout -v
python3 -m unittest tests.test_struct_model.TestStructModel.test_parse_hex_data_bitfields -v
```

### Bitfield 測試案例
- 單一 bitfield: `struct A { int a:1; int b:2; int c:5; };`
- 跨 byte bitfield: `struct B { char a:4; char b:4; char c:8; };`
- 不同型別斷開: `struct C { int a:3; char b:2; int c:5; };`
- 混合 bitfield 與一般欄位: `struct D { int a:1; int b; int c:2; };`

## 手動 Struct 定義測試 (Manual Struct Definition Testing)

### 概述
測試手動 struct 定義功能，包括 GUI 介面、驗證邏輯、匯出功能等。

> **Note:** Manual struct mode now fully supports C++-style alignment and padding. All members are automatically aligned and padded as in C++.

### 測試範圍
- **GUI 介面**: Tab 切換、成員表格、即時驗證
- **驗證邏輯**: 成員名稱唯一性、大小驗證、總大小一致性
- **Layout 計算**: 依 C++ 標準 struct align/padding 規則自動排列
- **匯出功能**: C header 檔案匯出
- **整合測試**: 完整的手動 struct 建立流程
- **C++ align/padding 驗證**: 測試手動 struct 產生的 layout 與 C++ 編譯器一致

### 執行手動 Struct 測試
```bash
# 執行所有手動 struct 相關測試
python3 -m unittest tests.test_struct_model.TestStructModel.test_manual_* -v
python3 -m unittest tests.test_struct_manual_integration -v

# 執行特定測試
python3 -m unittest tests.test_struct_model.TestStructModel.test_validate_manual_struct -v
python3 -m unittest tests.test_struct_model.TestStructModel.test_calculate_manual_layout -v
python3 -m unittest tests.test_struct_model.TestStructModel.test_export_manual_struct_to_h -v
```

### 手動 Struct 測試案例
- 基本手動 struct 建立與驗證
- 成員名稱重複錯誤處理
- 大小驗證錯誤處理
- 總大小不一致錯誤處理
- C header 檔案匯出格式驗證

## TDD 測試 (Test-Driven Development)

### 概述
專案採用 TDD 開發方法，所有新功能都先寫測試再實作。

### TDD 流程
1. **寫測試**: 先撰寫失敗的測試案例
2. **實作功能**: 實作最小可行功能讓測試通過
3. **重構**: 改善程式碼品質
4. **重複**: 持續迭代直到功能完成

### TDD 測試案例
- **剩餘空間顯示**: 測試 GUI 即時顯示剩餘可用空間
- **驗證回饋**: 測試驗證錯誤的即時顯示
- **動態更新**: 測試成員增刪時的動態更新
- **邊界情況**: 測試空 struct、滿 struct、部分填滿等情況

### 執行 TDD 測試
```bash
# 執行 TDD 相關測試
python3 -m unittest tests.test_struct_view.TestStructView.test_remaining_space_display -v
python3 -m unittest tests.test_struct_view.TestStructView.test_validation_feedback -v
```

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
python run_tests.py --test test_input_conversion
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

# Or use the cross-platform test runner (recommended)
python run_all_tests.py
```

### Run Specific Test Module
```bash
# From project root
python3 -m unittest tests.test_input_conversion -v
python3 -m unittest tests.test_string_parser -v
python3 -m unittest tests.test_struct_parsing -v
python3 -m unittest tests.test_struct_model_integration -v
python3 -m unittest tests.test_struct_parsing_core -v
python3 -m unittest tests.test_gui_input_validation -v
python3 -m unittest tests.test_struct_view -v
python3 -m unittest tests.test_struct_model -v
python3 -m unittest tests.test_struct_manual_integration -v

# Or use the test runner
python3 run_tests.py --test test_input_conversion
python3 run_tests.py --test test_string_parser
python3 run_tests.py --test test_struct_parsing
python3 run_tests.py --test test_struct_model_integration
python3 run_tests.py --test test_struct_parsing_core
python3 run_tests.py --test test_gui_input_validation
python3 run_tests.py --test test_struct_view
python3 run_tests.py --test test_struct_model
python3 run_tests.py --test test_struct_manual_integration
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
python3 -m unittest test_struct_parsing -v
python3 -m unittest test_struct_model_integration -v
python3 -m unittest test_struct_parsing_core -v
python3 -m unittest test_gui_input_validation -v
python3 -m unittest test_struct_view -v
python3 -m unittest test_struct_model -v
python3 -m unittest test_struct_manual_integration -v
```

## 測試結果統計

### 當前測試狀態
- **總測試數**: 131
- **通過**: 114
- **跳過**: 17 (GUI 測試在 headless 環境)
- **警告**: 3 (非關鍵配置問題)

### 測試分類
- **核心邏輯**: 所有測試通過
- **Bitfield 功能**: 完整覆蓋
- **手動 Struct 定義**: 完整驗證
- **GUI 介面**: 在 headless 環境中正確跳過

### 測試覆蓋範圍
- ✅ **Struct 解析**: 基本型別、bitfield、pointer
- ✅ **記憶體排列**: padding、alignment、bitfield packing
- ✅ **資料處理**: hex 轉換、endianness、bitfield 提取
- ✅ **手動定義**: GUI 介面、驗證、匯出
- ✅ **整合測試**: 端到端功能驗證
- ✅ **GUI 測試**: 介面行為 (適當的跳過處理)

## 測試最佳實踐

### 1. TDD 開發流程
- 先寫測試，再實作功能
- 確保測試失敗後再實作
- 持續重構改善程式碼品質

### 2. 測試分類
- **單元測試**: 測試個別函數/方法
- **整合測試**: 測試模組間互動
- **GUI 測試**: 測試使用者介面 (適當跳過)

### 3. 測試資料管理
- 使用 XML 配置檔案管理測試資料
- 支援自動化測試案例擴充
- 保持測試資料與程式碼同步

### 4. 跨平台測試
- 使用 `run_all_tests.py` 進行跨平台測試
- 分離 GUI 與非 GUI 測試
- 適當處理 headless 環境

## 未來測試規劃

### 1. 測試覆蓋率提升
- 增加更多邊界條件測試
- 擴充錯誤處理測試
- 新增效能測試

### 2. 自動化測試增強
- 整合 CI/CD pipeline
- 自動化 GUI 測試 (使用虛擬顯示)
- 測試報告自動化

### 3. 測試工具改進
- 測試資料生成工具
- 測試結果分析工具
- 測試覆蓋率報告工具 

## pytest 執行常見問題與解法

### 問題：zsh: command not found: pytest
- **原因**：未啟用正確的 Python 虛擬環境，或 PATH 未指向 .venv/bin。
- **解法**：
  1. 先啟用虛擬環境：
     ```sh
     source .venv/bin/activate
     ```
  2. 再執行 pytest：
     ```sh
     pytest tests/test_input_field_processor.py
     ```

### 問題：ModuleNotFoundError: No module named 'pytest'
- **原因**：虛擬環境內未安裝 pytest。
- **解法**：
  1. 啟用虛擬環境後安裝 pytest：
     ```sh
     pip install pytest
     ```

### 問題：找不到測試模組或 loader
- **原因**：PYTHONPATH 未正確設置，或 import 路徑錯誤。
- **解法**：
  - 確認 sys.path 有包含 src/ 及 tests/ 目錄。
  - 使用相對 import 或調整 sys.path。 