# v5 N-Dimension Array 支援 TDD 計畫

## 1. 目標
- 提升 `StructModel` 與 `LayoutCalculator` 能力，完整支援多維陣列 (N-D array) 的解析、佈局計算與資料還原。
- 以 TDD 方式漸進實作，確保新功能不破壞既有行為。

## 2. 現況
- `struct_parser.py` (約 33 行以後) 透過 `_extract_array_dims` 解析 `arr[3][2]` 等標記並存入 `MemberDef.array_dims`，但後續流程仍僅視為單一元素。
- `LayoutCalculator._process_array_member` (116 行附近) 目前僅建立單一 `LayoutItem`，沒有乘上維度數，仍為 TODO。
- `StructModel.parse_hex_data` 處理 layout 時忽略 `array_dims`，無法將陣列數值展開。
- 現有測試僅驗證「陣列被視為單一元素」的暫時行為，參考 `TestArrayMemberStubBehavior`。

## 3. TDD 實作步驟
1. **新增失敗測試**：
   - 在 `tests/test_struct_parsing.py` 新增 `TestArrayParsing`，以 `parse_member_line_v2` 解析 `int arr[3][2];`，預期回傳 `MemberDef(array_dims=[3, 2])`。
   - 在相同檔案或新檔案加入 `TestArrayLayout`，利用 `LayoutCalculator.calculate` 處理 `[{"type": "int", "name": "arr", "array_dims": [3,2]}]`，期望 layout 產生 `size == 24`、`offset == 0`。
   - 在 `tests/test_struct_model.py` 增加 `TestParseHexDataArray`，給定長度 24 的 hex 字串，`StructModel.parse_hex_data` 應得到 `[v00, v01, ...]` 形式的 list。
   - 新增測試時先以 `@unittest.expectedFailure` 標註，確保現行程式會失敗，之後再移除標記使其通過。
2. **實作功能**：
   - 完成 `LayoutCalculator._process_array_member`：
     1. 使用 `_get_type_size_and_align` 取得元素的 `size` 與 `alignment`，此方法目前定義於 `layout.py` 第 110 行左右。
     2. 計算 `total_elems = math.prod(array_dims)`，將元素大小乘上此乘積得到陣列總大小。
     3. 呼叫 `_add_padding_if_needed(alignment)` 將 `current_offset` 對齊後，再透過 `_add_member_to_layout` 建立 `LayoutItem`，其中應寫入 `array_dims` 供後續解析使用。
     4. 處理完畢後更新 `current_offset += total_size`，同時比較並更新 `max_alignment`。
   - 修改 `StructModel.parse_hex_data`：在逐一處理 layout 時，若 `item` 具有 `array_dims`，應以 `size // total_elems` 取得單一元素大小，並依序切片還原所有元素值，組成 list 儲存於回傳結果。
3. **重構與驗證**：
   - 重構重複邏輯（若有），確保程式碼可讀性與擴充性。
   - 移除 `expectedFailure` 標記，確認所有新測試通過。

## 4. 新增/調整的測試檔案
- `tests/data/` 新增 array 相關的 XML 測試案例，可擴充現有 loader。
- `tests/test_struct_parsing.py`：加入解析與佈局計算的單元測試。
- `tests/test_struct_model.py`：加入 `parse_hex_data` 對陣列輸出的驗證。

## 5. 文件與範例更新
- `README.md`、`docs/architecture/STRUCT_PARSING.md` 補充陣列支援說明與範例。
- `examples/example.h` 可加入含陣列的 struct 供測試與教學。

## 6. 待辦
- 手動 struct 定義頁面 (`StructView` 與 `StructPresenter`) 尚未處理陣列輸入，未來視需求擴充 GUI 邏輯與對應測試。
- 後續如要支援陣列內含 bitfield 或巢狀結構，需再擴充 `LayoutCalculator` 與解析流程。

## 7. 影響模組與修改項目
1. **`src/model/layout.py`**
   - `LayoutItem` dataclass (約在第 28 行) 新增 `array_dims: List[int]` 欄位，預設為 `[]`，以便在 layout 中保留維度資訊。
   - `_process_array_member` 應位於 115 行左右，實作時需：
       1. 透過 `_get_type_size_and_align` 取得元素資訊。
       2. 對 `alignment` 呼叫 `_add_padding_if_needed`。
       3. 使用 `_add_member_to_layout(name, mtype, total_size)` 生成項目，並於 `LayoutItem` 寫入 `array_dims`。
       4. 更新 `current_offset` 及 `max_alignment`。
   - `_process_regular_member` (160 行附近) 檢查 `array_dims` 後，轉由 `_process_array_member` 處理。
2. **`src/model/struct_model.py`**
   - `parse_hex_data` (約在第 60 行) 迭代 `self.layout` 時，若項目具有 `array_dims`，需：
       1. 依 `array_dims` 計算元素數量 `n`，再以 `item['size'] // n` 計算單一元素大小。
       2. 從 `data_bytes` 依序切片 `n` 次，使用 `int.from_bytes` 將每段 bytes 轉為數值。
       3. 將所得 list 以 `{"name": name, "value": values, "hex_raw": raw_hex}` 形式加入 `parsed_values`。
3. **`src/model/struct_parser.py`**
   - 現有 `_extract_array_dims` 與 `parse_member_line_v2` 已支援多維陣列，新增測試強化覆蓋率。
4. **XML Loader 與測試資料**
   - `tests/data/` 需新增 `test_struct_with_array.h` 與對應的 `struct_parsing_test_config.xml` 節點。XML 格式參考現有檔案，於 `<expected_results>` 下為每個 endianness 列出陣列元素的 `expected_value` 與 `expected_hex`，方便自動比對。

## 8. 新增測試清單
- `tests/test_struct_parsing.py::TestArrayParsing`：驗證解析階段能正確取得 `array_dims`。
- `tests/test_struct_parsing.py::TestArrayLayout`：確認 `_process_array_member` 依維度計算 size、offset、alignment。
- `tests/test_struct_model.py::TestParseHexDataArray`：`StructModel.parse_hex_data` 應回傳元素 list，並比對 hex 值。
- XML 驅動案例：於 `tests/data/struct_parsing_test_config.xml` 新增陣列測試節點，透過既有 loader 執行。

## 9. 後續擴充方向
- 陣列元素若為 nested struct 或 bitfield，需再擴充遞迴處理與 bitfield packing。
- GUI 手動輸入陣列值與驗證邏輯仍待規劃。

