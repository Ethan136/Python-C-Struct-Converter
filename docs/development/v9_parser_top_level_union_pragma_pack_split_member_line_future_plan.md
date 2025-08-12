# v9 Parser Top-Level Union / Pragma Pack / `_split_member_lines` Future Plan

## 背景
- 既有文件已規劃頂層 `union`、`#pragma pack` 與 `_split_member_lines` 的核心實作與整合。
- 後續仍需針對邊界情境、效能與文件同步進行更細緻的規劃，以確保功能在大型專案中穩定運作。

## 建議
1. **強化錯誤處理與警告**：對未知 `pragma`、未配對的 `pack` 堆疊與 `_split_member_lines` 異常提供明確訊息。
2. **支援進階 `union` 情境**：涵蓋頂層匿名 `union`、具 `__attribute__((packed))` 等屬性的宣告與巢狀結構。
3. **模組化拆分流程**：將 `_split_member_lines` 拆分成註解清理、括號深度追蹤與續行處理等子函式，提升可維護性。
4. **文件與範例同步**：更新 README、開發指南與 `examples/`，使新功能與限制清楚呈現。

## 實作步驟
- 依循 Red → Green → Refactor 迭代；每項功能先撰寫失敗測試再實作與重構。
- 完成後執行 `python run_tests.py -t test_parser`，最終以 `python run_tests.py` 全套驗證。

## 詳細實作
1. **頂層 `union`**
   - `parse_aggregate_definition` 支援匿名與帶屬性的 `union`，並與 `struct` 共用入口。
   - 增加對巢狀 `union` 的遞迴解析與對齊繼承邏輯。
2. **`#pragma pack`**
   - `_handle_directives` 擴充未知指令與未配對 `pop` 的例外處理。
   - 維護巢狀 `push/pop` 堆疊，並將 pack 值寫入 AST 節點。
3. **`_split_member_lines`**
   - 抽出 `strip_comments()`、`track_brace_depth()`、`handle_line_continuation()`。
   - 處理巨集展開與行末反斜線，避免錯誤切分。

## 測試案例
- `test_parse_top_level_union_with_attribute`
- `test_parse_struct_with_unmatched_pragma_pack_pop`
- `test_split_member_lines_with_macro_and_comment`
- `test_parse_nested_pragma_pack_stack_behavior`
- `test_split_member_lines_with_line_continuation`

## 開發時程
- **週 1**：完成匿名與屬性化頂層 `union` 支援。
- **週 2**：補齊 `pragma pack` 錯誤處理與巢狀堆疊測試。
- **週 3**：模組化 `_split_member_lines` 並涵蓋巨集與續行情境。
- **週 4**：整合與回歸測試，更新文件與範例後準備釋出。

## 其他考量
- 針對大型檔案與深度巢狀結構進行效能評估，必要時使用 profiling 優化。
- `_handle_directives` 應保留擴充點以支援其他前處理指令（如 `#pragma once`）。
- 確認 GUI 與 CLI 皆能載入含上述語法的檔案，維持前後端一致性。

---

本文件延續 v9 既有規劃，提供頂層 `union`、`#pragma pack` 與 `_split_member_lines` 的後續開發方向，以利在未來版本中達到更高的穩定性與可維護性。
