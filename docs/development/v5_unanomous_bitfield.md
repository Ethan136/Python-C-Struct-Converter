# v5 Anonymous Bitfield 支援 TDD 規劃

## 目標
- 讓解析器與 layout 計算支援匿名 bit field (`int : 3;`)，可用於保留位元或對齊。
- 維持現有 bitfield 行為，並使匯出與 GUI 顯示能處理 `name=None` 的欄位。
- 全程遵循 TDD 流程：撰寫失敗測試 → 實作 → 重構。

## 現況檢查
1. `MemberDef.name` 及 `LayoutItem.name` 已為 `Optional[str]`【F:src/model/struct_parser.py†L10-L23】【F:src/model/layout.py†L25-L40】，預留匿名欄位可能性。
2. `_parse_bitfield_declaration` 的 regex 已改為 `r"(.+?)\s+(?:([\w\[\]]+)\s*)?:\s*(\d+)$"`，名稱為可選【F:src/model/struct_parser.py†L50-L72】。
3. `parse_member_line_v2` 會將取得的名稱直接傳入 `MemberDef`，因此能回傳 `name=None` 的物件【F:src/model/struct_parser.py†L101-L117】。
4. `LayoutCalculator._add_bitfield_to_layout` 現已接受 `name=None`，並直接寫入 layout【F:src/model/layout.py†L292-L308】。
5. `parse_hex_data` 在組合結果時使用 `item['name']`，若值為 `None` 仍能正常處理【F:src/model/struct_model.py†L93-L138】。
6. `tests/test_struct_parser_utils.py` 中已包含解析匿名 bitfield 的測試並正常通過【F:tests/test_struct_parser_utils.py†L20-L26】。
7. `export_manual_struct_to_h` 在遇到 `name=None` 時仍會輸出 `None` 字串，需改成省略名稱【F:src/model/struct_model.py†L267-L283】。

## TDD 實作步驟
以下流程每一步皆遵循 **Red → Green → Refactor**：先撰寫或啟用測試，確認失敗後再實作使其通過。

### 1. Parser 支援
本功能已完成實作並具備測試：
1. `tests/test_struct_parser_utils.py` 的 `test_anonymous_bitfield_member` 驗證 `parse_member_line` 可處理匿名 bitfield【F:tests/test_struct_parser_utils.py†L20-L26】。
2. `tests/test_struct_parser_v2.py` 包含 `test_parse_anonymous_bitfield_v2` 與 `test_struct_with_anonymous_bitfield`，確認新版 parser 也能解析【F:tests/test_struct_parser_v2.py†L44-L49】【F:tests/test_struct_parser_v2.py†L196-L209】。
因此不需再啟用 `xfail` 或新增額外測試，僅需維護既有測試通過。

### 2. Layout 計算
對應測試 `test_anonymous_bitfield_layout` 已於 `tests/test_struct_model.py` 實作並通過【F:tests/test_struct_model.py†L322-L336】。
現行 `LayoutCalculator` 支援 `name=None`，僅需維護其正確性。

### 3. Hex 資料解析
`tests/test_struct_model.py` 中的 `test_parse_hex_data_with_anonymous_bitfield` 驗證 `StructModel.parse_hex_data` 能處理 `name=None` 的欄位【F:tests/test_struct_model.py†L650-L669】。

### 4. GUI 與文件
1. **GUI 測試**：若 GUI 需顯示匿名 bitfield，可在 `tests/test_struct_view.py` 內新增對應顯示測試，先使用 `@unittest.expectedFailure`。
2. **文件更新**：更新 `STRUCT_PARSING.md` 以及 `README.md` 的功能列表，說明支援匿名 bit field。
3. **匯出功能**：新增 `test_export_manual_struct_to_h_anonymous_bitfield` 測試，確保 `export_manual_struct_to_h` 省略名稱時輸出正確【F:tests/test_struct_model.py†L961-L973】。

### 5. 迭代與驗證
- 每完成一項功能立即執行 `run_all_tests.py`，確保所有既有與新測試皆通過。
- 如發現 Parser、Layout、Hex 解析有互相影響，應回到對應單元測試補強再重構。

## 後續擴充方向
- 目前僅支援 `int`/`unsigned int`/`char` 等基本型別之匿名 bitfield；若要支援其他型別或複合結構，需再擴充驗證與 layout 規則。
- GUI 目前僅以文字呈現，如需進一步編輯或輸入匿名 bitfield，可新增相應欄位類型與驗證邏輯。

