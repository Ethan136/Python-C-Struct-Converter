# v9 Parser Enhancement Plan

## 背景
- 目前 `V7StructParser` 僅針對以 `struct` 開頭的內容進行解析，遇到 `#pragma pack` 等前置處理指令會提前返回 `None`。
- `_split_member_lines` 在處理多行 `union` 或包含註解的成員時容易將 `union` 切成多段，導致成員解析失敗。
- 無法解析獨立宣告的頂層 `union`，GUI 介面載入 `examples/v5_features_example.h` 時因為 `#pragma pack` 而完全失敗。

## 建議
1. **支援頂層 `union` 解析**：偵測 `union` 關鍵字並透過 `ASTNodeFactory.create_union_node` 建立根節點。
2. **支援前處理 `#pragma` 指令**：能識別並正確處理 `#pragma pack` 等指令，保留對齊設定並確保解析流程不中斷。
3. **改進 `_split_member_lines`**：在遇到巢狀 `struct/union` 時維持完整區塊，避免錯誤拆分。
4. **新增測試案例**：針對上述三點建立單元測試，確保解析器可正確處理。

## 實作步驟
- 重構 `parse_struct_definition`，讓其能同時處理 `struct` 與 `union`。
- 新增 `_handle_directives()` 或於 `_clean_content` 解析 `#pragma` 行，保存 pack 等資訊後再以 `re.search` 找到第一個聚合型別。
- 更新 `_split_member_lines` 判斷邏輯，當偵測到 `union`/`struct` 起始符號 `{` 時累計括號深度，直到對應 `};` 才視為單一成員。
- 在 `tests/model` 下新增：
  - 解析含 `#pragma pack` 的 `struct` 測試。
  - 頂層 `union` 宣告測試。
  - 多行 `union` 或含註解、位元欄位的成員拆分測試。

## 詳細實作
以下列出需調整的檔案與重點內容：
1. **`src/model/parser.py`**
   - `parse_struct_definition` → 改名為 `parse_aggregate_definition` 或內部判斷 `struct/union`。
   - 新增 `_handle_directives()` 於 `_clean_content`，解析並保留 `#pragma` 對齊資訊。
   - `_split_member_lines` → 追蹤括號深度，遇到 `union`/`struct` 直到 `};` 才切分。
2. **`tests/model/test_parser.py`** *(新增/更新)*
   - `test_parse_struct_with_pragma_pack()`：驗證帶有 `#pragma pack` 的檔案可解析。
   - `test_parse_top_level_union()`：驗證頂層 `union` 能建立 AST。
   - `test_split_member_lines_with_union()`：確保多行 `union` 被視為單一成員。
3. **`examples/v5_features_example.h`** *(若必要)*
   - 可新增頂層 `union` 範例或註解說明以輔助測試。

## 需要改動的函式
- `V7StructParser.parse_struct_definition` *(或新 `parse_aggregate_definition`)*
- `V7StructParser._clean_content`
- `V7StructParser._split_member_lines`

## 測試腳本更新細節
- 於 `run_tests.py` 加入新測試路徑，或確保 `pytest` 自動搜尋。
- 測試 `examples/v5_features_example.h`：
  - `#pragma pack` 指令應被解析並套用對齊設定，`struct` 仍能解析。
  - 含有頂層 `union` 時 GUI 亦能載入。
  - 確認 `_split_member_lines` 對含註解、多行或位元欄位的 `union` 可維持完整性。

---

本文件提出 v9 階段對 Parser 的增強計畫，目標是完整支援 `top level union`、`pragma pack` 及更健壯的 `_split_member_lines` 邏輯，以便在未來 GUI 與 CLI 操作中正確解析更多 C 語言結構。
