## v17 Data Format Unification + Target Struct Selection（TDD 計畫）

### 目標
- 統一 parser → model → layout 的資料格式為 MemberDef（移除 tuple/dict 混用），降低型別分歧與維護成本。
- 保持 v15（指標 N-D 陣列展開）與 v16（引用型 struct/union、forward reference）能力不退步。
- 匯入 .h 頁簽支援指定要顯示的根 struct/union 名稱（Target Struct Selection），不再受「取最後一個頂層 struct」的限制。
- 強化 GUI Treeview 資料傳遞：`values` 必為字串列表/tuple（避免 Tk `unknown option "{} {} {} {}"` 類錯誤）。

---

### 範圍與風險
- 僅針對本專案現有解析與 GUI 顯示流程；不處理跨檔 include、typedef 與複雜宣告語法。
- 需要調整多處 API 介面（`calculate_layout`/`load_struct_from_file`/Presenter），需完整回歸。

---

### 主要變更項目（檔案與函式級明細）

1) `src/model/struct_parser.py`
   - 方向：全面導入 `parse_member_line_v2`/`MemberDef`。
   - 變更點：
     - 移除（或標記 deprecated）`parse_member_line` 舊 tuple/dict 輸出；內部改為只對外暴露 v2 版本。
     - 確認以下情境皆回傳 `MemberDef`：
       - 基本型別、bitfield、pointer、N-D 陣列（含 pointer 元素，v15）、
       - 具名/匿名 struct/union、引用型 struct/union（v16）、forward reference（v16）。
     - `parse_struct_definition_ast(file_content, target_name=None)`：保留 v16 的 `target_name` 與 known-types registry/解參考 pass。

2) `src/model/layout.py`
   - 方向：`calculate` 僅處理 `MemberDef` 物件；保留 `_get_attr` 但簡化分支。
   - 變更點：
     - 確認 `StructLayoutCalculator.calculate(members: List[MemberDef])` 不再依賴 tuple/dict。
     - 維持並驗證：
       - N-D 陣列展開（含 pointer 元素）
       - 巢狀 struct/union/array 展開
       - bitfield 排版與 storage 單元換行

3) `src/model/struct_model.py`
   - 方向：移除 legacy 展平（tuple/dict）路徑，統一以 `MemberDef` 為核心。
   - 變更點：
     - `calculate_layout(members)`：刪除 `_flatten_legacy_members` 路徑；直接呼叫 `LayoutCalculator.calculate(members)`（MemberDef）。
     - `load_struct_from_file(file_path, target_name=None)`：
       - 呼叫 `parse_c_definition_ast` → `parse_struct_definition_ast(file_content, target_name=target_name)`。
       - 於 context 中保留 `available_top_level_types`（列出檔案內所有頂層 struct/union 名稱），供 GUI 下拉選單使用。
     - `get_struct_ast()`：維持 AST → dict 的輸出格式不變。

4) `src/presenter/struct_presenter.py`
   - 方向：V2P API 新增「選擇根結構」能力；規範 Treeview `values` 型別。
   - 變更點：
     - 新增公開方法：`set_import_target_struct(name: str)` → 觸發 model 重新載入（或僅重新解析以切換 root）。
     - `update_display(...)` 前，將每個節點的 `values` 統一轉成 `("value", "offset", "size")` 三欄字串 tuple；若無值則空字串。
     - 於 `context` 中帶出 `available_top_level_types`，供 view 渲染下拉選單。

5) `src/view/struct_view.py`
   - 方向：匯入 .h 頁簽加上「Target Struct」選擇器。
   - 變更點：
     - 新增 UI 元件（下拉/輸入框），資料來源為 Presenter context 的 `available_top_level_types`。
     - 當使用者選擇/輸入名稱時，呼叫 Presenter `set_import_target_struct(name)`。
     - `Treeview.insert(...)` 時，`values` 明確傳入 tuple/list（避免傳入 dict/None 造成 Tkinter 異常）。

