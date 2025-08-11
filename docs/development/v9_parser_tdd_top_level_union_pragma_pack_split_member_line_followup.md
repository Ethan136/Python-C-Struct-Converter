# v9 Parser Top-Level Union / Pragma Pack / `_split_member_lines` Follow-Up TDD Plan

## 背景
- v9 初步規劃已建立 parser 支援頂層 `union`、`#pragma pack` 與穩健的 `_split_member_lines` 基礎，但仍有進階情境未涵蓋。
- 此文件延伸先前計畫，聚焦於補強邊界測試與錯誤處理，確保解析器在實務使用中保持穩定。

## 建議
1. **錯誤條件處理**：測試 `#pragma pack` 未配對 `pop`、未知 `pragma` 指令等異常流程。
2. **進階 `union` 情境**：涵蓋頂層匿名 `union` 與帶 `__attribute__((packed))` 等屬性的宣告。
3. **`_split_member_lines` 邊界**：處理巨集、行末反斜線與註解混合的拆分邏輯，避免錯誤切分。
4. **小步迭代**：維持 Red→Green→Refactor 週期，確保每次變更都有測試保護。

## 實作步驟
- 依序新增失敗測試、實作功能、重構程式碼。
- 每完成一組功能，執行 `python run_tests.py -t test_parser` 確認回歸。
- 更新 `examples/` 與文件，讓測試與範例同步。

## 詳細實作
1. **`src/model/parser.py`**
   - `_handle_directives`：擴充處理未配對 `pop` 與未知 `pragma`，提供警告或錯誤。
   - `parse_aggregate_definition`：支援 `__attribute__` 與頂層匿名 `union`。
   - `_split_member_lines`：新增對 `\\\n` 續行、`//` 與 `/* */` 註解、`#define` 巨集的防護。
2. **`tests/model/test_parser.py`**
   - 新增對上述情境的測試，確保解析結果與錯誤處理符合預期。
3. **`examples/`**
   - 製作含巢狀 `#pragma pack`、巨集與匿名 `union` 的示例檔案供測試使用。

## 新增測試案例
- `test_parse_top_level_union_with_attribute`
- `test_parse_struct_with_unmatched_pragma_pack_pop`
- `test_split_member_lines_with_macro_and_comment`
- `test_parse_nested_pragma_pack_stack_behavior`
- `test_split_member_lines_with_line_continuation`

## TDD 迭代建議
1. Commit 1：新增 `test_parse_top_level_union_with_attribute`（Red）。
2. Commit 2：實作 `parse_aggregate_definition` 支援 `__attribute__`（Green）。
3. Commit 3：重構頂層聚合解析流程（Refactor）。
4. Commit 4：新增 `test_parse_struct_with_unmatched_pragma_pack_pop`（Red）。
5. Commit 5：改寫 `_handle_directives` 處理 pack 堆疊錯誤（Green）。
6. Commit 6：整理指令錯誤處理流程（Refactor）。
7. Commit 7：新增 `_split_member_lines` 巨集與註解測試（Red）。
8. Commit 8：實作續行符號與巨集處理邏輯（Green）。
9. Commit 9：重構拆分函式並更新文件（Refactor）。

## 開發時程
- **週 1**：完成屬性化 `union` 支援與相關測試。
- **週 2**：補齊 `pragma pack` 錯誤處理與巢狀測試。
- **週 3**：強化 `_split_member_lines` 處理巨集與註解混合情境。
- **週 4**：整合與回歸測試，整理文件後準備發佈。

---

本文件補充 v9 Parser 在頂層 `union`、`#pragma pack` 及 `_split_member_lines` 的進階 TDD 規劃，協助後續實作保持穩定與可維護。
