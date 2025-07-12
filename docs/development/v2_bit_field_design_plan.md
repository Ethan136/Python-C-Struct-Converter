# Struct Bit Field (Bit Define) 支援設計規劃

## 目標
- 使 struct 解析、記憶體佈局、資料解析流程支援 C/C++ 的 bit field（如 `int a : 1;`）。

## 需修改/擴充之處

### 1. struct 解析
- `parse_struct_definition` 需能解析 `type name : bits;`，並記錄 bit 數。
- 解析結果需能區分一般欄位與 bit field 欄位。

### 2. 記憶體佈局計算
- `calculate_layout` 需依據 C/C++ bit field packing 規則計算 bit offset、storage unit。
- layout dict 需增加 `bit_offset`、`bit_size` 欄位。
- 需考慮 bit field 跨 byte、跨 storage unit、不同型別斷開等情境。

### 3. layout 資料結構
- 每個欄位 dict 增加 `is_bitfield`、`bit_offset`、`bit_size`。
- 例：
  ```python
  {
    "name": "a",
    "type": "int",
    "size": 4,           # storage unit 大小 (bytes)
    "offset": 0,         # storage unit 在 struct 內的 byte offset
    "is_bitfield": True,
    "bit_offset": 0,     # 在 storage unit 內的 bit offset
    "bit_size": 1
  }
  ```

### 4. hex 資料解析
- `parse_hex_data` 需能從 bytes 取出正確 bit 區段，並還原數值。
- 需考慮 endianness 及 bit field 跨 byte 情況。

### 5. 輸入欄位處理
- `input_field_processor` 需支援 bit 欄位的輸入驗證與 padding。
- 可能需新增 bit field 專用的處理函式。

### 6. Presenter/GUI
- 支援 bit 欄位的顯示、輸入、解析結果顯示。
- 需考慮 bit 欄位的輸入框設計與驗證。

### 7. 文件與測試
- 設計文檔補充 bit field 支援說明。
- 新增 bit field 解析的單元測試。

## 參考
- [docs/architecture/STRUCT_PARSING.md](../architecture/STRUCT_PARSING.md)
- [C++ 標準 bit field packing 規則](https://en.cppreference.com/w/cpp/language/bit_field) 

---

## 現有程式碼/測試檢查與 v2 bit field 支援規劃

### 1. 目前程式碼現況

#### 1.1 struct 解析
- `src/model/struct_model.py` 的 `parse_struct_definition` 目前僅支援 `type name;`，**不支援** `type name : bits;`。
- 解析結果（members）為 tuple，無法記錄 bit field 資訊。

#### 1.2 記憶體佈局計算
- `calculate_layout` 只考慮 byte 為單位的欄位與 padding，**未考慮 bit field packing**。
- layout dict 無 `bit_offset`、`bit_size`、`is_bitfield` 欄位。

#### 1.3 hex 資料解析
- `parse_hex_data` 只支援 byte 欄位，**無法正確解析 bit field**。

#### 1.4 輸入欄位處理
- `input_field_processor.py` 只支援 byte 欄位，**無 bit 欄位驗證/處理**。

#### 1.5 Presenter/GUI
- `struct_presenter.py`、`struct_view.py` 只支援 byte 欄位，**無 bit 欄位顯示/輸入/驗證**。

#### 1.6 文件
- 目前設計文檔、分析文檔、README 皆**未提及 bit field 支援**。

---

### 2. 目前測試現況

- `tests/test_struct_model.py`、`tests/test_struct_parsing_core.py`、`tests/test_input_conversion.py` 皆**無 bit field 相關測試**。
- 測試 XML (`tests/data/struct_parsing_test_config.xml`) 也**無 bit field struct 測試案例**。
- 目前測試僅涵蓋 char/int/long long/padding/空值/endianness/mixed size，**未涵蓋 bit field**。

---

### 3. v2 bit field 支援需修改/新增的程式碼與測試

#### 3.1 程式碼需修改/新增處
- `src/model/struct_model.py`
  - `parse_struct_definition`：支援 `type name : bits;`，解析出 bit 數，members 結構需能記錄 bit 欄位。
  - `calculate_layout`：依 C/C++ packing 規則計算 bit offset、storage unit，layout dict 增加 `is_bitfield`、`bit_offset`、`bit_size`。
  - `parse_hex_data`：能從 bytes 取出正確 bit 區段，還原 bit field 數值。
- `src/model/input_field_processor.py`
  - 增加 bit 欄位的輸入驗證、padding、轉換處理。
- `src/presenter/struct_presenter.py`、`src/view/struct_view.py`
  - 支援 bit 欄位的顯示、輸入、驗證、解析結果顯示。
- 其他：如有 struct layout 顯示、debug 輸出等，也需支援 bit 欄位資訊。

#### 3.2 測試需新增/調整內容
- `tests/test_struct_model.py`、`tests/test_struct_parsing_core.py`
  - 新增 bit field struct 解析、layout、hex 解析的單元測試。
  - 測試 bit field packing、跨 byte、不同型別斷開、endianness 等情境。
- `tests/data/struct_parsing_test_config.xml`
  - 新增 bit field struct 測試案例（如 `struct A { int a:1; int b:2; int c:6; };`），並設計對應的 input/expected result。
- `tests/test_input_conversion.py`
  - 新增 bit 欄位的輸入驗證、padding、轉換測試。

#### 3.3 文件需同步調整
- `docs/architecture/STRUCT_PARSING.md`：補充 bit field 解析、layout、資料結構說明。
- `src/model/README.md`：補充 bit field 支援說明。
- `docs/analysis/input_field_processor_analysis.md`：補充 bit 欄位處理設計。
- `tests/README.md`：補充 bit field 測試說明與範例。
- 本文件（`v2_bit_field_design_plan.md`）：持續更新規劃與進度。

---

### 4. 建議測試案例（可直接納入 XML 或 unittest）

- 單一 bit field struct：`struct A { int a:1; int b:2; int c:5; };`
- 跨 byte bit field：`struct B { char a:4; char b:4; char c:8; };`
- 不同型別斷開：`struct C { int a:3; char b:2; int c:5; };`
- 混合 bit field 與一般欄位：`struct D { int a:1; int b; int c:2; };`
- 測試 little/big endian 下 bit field 解析結果。 