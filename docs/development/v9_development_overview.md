# v9 開發總表

以下依開發順序列出 v9 相關文件，完成每個階段後勾選對應項目。

1. 規劃基礎
   - [ ] **v9_parser_tdd_plan.md**：建立 v9 目標與 TDD 流程，涵蓋頂層 `union`、`#pragma pack` 與 `_split_member_lines` 重寫。
2. 詳細規劃
   - [ ] **v9_parser_tdd_detailed_plan.md**：細分每個功能的實作步驟、測試命名與開發時程。
3. 初始增強方案
   - [ ] **v9_parser_top_level_union_and_pragma_pack.md**：分析現有解析器缺口，規劃頂層 `union` 與 `pragma` 支援的基本改動。
4. 整合功能計畫
   - [ ] **v9_parser_top_level_union_pragma_pack_split_member_line.md**：整合頂層 `union`、`#pragma pack` 與 `_split_member_lines` 的開發策略。
5. TDD 執行計畫
   - [ ] **v9_parser_tdd_top_level_union_pragma_pack_split_member_line.md**：以 TDD 方式實作整合功能的具體指引。
6. 開發檢查清單
   - [ ] **v9_parser_tdd_top_level_union_pragma_pack_split_member_line_checklist.md**：逐項確認測試、實作與錯誤處理是否完成。
7. 後續補強
   - [ ] **v9_parser_tdd_top_level_union_pragma_pack_split_member_line_followup.md**：涵蓋匿名 `union`、未配對 `pragma` 等邊界情境的後續規劃。
8. 最終整合
   - [ ] **v9_parser_tdd_top_level_union_pragma_pack_split_member_line_integration_plan.md**：統整各功能並新增整合測試與範例。
9. 釋出準備
   - [ ] **v9_parser_top_level_union_pragma_pack_split_member_line_release_plan.md**：收尾重構、文件同步與效能評估。
10. 未來方向
    - [ ] **v9_parser_top_level_union_pragma_pack_split_member_line_future_plan.md**：進一步的錯誤處理、模組化與效能提升規劃。
