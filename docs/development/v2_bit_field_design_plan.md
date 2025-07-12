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

---

## 2024/07/07 進度與實作說明

### 已完成項目

#### 1. struct 解析
- `parse_struct_definition` 已支援 `type name : bits;` 語法，能正確解析 bit field 欄位，並以 dict 格式記錄 type、name、is_bitfield、bit_size。
- 單元測試：`test_struct_with_bitfields` 驗證 bit 欄位解析正確。

#### 2. 記憶體佈局計算
- `calculate_layout` 已依據 C/C++ bit field packing 規則，計算 bit offset、storage unit，並於 layout dict 增加 `is_bitfield`、`bit_offset`、`bit_size` 欄位。
- 支援同一 storage unit 連續 bit field、自動斷開不同型別或超過 storage unit 大小時換新單元。
- 單元測試：`test_bitfield_layout` 驗證 bit 欄位 layout 正確（offset、bit_offset、bit_size）。

#### 3. hex 資料解析
- `parse_hex_data` 已能根據 layout，從 bytes 取出正確 bit 區段，還原 bit field 數值，並考慮 endianness。
- 單元測試：`test_parse_hex_data_bitfields` 驗證 bit 欄位值解析正確，並以 little endian 測試 C 語言 bitfield 實際行為。

#### 4. TDD 流程
- 每個功能皆先撰寫/調整對應單元測試，確保測試失敗後再實作，並於實作後測試通過。
- 目前所有 bit field 相關測試皆已通過。

#### 5. 尚未實作/待辦
- `input_field_processor.py` 尚未支援 bit 欄位專用輸入驗證/轉換。
- GUI（Presenter/View）尚未支援 bit 欄位顯示、輸入、驗證。
- 測試 XML、其他跨 byte/型別/混合欄位案例、文件補充等。

#### 6. 主要修改檔案
- `src/model/struct_model.py`：三大核心 function 均已支援 bit field。
- `tests/test_struct_model.py`：新增/擴充 bit field 解析、layout、hex 解析單元測試。

--- 

## 2024/07/07 View/GUI 層 bit field 支援現況與待辦

### 現況分析
- 目前 `src/view/struct_view.py` 的 `show_parsed_values`、`show_struct_member_debug` 僅以通用欄位格式顯示 struct 解析結果，未針對 bit field 欄位做特殊顯示。
- GUI 解析結果區（Parsed Values）與 Debug 區，僅顯示欄位名稱、值、hex，無法辨識哪些欄位為 bit field，也未顯示 bit offset/bit size 等資訊。
- struct layout 顯示（show_struct_layout）同樣未顯示 bit 欄位的 bit offset/bit size/is_bitfield 屬性。
- 目前 GUI 輸入區（hex grid）僅支援以 byte 為單位的欄位，無法針對 bit 欄位提供更細緻的輸入框或提示。

### 待辦與建議修改
- [ ] **struct layout 顯示**：於 struct layout 區塊，若欄位為 bit field，應額外顯示 `bit_offset`、`bit_size`、`is_bitfield`。
- [ ] **解析結果顯示**：於解析結果區，bit 欄位應有明顯標示（如加註 [bitfield]、顯示 bit offset/size），以利辨識。
- [ ] **Debug 區**：struct member debug info 應顯示 bit 欄位的 storage unit、bit offset、bit size。
- [ ] **GUI 輸入區**：未來可考慮針對 bit 欄位提供更細緻的輸入驗證或提示（目前僅支援 byte 為單位）。
- [ ] **View 文件**：`src/view/README.md` 應補充 bit field 顯示支援現況與設計。

### 目前尚未支援/需修改的檔案
- `src/view/struct_view.py`（顯示/標示 bit 欄位資訊）
- `src/view/README.md`（文件補充）

--- 

## [2024-07-09] GUI struct layout 顯示錯誤排查紀錄

### 問題現象
- 以 `examples/example.h` 的 struct 作為輸入，GUI 顯示 struct layout 時：
    - 欄位順序錯誤（bitfield 欄位全部排在最前面，與原始 struct 不符）
    - offset/size 計算錯誤
    - 部分欄位（如 e, f, g）完全沒顯示
    - bitfield 只顯示 c1, c2, c3，其他欄位缺失

### 主要原因
- `parse_struct_definition` 目前是：
    1. 先用 regex 抓所有 bitfield 欄位，依序加入 members
    2. 再抓所有普通欄位，跳過已經 match 過的 bitfield
    3. 這會導致 bitfield 欄位永遠排在最前面，欄位順序與原始 struct 不符
    4. 若 struct 欄位有交錯（bitfield 與普通欄位混用），順序就會錯誤
    5. 若 regex 沒有 match 到所有欄位，會造成欄位遺失

### code 檢查重點
- `parse_struct_definition` 需改為：
    - 依照原始 struct 內容逐行解析
    - 每一行判斷是 bitfield 還是普通欄位，依序加入 members
    - 這樣才能保證欄位順序正確，bitfield 與普通欄位混用時也不會出錯

### 待修正事項
- [ ] 重構 `parse_struct_definition`，改為逐行解析、順序保留
- [ ] 增加單元測試，驗證 bitfield 與普通欄位混用時順序正確
- [ ] 驗證 GUI layout 顯示與 C++ 編譯器一致 

### 資料結構範例

- layout 內每個欄位 dict 格式：
  ```python
  {
    "name": "欄位名稱",
    "type": "型別",
    "size": 4,           # 占用 bytes 數
    "offset": 0,         # 在 struct 內的 byte offset
    "is_bitfield": True, # 是否為 bitfield 欄位 (optional)
    "bit_offset": 0,     # 若為 bitfield，於 storage unit 內的 bit offset (optional)
    "bit_size": 1        # 若為 bitfield，bitfield 欄位寬度 (optional)
  }
  ```
- members list 範例：
  ```python
  [
    ("char", "a"),
    ("int", "b"),
    {"type": "int", "name": "c1", "is_bitfield": True, "bit_size": 1},
    ...
  ]
  ```

### 支援限制
- 目前不支援 union、enum、typedef、nested struct、#pragma pack、__attribute__ 等 C/C++ 語法。
- 只支援單一 struct 解析，不支援多 struct 同時解析。
- bitfield 只支援 int/unsigned int/char/unsigned char 等基本型別，不支援 pointer bitfield。

### 測試覆蓋清單
- 基本型別 struct
- bitfield struct（連續/跨 storage unit）
- padding/alignment struct
- pointer struct
- 混合欄位 struct
- 複雜 struct（如 example.h 的 CombinedExample）
- hex 資料解析（含 bitfield、padding、pointer） 