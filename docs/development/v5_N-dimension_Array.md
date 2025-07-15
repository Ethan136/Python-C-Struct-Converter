# v5 N-Dimension Array 支援 TDD 計畫

## 1. 目標
- 提升 `StructModel` 與 `LayoutCalculator` 能力，完整支援多維陣列 (N-D array) 的解析、佈局計算與資料還原。
- 以 TDD 方式漸進實作，確保新功能不破壞既有行為。

## 2. 現況
- `struct_parser.py` 已能解析 `arr[3][2]` 類型並回傳 `array_dims`，但後續流程僅當成單一元素處理。
- `LayoutCalculator._process_array_member` 目前僅放置 TODO，計算總大小時忽略陣列維度。
- `StructModel.parse_hex_data` 在解析時也無法拆解陣列元素。
- 測試僅驗證「陣列被視為單一元素」的暫時行為 (參見 `TestArrayMemberStubBehavior`)。

## 3. TDD 實作步驟
1. **新增失敗測試**：
   - 在 `tests/test_struct_parsing.py` 新增 `TestArrayParsing`，驗證 `parse_member_line_v2` 可解析多維陣列並取得正確 `array_dims`。
   - 在 `tests/test_struct_parsing.py` 或新檔案中新增 `TestArrayLayout`，期待 `calculate_layout` 對 `int arr[3][2]` 等產生正確 `size` 及 `offset`，總大小應為 element size × 維度乘積。
   - 在 `tests/test_struct_model.py` 新增 `TestParseHexDataArray`，輸入對應 hex 字串，驗證 `parse_hex_data` 會回傳各陣列元素值 (可使用 list 形式)。
   - 以上測試初期標記為 `@unittest.expectedFailure` 或先讓其失敗，確認現狀不足。
2. **實作功能**：
   - 完成 `LayoutCalculator._process_array_member`：
     1. 計算元素大小與 alignment。
     2. 根據維度乘積求得總大小。
     3. 產生對應 `LayoutItem`，並更新 `current_offset` 與 `max_alignment`。
   - 修改 `StructModel.parse_hex_data`：依照佈局中的陣列項目，按元素大小切片並還原多個值，組成 list 回傳。
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