---

### TDD 計畫與測試清單

1) Parser 層（新檔：`tests/model/test_parser_v17_memberdef_only.py`）
   - `test_scalar_pointer_array_returns_memberdef`
   - `test_nd_pointer_array_memberdef_dims_preserved`（覆蓋 v15）
   - `test_referenced_struct_union_memberdef`（覆蓋 v16 引用/forward ref）
   - 斷言：所有成員皆為 `MemberDef`，不再出現 tuple/dict。

2) Layout 層（新檔：`tests/model/test_layout_v17_memberdef_only.py`）
   - `test_layout_expands_nd_pointer_array`（v15 回歸）
   - `test_layout_referenced_struct_array_expand`（v16 回歸）
   - `test_layout_forward_reference_expand`（v16 回歸）
   - 斷言：展平名稱（`a.x` / `arr[0].x` / `nd[1][1].x`）、offset/size 合理。

3) Model 層（新檔：`tests/model/test_model_v17_target_struct.py`）
   - `test_load_struct_from_file_with_target_name_outer`
   - `test_load_struct_from_file_with_target_name_forward`
   - `test_available_top_level_types_listed`
   - 斷言：能切換 root、`available_top_level_types` 非空且包含目標名稱。

4) Presenter 層（新檔：`tests/presenter/test_presenter_v17_target_struct.py`）
   - `test_set_import_target_struct_switches_root`
   - `test_presenter_values_are_strings`
   - 使用 mock view，檢查呼叫 `update_display` 時節點 `values` 為字串 tuple。

5) View 層（新增/擴充既有 view 測試）
   - `test_struct_view_target_struct_dropdown_population`（可用小型 integration/mocking）
   - `test_struct_view_insert_values_tuple_type`
   - 斷言：不會觸發 Tkinter `unknown option "{} {} {} {}"`。

---

### 開發步驟（實作順序）

1) Parser：
   - 將對外使用面改為 `parse_member_line_v2` 與 `parse_struct_definition_ast`（維持 v16 的 registry/target_name）。
   - 清理 `parse_member_line` 的對外呼叫點；如仍留用，改內部轉呼 v2 後回傳 MemberDef。

2) Layout：
   - 移除/關閉 tuple/dict 支援路徑；測試以 MemberDef 驗證所有展開行為。

3) Model：
   - `calculate_layout` 移除 legacy 分支。
   - `load_struct_from_file(file_path, target_name=None)` 加入 target 名稱參數；
   - 保留 `available_top_level_types` 至 context。

4) Presenter：
   - 新增 `set_import_target_struct(name)` → 重新解析/載入。
   - `get_display_nodes("tree")` 的 `values` 統一為字串 tuple，避免 view 層崩潰。

5) View：
   - 匯入 .h 頁簽新增「Target Struct」下拉；變更時呼叫 Presenter。
   - `Treeview.insert(..., values=...)` 僅傳入 `(str(value), str(offset), str(size))`。

6) 文件/範例：
   - 更新 `docs/development`：本檔與 v15/v16 對齊連結。
   - 補充 `examples/`：`v16_referenced_struct_example.h` 可作為手動驗證。

---

### 驗收準則
- 所有 v17 新增測試 + 既有測試（含 v15/v16）全部綠燈。
- 匯入 .h 頁簽可選擇目標 struct，視覺上顯示正確，切換不閃退。
- GUI Treeview 不再出現 `_tkinter.TclError: unknown option "{} {} {} {}"`。
- Parser/Model/Layout 僅使用 `MemberDef` 於內部資料流；取消 tuple/dict 混用。

---

### 推出與回滾
- 建議以 feature 分支開發：`feature/v17-unify-and-target-struct`。
- 提交順序：Parser → Layout → Model → Presenter → View → 文件/範例。
- 若 View 層變更導致暫時性不相容，可先隱藏 Target Struct 控制項，以不影響既有功能為前提進行漸進式整合。


