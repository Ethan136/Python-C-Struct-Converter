# v9 Parser TDD Detailed Plan

## 背景
- v9 目標是讓 `V7StructParser` 更完整，支援 **頂層 union**、`#pragma pack` 對齊設定，以及更健壯的 `_split_member_lines` 拆分。
- 目前解析器遇到這些情境時會返回 `None` 或拆分錯誤，無法解析 `examples/v5_features_example.h` 等複雜範例。
- 採用測試驅動開發（TDD）流程能逐步驗證功能並提供回歸防護。

## 建議
1. **分階段導入**：依序完成頂層 union、`pragma pack`、`_split_member_lines` 三項功能，確保每階段測試皆綠燈後再前進。
2. **測試命名一致**：所有新測試使用 `test_parse_*` 或 `test_split_*` 前綴，維持可讀性與追蹤性。
3. **重構優先**：每次實作後即進行重構，避免技術債堆積並維持解析器模組的清晰度。
4. **文件同步**：完成每階段後更新相應文件與範例，確保團隊成員了解最新功能。

## 實作步驟
- 透過 `tests/model/test_parser.py` 撰寫失敗測試（Red）→ 實作功能（Green）→ 重構（Refactor）。
- 測試期間可新增或修改 `examples/` 下的輸入檔以涵蓋各種情境。

### 1. 支援頂層 union
- **Red**：新增 `test_parse_top_level_union_returns_ast`，輸入僅含 `union` 的檔案。
- **Green**：重構 `parse_struct_definition` 為 `parse_aggregate_definition`，偵測 `union` 關鍵字並建立根節點。
- **Refactor**：整理共用流程，確保 `struct/union` 解析邏輯一致。

### 2. 支援 `#pragma pack`
- **Red**：新增 `test_parse_struct_with_pragma_pack_applies_alignment`，驗證 `pack` 值套用至 AST。
- **Green**：於 `_clean_content` 或新函式 `_handle_directives` 解析 `#pragma pack(push, n)` / `pop`，維護對齊堆疊。
- **Refactor**：將指令解析抽成 helper，方便未來擴充其他 `pragma`。

### 3. 強化 `_split_member_lines`
- **Red**：新增 `test_split_member_lines_handles_nested_union`，輸入含巢狀 `union`、註解與位元欄位。
- **Green**：以括號深度追蹤方式改寫 `_split_member_lines`，確保巢狀區塊在 `};` 前不被拆分。
- **Refactor**：抽出註解與續行符號處理邏輯，降低函式複雜度。

## 詳細實作
以下列出需調整的檔案與重點內容：

1. **`src/model/parser.py`**
   - `parse_struct_definition` → `parse_aggregate_definition`，支援頂層 `union`。
   - `_clean_content` / `_handle_directives`：解析並套用 `#pragma pack`。
   - `_split_member_lines`：改為括號深度追蹤與註解清理。
2. **`tests/model/test_parser.py`**
   - 新增上述三項測試案例並確保舊測試仍通過。
3. **`examples/` 測試資料**
   - 視需求新增 `union` 或 `pragma pack` 範例檔案。

## 測試腳本更新細節
- 使用 `python run_tests.py -t test_parser` 執行所有解析相關測試。
- 更新 `run_all_tests.py` 或 CI 設定，確保新測試被自動執行。

## 迭代提交建議
1. Commit 1：新增 `test_parse_top_level_union_returns_ast`（Red）。
2. Commit 2：實作 `parse_aggregate_definition` 支援頂層 `union`（Green）。
3. Commit 3：重構解析入口函式（Refactor）。
4. Commit 4：新增 `test_parse_struct_with_pragma_pack_applies_alignment`（Red）。
5. Commit 5：導入 `_handle_directives` 支援 `pragma pack`（Green）。
6. Commit 6：整理指令解析模組（Refactor）。
7. Commit 7：新增 `test_split_member_lines_handles_nested_union`（Red）。
8. Commit 8：改寫 `_split_member_lines`（Green）。
9. Commit 9：重構並更新文件（Refactor）。

## 開發時程
- **週 1**：完成頂層 `union` 支援與相關測試。
- **週 2**：實作 `#pragma pack` 解析並確認測試通過。
- **週 3**：改寫 `_split_member_lines` 並補齊所有測試。
- **週 4**：整合與回歸測試，更新文件後準備發佈。

---

本文件整理 v9 階段 Parser 的 TDD 詳細規劃，協助團隊以測試驅動方式完成頂層 `union`、`#pragma pack` 與 `_split_member_lines` 支援。
