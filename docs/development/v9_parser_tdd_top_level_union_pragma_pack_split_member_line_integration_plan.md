# v9 Parser Top-Level Union / Pragma Pack / `_split_member_lines` Integration Plan

## 背景
- 先前的 TDD 規劃與後續補強已建立頂層 `union`、`#pragma pack` 與 `_split_member_lines` 的基礎功能。
- 為確保釋出品質，需要統整各項改動並確認解析器在整合情境下運作正常。
- 此文件提供最終整合階段的建議與測試計畫，延續 v8 文件的結構與描述方式。

## 建議
1. **統一路徑**：將 `struct` 與 `union` 解析流程整合在 `parse_aggregate_definition`，減少重複邏輯。
2. **完整對齊堆疊**：`#pragma pack` 需支援巢狀 `push/pop`，並確保離開區塊後還原預設值。
3. **拆分函式模組化**： `_split_member_lines` 分離註解處理與括號追蹤，方便獨立測試與維護。
4. **回歸測試**：新增跨功能整合測試，確保三者組合下仍能產生正確 AST。

## 實作步驟
- 以 Red → Green → Refactor 為迭代模式，每次提交先撰寫失敗測試再實作。
- 完成核心功能後執行 `python run_tests.py -t test_parser` 驗證解析器案例；最終以 `--all` 進行回歸。
- 文件與示例於每次迭代同步更新，避免遺漏。

## 詳細實作
1. **`src/model/parser.py`**
   - 重構 `parse_aggregate_definition`，讓頂層 `struct/union` 共用流程並記錄 `pack` 值。
   - 抽出 `_parse_pragma_pack` 處理對齊堆疊，並在結束區塊時還原。
   - 改寫 `_split_member_lines`：
     - `strip_comments(line)` 移除註解。
     - `track_brace_depth(line)` 追蹤 `{`/`}` 深度。
     - 於深度回到 0 時才切分成員。
2. **`tests/model/test_parser.py`**
   - 新增整合測試：頂層 `union` 搭配 `pragma pack` 與多行成員宣告。
   - 為 `_split_member_lines` 建立單元測試，涵蓋註解、反斜線續行與巨集。
3. **`examples/`**
   - 新增 `v9_parser_integration_example.h`，包含上述語法以供測試使用。

## 測試案例
- `test_parse_mixed_struct_union_with_pack`
  - **輸入**：含 `#pragma pack(push,1)` 的檔案，頂層同時宣告 `struct` 與 `union`。
  - **預期**：AST 根節點依序掛載各型別，對齊值正確。
- `test_split_member_lines_with_continuation_and_macro`
  - **輸入**：成員行含 `\\` 續行與 `#define` 巨集。
  - **預期**：函式回傳的列表保持語義完整。
- `test_pragma_pack_stack_restoration`
  - **輸入**：多層 `push`/`pop` 組合。
  - **預期**：離開最內層後對齊設定恢復。

## TDD 迭代建議
1. Commit 1：新增 `test_parse_mixed_struct_union_with_pack`（Red）。
2. Commit 2：整合 `parse_aggregate_definition` 與 `#pragma pack`（Green）。
3. Commit 3：重構解析入口與 pack 堆疊（Refactor）。
4. Commit 4：新增 `_split_member_lines` 續行與巨集測試（Red）。
5. Commit 5：模組化 `_split_member_lines`（Green）。
6. Commit 6：整理拆分函式並更新文件（Refactor）。
7. Commit 7：最後以 `--all` 執行回歸並調整範例。

## 開發時程
- **週 1**：完成頂層 `union` 與 `pragma pack` 整合。
- **週 2**：模組化 `_split_member_lines` 並補齊測試。
- **週 3**：整合範例與文件，執行回歸測試。
- **週 4**：確認效能與穩定性，準備 v9 發佈。

---

本文件延續 v9 先前規劃，提供頂層 `union`、`#pragma pack` 與 `_split_member_lines` 在最終整合階段的 TDD 指引，確保釋出前解析器功能完整且易於維護。
