# v9 Parser Top-Level Union / Pragma Pack / `_split_member_lines` Release Plan

## 背景
- 前期規劃已透過 TDD 導入頂層 `union` 解析、`#pragma pack` 對齊堆疊以及改寫 `_split_member_lines` 以避免多行聚合型別被誤切。
- Follow-up 與 Integration Plan 完成核心功能整合，但在實務應用與文件更新上仍需進一步統整。
- 本文件延續 v8 文件風格，作為 v9 最終釋出前的收尾規劃。

## 建議
1. **驗證整體流程**：於 Parser、例子、GUI 互動間進行端到端測試，確保 pack 堆疊與頂層 `union` 同時存在時 AST 正確。
2. **錯誤處理**：對未知 `#pragma`、未配對 `pop` 或 `_split_member_lines` 遇到異常時提供明確訊息，避免悄悄失敗。
3. **文件同步**：更新 README、開發指南與示例，使團隊與使用者了解新的語法支援與限制。
4. **效能評估**：在大型專案或深度巢狀結構上量測解析時間，必要時以 profiling 調整實作。

## 實作步驟
- 整理 `parser.py` 最終介面與內部 helper 命名，刪除不再使用的暫時性函式。
- 補齊 `examples/` 中覆蓋 `union`、`pragma pack` 與行續案例的檔案，並在測試中引用。
- 在 `tests/model/test_parser.py` 新增整合測試，模擬複雜多層 `push/pop`、匿名 `union` 與行內註解組合。
- 針對 `_split_member_lines` 建立獨立單元測試，覆蓋巨集、行末反斜線與註解交錯情境。
- 更新 `run_all_tests.py` 與 CI 設定，確保新測試自動執行。
- 文件與 README 同步說明 pack 對齊及 `union` 支援情形。

## 詳細實作
1. **`src/model/parser.py`**
   - 將 `parse_aggregate_definition` 作為唯一入口，統一路徑處理 `struct/union`。
   - `_handle_directives` 增加未知 pragma 與 pack stack 錯誤的例外或警告。
   - `_split_member_lines` 拆分出 `strip_comments()`、`track_brace_depth()` 等子函式，降低複雜度。
2. **`tests/model/test_parser.py`**
   - 新增 `test_parse_mixed_aggregate_with_nested_pack()`、`test_split_member_lines_with_macro_and_comment()` 等案例。
   - 以 `@pytest.mark.parametrize` 驗證 pack 堆疊與匿名 `union` 組合。
3. **`examples/`**
   - 增加 `v9_parser_release_example.h` 展示頂層 `union`、巢狀 pack 及行續語法。
4. **文件**
   - `docs/development` 內相關 v9 檔案補充連結與狀態，README 增加使用說明。

## 測試腳本更新細節
- 執行 `python run_tests.py -t test_parser` 作為基本驗證，最終釋出前執行 `python run_tests.py` 全套測試。
- CI 應新增解析器專用工作流程，於 PR 觸發時自動執行以上兩組測試。

## 其他考量
- 若後續需支援其他前置處理指令（如 `#pragma once`），`_handle_directives` 應保持擴充性。
- `_split_member_lines` 在巨集展開後的效能需監控，避免在包含大量巨集的專案中造成瓶頸。
- 釋出前確認 GUI 與 CLI 均能載入含上述語法的檔案，以確保解析器與前端一致。

---

本計畫整合先前的 v9 規劃，提供頂層 `union`、`#pragma pack` 與 `_split_member_lines` 在釋出前的最終收尾指引，確保功能完整、測試充足且文件同步更新。

