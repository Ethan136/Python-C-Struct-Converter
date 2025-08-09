# v9 Parser TDD Plan

## 背景
- 目標是在 v9 階段讓 `V7StructParser` 能完整支援 **頂層 union**、`#pragma pack` 對齊設定與更加穩健的 `_split_member_lines`。
- 採用測試驅動開發（TDD）流程，先撰寫失敗測試再實作，確保功能覆蓋與回歸防護。

## 開發範圍
1. **頂層 union 解析**：輸入檔案僅含 `union` 定義時仍能建立 AST。
2. **`#pragma pack` 支援**：解析對齊指令並套用到後續聚合型別。
3. **`_split_member_lines` 強化**：巢狀 `union/struct`、位元欄位與註解皆能正確切分。

## TDD 流程概述
- 每項功能皆遵循 Red → Green → Refactor 迭代。
- 測試集中於 `tests/model/test_parser.py`，必要時補充 `examples/` 測試資料。
- 每次 commit 先新增失敗測試，再實作使之通過，最後重構確保程式碼品質。

## 開發步驟
### 1. 頂層 union 支援
- **Red**：新增 `test_parse_top_level_union_returns_ast`，驗證僅含 `union` 的檔案可建立根節點。
- **Green**：重構 `parse_struct_definition` → `parse_aggregate_definition`，偵測 `union` 關鍵字並透過 `ASTNodeFactory.create_union_node` 建立節點。
- **Refactor**：整理共用流程，確保 `struct/union` 解析邏輯一致。

### 2. `#pragma pack` 指令
- **Red**：新增 `test_parse_struct_with_pragma_pack_applies_alignment`，驗證 `pack` 值被記錄於 AST。
- **Green**：在 `_clean_content` 或新函式 `_handle_directives` 中解析 `#pragma pack(push, n)` / `pop`，維護對齊堆疊並套用到節點。
- **Refactor**：將指令解析抽成獨立 helper，便於未來擴充其他 pragma。

### 3. `_split_member_lines` 改寫
- **Red**：新增 `test_split_member_lines_handles_nested_union`，輸入含多行 `union`、註解與位元欄位。
- **Green**：以括號深度追蹤方式重寫 `_split_member_lines`，確保巢狀區塊在 `};` 前不被拆分。
- **Refactor**：抽出處理註解與續行符號的子函式，降低複雜度。

### 4. 整合與回歸
- 全面執行 `python run_tests.py` 或 `python run_tests.py -t test_parser`，確認所有新舊測試皆通過。
- 檢視覆蓋率與錯誤訊息，必要時補齊測試或修正文件。

## 需調整的檔案
- `src/model/parser.py`
- `tests/model/test_parser.py`
- `examples/` 內對應測試資料（視需求新增或更新）

## 測試腳本更新
- 確保 `run_tests.py` 能自動載入新增的測試案例。
- 於 CI 或開發流程中執行 `python run_tests.py -t test_parser` 作為基本驗證。

## 迭代提交建議
1. **Commit 1**：新增 `test_parse_top_level_union_returns_ast`（Red）。
2. **Commit 2**：實作 `parse_aggregate_definition` 支援 union（Green）。
3. **Commit 3**：重構 parser 共用邏輯（Refactor）。
4. **Commit 4**：新增 `test_parse_struct_with_pragma_pack_applies_alignment`（Red）。
5. **Commit 5**：導入 `_handle_directives` 支援 `#pragma pack`（Green）。
6. **Commit 6**：整理指令解析模組（Refactor）。
7. **Commit 7**：新增 `test_split_member_lines_handles_nested_union`（Red）。
8. **Commit 8**：改寫 `_split_member_lines`（Green）。
9. **Commit 9**：重構與文件更新（Refactor）。

## 開發時程
- **週 1**：完成頂層 union 支援。
- **週 2**：實作與驗證 `#pragma pack`。
- **週 3**：強化 `_split_member_lines`。
- **週 4**：整合與回歸測試，準備提交。

## 注意事項
- `#pragma pack` 僅影響其後宣告，需處理巢狀聚合型別的繼承與還原。
- `_split_member_lines` 改寫後需評估效能，避免在大型檔案造成顯著延遲。
- 任何新增測試資料應同步更新 `examples/` 文件，以利後續維護。

---

本文件提供在 v9 階段以 TDD 推動 Parser 支援頂層 union、`#pragma pack` 與更穩健 `_split_member_lines` 的具體規劃，並附上迭代步驟與時程供開發參考。
