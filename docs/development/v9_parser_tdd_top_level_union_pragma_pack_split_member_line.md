# v9 Parser Top-Level Union / Pragma Pack / `_split_member_lines` TDD Plan

## 背景
- v9 目標是讓 `V7StructParser` 更完善，能處理頂層 `union`、`#pragma pack` 對齊與更穩健的 `_split_member_lines`。
- 現有解析器在遇到上述情境時會提前返回 `None` 或拆分錯誤，無法支援 `examples/v5_features_example.h` 中的案例。
- 透過測試驅動開發（TDD）逐步導入功能，可確保回歸防護並厘清需求。

## 建議
1. **頂層 `union` 支援**：重構入口函式，能同時偵測 `struct` 與 `union` 作為根節點。
2. **`#pragma pack` 指令解析**：在清理內容階段保留對齊資訊，並將 `push/pop` 堆疊套用到後續節點。
3. **改寫 `_split_member_lines`**：以括號深度追蹤方式避免多行 `union/struct` 被切成多段。
4. **強化測試**：針對每項功能撰寫失敗測試，再依序實作與重構。

## 實作步驟
- 先新增失敗測試，再實作功能，最後重構：Red → Green → Refactor。
- 測試集中於 `tests/model/test_parser.py`，必要時新增 `examples/` 檔案。

## 詳細實作
1. **頂層 `union`**
   - `parse_struct_definition` 改為 `parse_aggregate_definition` 或內部判斷 `struct/union`。
   - 透過 `ASTNodeFactory.create_union_node` 建立根節點。
2. **`#pragma pack`**
   - 新增 `_handle_directives` 於 `_clean_content` 階段解析 `#pragma`。
   - 維護 pack 堆疊並附加到 AST 節點的 `pack` 欄位。
3. **`_split_member_lines`**
   - 追蹤 `{`/`}` 括號深度；僅在深度回到 0 時切分。
   - 處理行內註解與續行符號 `\`，確保不誤切。

## 需要改動的函式與檔案
- `src/model/parser.py`
  - `parse_struct_definition`（或新函式）
  - `_clean_content` / `_handle_directives`
  - `_split_member_lines`
- `tests/model/test_parser.py`
- `examples/` 內新增對應的測試輸入檔

## 測試案例
- `test_parse_top_level_union_returns_ast`
  - **輸入**：僅含 `union` 定義的檔案。
  - **預期**：建立 `UnionNode` 根節點，含成員 `a`、`b`。
- `test_parse_struct_with_pragma_pack_applies_alignment`
  - **輸入**：含 `#pragma pack(push,1)` 的 `struct`。
  - **預期**：`StructNode.pack == 1` 且 `pop` 後恢復預設。
- `test_split_member_lines_handles_nested_union`
  - **輸入**：巢狀 `union` 與註解混雜的 `struct`。
  - **預期**：`_split_member_lines` 回傳的列表將整個 `union` 視為單一元素。

## TDD 迭代建議
1. Commit 1：新增 `test_parse_top_level_union_returns_ast`（Red）。
2. Commit 2：實作 `parse_aggregate_definition` 支援 `union`（Green）。
3. Commit 3：重構解析入口函式（Refactor）。
4. Commit 4：新增 `test_parse_struct_with_pragma_pack_applies_alignment`（Red）。
5. Commit 5：導入 `_handle_directives` 支援 `pragma pack`（Green）。
6. Commit 6：整理指令解析模組（Refactor）。
7. Commit 7：新增 `test_split_member_lines_handles_nested_union`（Red）。
8. Commit 8：改寫 `_split_member_lines`（Green）。
9. Commit 9：重構並更新文件（Refactor）。

## 開發時程
- **週 1**：完成頂層 `union` 支援。
- **週 2**：導入 `#pragma pack` 邏輯並驗證。
- **週 3**：改寫 `_split_member_lines` 並補齊測試。
- **週 4**：回歸測試與文件整理，準備提交。

---

本文件提供 v9 階段針對頂層 `union`、`#pragma pack` 與 `_split_member_lines` 的 TDD 開發規劃，供後續實作與驗證參考。
