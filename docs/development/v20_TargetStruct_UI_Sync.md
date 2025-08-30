## v20 Target Struct 切換後的 UI 同步修正與改進計畫

### 背景與目標
- 在匯入 .h 檔時，當同一份檔案內含多個頂層 `struct/union`，使用者可透過「Target Struct」下拉選單選擇要檢視的根結構。
- 目標：當使用者切換不同的 `struct/union` 後，UI 應同步更新「Struct Layout」與「Hex 輸入格（欄位長度/數量）」以反映新選擇的 `total_size` 與 layout。

---

### 問題描述（現象）
- 現況：切換 Target Struct 時，僅重新整理 TreeView 的節點顯示；「Struct Layout」及「Hex 輸入格數量」沒有更新。
- 造成結果：
  - Layout 面板仍顯示前一個 `struct/union` 的欄位排版。
  - Hex 輸入格數量仍依前一個 `total_size` 計算，導致欄位長度與結構不一致。

---

### 影響範圍
- 使用匯入 .h 功能，且同一 .h 檔包含多個頂層 `struct/union`，並透過 Target Struct 下拉選單頻繁切換者。
- UI 一致性與使用者信任感：切換後數據不一致，易造成誤判與解析錯誤。

---

### 根因分析
- Presenter 已提供 `set_import_target_struct(name)` 會更新 Model（解析 AST、重算 layout、更新 `total_size`），並 push context。
  - 位置：`src/presenter/struct_presenter.py::set_import_target_struct`
  - Model 切換實作：`src/model/struct_model.py::set_import_target_struct`
- View 的 Target Struct 事件處理僅呼叫 Presenter 並更新「資料節點」，但缺少對「Struct Layout」與「Hex Grid」的同步刷新。
  - 原始事件處理：`src/view/struct_view.py::_on_target_struct_change` 只做 `update_display(...)`。
- 因此 layout 與 hex grid 沒有在切換後被 rebuild。

---

### 預期行為
當 Target Struct 改變時：
1) 重新抓取當前 `presenter.model` 的 `struct_name`、`layout`、`total_size`、`struct_align`。
2) 呼叫 `show_struct_layout(struct_name, layout, total_size, struct_align)` 更新 Layout 面板。
3) 將 `current_file_total_size` 設為新的 `total_size`，讀取目前 UI 的單位大小（1/4/8 Bytes），並 `rebuild_hex_grid(total_size, unit_size)`。

---

### v20 改動摘要（實作重點）
- View：於 Target Struct 變更事件中補齊 UI 同步行為。
  - 檔案：`src/view/struct_view.py`
  - 函式：`_on_target_struct_change`
  - 新增步驟：
    - 自 `presenter.model` 取回 `struct_name/layout/total_size/struct_align`。
    - 呼叫 `show_struct_layout(...)` 刷新。
    - 更新 `current_file_total_size` 並依目前 unit size `rebuild_hex_grid(...)`。

---

### 具體代碼介面（參考）
- Presenter
  - `src/presenter/struct_presenter.py::set_import_target_struct(name)`
    - 驅動 Model 切換對象並 push context。
- Model
  - `src/model/struct_model.py::set_import_target_struct(name)`
    - 以 AST 重新選定目標聚合，計算 layout 與 `total_size`。
- View（新增邏輯）
  - `src/view/struct_view.py::_on_target_struct_change`
    - 補：更新 layout 面板與 hex grid。

---

### UX/契約考量
- 單位大小切換與 Target Struct 切換互動：
  - Target Struct 切換後，hex grid 以「目前選定的單位大小」重建，避免額外的使用者操作。
- `current_file_total_size` 為匯入檔案的當前 root `total_size` 快取：
  - 切換 root 時需同步更新，供後續 unit size 變更時使用。

---

### 測試計畫（TDD/回歸）
1) View 行為（新增或擴充）：
   - `test_struct_view_target_struct_updates_layout_and_hex_grid`
     - 模擬多個頂層 `struct/union` 的 .h 匯入後切換 Target Struct。
     - 斷言：
       - `show_struct_layout` 被呼叫且資料對應新 root。
       - `rebuild_hex_grid` 被呼叫，box 數量符合新 `total_size` 與當前 unit size。
2) Presenter/Model 既有測試回歸：
   - `set_import_target_struct` 切換 root 後，`layout/total_size/struct_name` 正確更新。
3) 手動驗證腳本（可選）：
   - 匯入含 `struct A {...}; struct B {...};` 的 .h 檔，來回切換 A/B，觀察 Layout 與 hex grid 是否同步變更。

---

### 風險與相容性
- 變更僅限 View 邏輯，不影響 Presenter/Model API；屬低風險 UI 修正。
- 小心避免在無 presenter/model 或屬性缺失時觸發例外，故加入 `getattr` 與 try/except 防護。

---

### 驗收標準
- 切換 Target Struct 後：
  - Layout 面板立即反映新結構（欄位、offset/size、bitfield 資訊）。
  - Hex 輸入格數量與每格長度符合新 `total_size` 與目前 unit size。
  - TreeView、Layout、Hex Grid 三者內容一致且無殘留舊資料。

---

### 後續改進（v20+）
- 將此行為抽象為統一的「上下文切換後 UI 同步」helper：
  - 例如：`_sync_layout_and_hex_grid_from_model()`，供其他影響 `total_size/layout` 的事件（如 pack 對齊策略切換、arch 模式切換）重用。
- 於 Presenter push context 時，可在 context 裡帶上 `total_size` 及當前 `unit_size`，讓 View 可更少查詢 model。
- 增加 E2E 測試：模擬實際 GUI 互動軌跡，降低回歸風險。

