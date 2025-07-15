# v5 Anonymous Bitfield 支援 TDD 規劃

## 目標
- 讓解析器與 layout 計算支援匿名 bit field (`int : 3;`)，可用於保留位元或對齊。
- 維持現有 bitfield 行為，並使匯出與 GUI 顯示能處理 `name=None` 的欄位。
- 全程遵循 TDD 流程：撰寫失敗測試 → 實作 → 重構。

## 現況檢查
1. `MemberDef.name` 及 `LayoutItem.name` 已為 `Optional[str]`【F:src/model/struct_parser.py†L10-L23】【F:src/model/layout.py†L25-L40】，預留匿名欄位可能性。
2. `_parse_bitfield_declaration` 的 regex `r"(.+?)\s+([\w\[\]]+)\s*:\s*(\d+)$"` 限制必須有名稱【F:src/model/struct_parser.py†L50-L66】。
3. `parse_member_line_v2` 依賴上述函式，若解析失敗則回傳 `None`，因此匿名 bitfield 現階段被忽略。
4. `LayoutCalculator._add_bitfield_to_layout` 已註解日後可接受 `name=None`【F:src/model/layout.py†L287-L301】。
5. `parse_hex_data` 在組合結果時直接使用 `item['name']`，若值為 `None` 仍可處理，但 GUI 尚未顯示此狀態【F:src/model/struct_model.py†L93-L138】。
6. 測試檔 `tests/test_struct_parser_utils.py` 已對匿名 bitfield 標示 `xfail`【F:tests/test_struct_parser_utils.py†L19-L23】，代表功能未實作。

## TDD 實作步驟
以下流程每一步皆遵循 **Red → Green → Refactor**：先撰寫或啟用測試，確認失敗後再實作使其通過。

### 1. Parser 支援
1. **啟用測試**：移除 `pytest.mark.xfail` 標註，讓 `TestParseMemberLine.test_anonymous_bitfield_member` 變成正式失敗測試。
2. **新增測試**：在 `tests/test_struct_parser_v2.py` 中加入：
   - `test_parse_anonymous_bitfield_v2`：確認 `parse_member_line_v2('int : 5')` 回傳 `MemberDef(type='int', name=None, is_bitfield=True, bit_size=5)`。
   - `test_struct_with_anonymous_bitfield`：以 `parse_struct_definition_ast` 解析含匿名 bitfield 的 struct，驗證 members 序列包含 `name is None` 之項目。
3. **實作**：
   - 修改 `_parse_bitfield_declaration` 允許名稱省略，regex 可改為 `r"(.+?)\s+(?:([\w\[\]]+)\s*)?:\s*(\d+)$"`，捕捉 `name` 群組為可選；若未匹配則設為 `None`。
   - `parse_member_line_v2` 需在建立 `MemberDef` 時接受 `name=None`。
4. **重構**：確認一般 bitfield 行為不受影響，並適度整理重複程式碼。

### 2. Layout 計算
1. **新增測試**：於 `tests/test_struct_model.py` 新增 `test_anonymous_bitfield_layout`：
   ```python
   members = [
       {"type": "int", "name": "a", "is_bitfield": True, "bit_size": 3},
       {"type": "int", "name": None, "is_bitfield": True, "bit_size": 5},
       {"type": "int", "name": "b", "is_bitfield": True, "bit_size": 4},
   ]
   layout, total, align = calculate_layout(members)
   ```
   預期三者共用同一 storage unit，`layout[1].name is None` 且 `bit_offset` 正確為 3。
2. **實作**：`LayoutCalculator` 目前已支援 `name=None` 的加入，僅需確保 `parse_member_line_v2` 產生的資料格式正確即可。

### 3. Hex 資料解析
1. **新增測試**：在 `tests/test_struct_model.py` 或整合測試檔新增 `test_parse_hex_data_with_anonymous_bitfield`，輸入對應 hex 並驗證回傳 list 仍包含 `{"name": None, "value": "..."}`。
2. **實作**：`StructModel.parse_hex_data` 已能處理 `name=None`，但為清晰起見，可在結果中將 `None` 名稱轉為 `"(anon bitfield)"` 或保持 `None`，視 GUI 需求調整。

### 4. GUI 與文件
1. **GUI 測試**：若 GUI 需顯示匿名 bitfield，可在 `tests/test_struct_view.py` 內新增對應顯示測試，先使用 `@unittest.expectedFailure`。
2. **文件更新**：更新 `STRUCT_PARSING.md` 以及 `README.md` 的功能列表，說明支援匿名 bit field。

### 5. 迭代與驗證
- 每完成一項功能立即執行 `run_all_tests.py`，確保所有既有與新測試皆通過。
- 如發現 Parser、Layout、Hex 解析有互相影響，應回到對應單元測試補強再重構。

## 後續擴充方向
- 目前僅支援 `int`/`unsigned int`/`char` 等基本型別之匿名 bitfield；若要支援其他型別或複合結構，需再擴充驗證與 layout 規則。
- GUI 目前僅以文字呈現，如需進一步編輯或輸入匿名 bitfield，可新增相應欄位類型與驗證邏輯。

