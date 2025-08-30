## V23 - Modern 取代 Legacy，並區分 Tree 與 Flat 顯示（TDD 計畫）

### 背景與目標
- 目前 Import .H 頁籤中，Modern 與 Legacy 視覺幾乎一致，且 Tree/Flat 模式在 UI 上差異不明顯。
- V23 目標：
  - 1) 以 Modern 完全取代 Legacy（Legacy 僅保留為別名或移除選項）。
  - 2) 讓 Tree 與 Flat 在 UI 呈現上明顯區分。

### 高層策略
- 完全移除 Legacy 與 GUI 版本切換選單，預設即為 Modern 介面（不再提供 legacy/modern 切換）。
- Tree 模式：啟用樹欄呈現（show="tree headings"），可展開/收合巢狀節點。
- Flat 模式：維持表格（show="headings"）、所有節點視為單層列表，不可展開；可選配顯示完整路徑欄，強化檢索。
- 保持既有欄位設定集中化（`MEMBER_TREEVIEW_COLUMNS`）的一致性。

---

### TDD 計畫總覽
1. 測試先行：撰寫 Presenter/View/Model 測試以驗證新行為。
2. 實作最小變更：通過測試後，再做結構化重構（例如移除 Legacy 項目）。
3. 補充文件與使用說明。

---

### 需新增/調整的測試（Test Cases）

#### A. Modern 取代 Legacy（移除 Legacy 與版本切換）
1) View 初始化與選單
   - 測試：Import .H 控制列不再提供 GUI 版本切換選單（`gui_version_var/gui_version_menu` 不存在）。
   - 檔案：`tests/view/test_struct_view.py` 新增/調整用例。
   - 斷言：
     - 啟動後即為 Modern，`modern_tree` 預設存在且可用。
     - 不存在 `gui_version_var`、`gui_version_menu`、`_on_gui_version_change`。

2) Presenter 行為
   - 檔案：`tests/presenter/test_struct_presenter.py`
   - 斷言：不再提供 `on_switch_gui_version` API；`get_default_context()` 不含 `gui_version` 欄位或其值固定不檢查。

3) 現有相容測試
   - 檔案：`tests/view/test_struct_view.py`（GUI 版本切換測試需移除或改寫）。
   - 調整：刪除所有針對 `legacy/v7` 切換與 `gui_version` 選單的斷言；改為驗證 Modern 預設存在與可用。

#### B. Tree vs Flat 視覺差異
1) Tree 模式顯示樹欄
   - 檔案：`tests/view/test_struct_view.py`
   - 步驟：
     - 切換 display_mode = "tree"。
     - 斷言 `member_tree.cget("show")` 含有 `tree`（例如 "tree headings"）。
     - 若有巢狀節點，驗證可展開（`get_children` 層級 > 1）。

2) Flat 模式單層表格
   - 檔案：`tests/view/test_struct_view.py`
   - 步驟：
     - 切換 display_mode = "flat"。
     - 斷言 `member_tree.cget("show") == "headings"`。
     - `get_children("")` 取得的每個項目 `get_children(item)` 都為空（不可展開）。

3) Model flat nodes 無 children（或 View 強制去除）
   - 檔案：`tests/model/test_struct_model_display_nodes.py`（新增）或併入既有 Presenter 測試。
   - 步驟：
     - 呼叫 `StructModel.get_display_nodes("flat")`。
     - 斷言：回傳陣列每個節點 `children == []`（或在 View 端去除 children 後再渲染）。

4) 選配：Flat 模式顯示完整路徑欄
   - 檔案：`tests/view/test_struct_view.py`
   - 步驟：
     - 切換到 flat，驗證多出 `full_path` 欄（若啟用此選配）。

---

### 需改動的檔案與調整內容（按檔案列出）

#### 1) `src/view/struct_view.py`
- A. 移除 GUI 版本切換功能：
  - 移除 GUI 版本標籤與選單（`label_gui_version` / `gui_version_var` / `gui_version_menu`）。
  - 移除 `_on_gui_version_change`、`_switch_to_legacy_gui`、`_switch_to_v7_gui` 方法與相關呼叫。
  - 初始化即建立 Modern 介面：`_create_modern_gui()` 或將現有 `member_tree` 統一為現代化樹視圖（可直接命名 `member_tree`）。

- B. Tree/Flat 視覺差異切換：
  - 在 `update_display()` 或 `show_treeview_nodes()` 中，依 `context["display_mode"]` 調整 `member_tree` 的 `show`：
    - `tree` → `member_tree.configure(show="tree headings")`
    - `flat` → `member_tree.configure(show="headings")`
  - 在 flat 模式渲染前，確保傳入的 nodes 無 children（可在 View 端過濾：把 `children` 清空）。
  - 若啟用完整路徑欄：在 flat 模式前先調整 `MEMBER_TREEVIEW_COLUMNS` 額外加入 `full_path`（或動態 columns）並在渲染時填值。

- C. Modern 預設啟用虛擬化（選配）：
  - 若頁面節點數 > threshold（如 1000），自動啟用 `VirtualTreeview`；否則使用一般 Treeview。
  - 測試需考慮 headless 環境。

#### 2) `src/presenter/struct_presenter.py`
- A. 移除 `on_switch_gui_version(version)` 與所有對其的引用。
- B. `get_default_context()`：移除 `gui_version` 欄位（或保留但不在任何地方使用；建議移除）。
- C. 同步更新 `validate_presenter_context`（`src/presenter/context_schema.py`）：刪除 `gui_version` 欄位定義。

- B. `on_switch_display_mode(mode)`：
  - 現有行為保留（設定 `display_mode`、重置 `expanded_nodes/selected_node`）。
  - 測試覆蓋 tree/flat 下的狀態初始化。

#### 3) `src/model/struct_model.py`
- A. `get_display_nodes("flat")` 明確移除 children：
  - 現況會對 flatten 後的每個節點仍呼叫 `to_treeview_node(n)`，其輸出包含 `children`。
  - 調整為 flat 模式輸出節點其 `children` 為空，或提供 `to_treeview_node(..., strip_children=True)` 參數。

- B. （選配）提供 full_path：
  - 在展平時附加 `full_path` 欄位（透過遞迴組路徑或在 `ast_to_dict` 中持有 parent 路徑）。

#### 4) 測試檔更新
- `tests/view/test_struct_view.py`：
  - 刪除與 `gui_version` 相關的測試（包含 `test_gui_version_switch_ui_and_presenter_call`、`test_gui_version_switch_ui_visibility` 及任何使用 `_on_gui_version_change` 的測試）。
  - 新增 Modern 預設存在與可用的測試（取代 `test_modern_gui_creation` → 驗證初始化後現代 Treeview 已存在）。
  - 新增/調整 Tree/Flat 視覺差異測試（見上節）。
- `tests/presenter/test_struct_presenter.py`：
  - 移除 `on_switch_gui_version` 相關測試。
  - 更新 `get_default_context` 期望（不含 `gui_version`）。
- `tests/model/test_struct_model_display_nodes.py`（新增）：驗證 flat nodes 無 children 與（選配）full_path。

---

### 逐步 TDD 流程（細項）

1) 新增/調整測試：Modern 取代 Legacy（移除 Legacy 與版本切換）
   - 編寫 View 測試：
     - 斷言初始化後即為 Modern，`modern_tree/member_tree` 存在；且不存在 `gui_version_var/gui_version_menu`。
   - 編寫 Presenter 測試：
     - `get_default_context()` 不含 `gui_version`；不存在 `on_switch_gui_version`。

2) 新增測試：Tree vs Flat 視覺差異
   - Tree：`show` 包含 `tree`；巢狀可展開。
   - Flat：`show == "headings"`；所有節點無子項。

3) 實作最小變更：
   - View：
     - 移除 GUI 版本切換 UI 與方法；初始化即建立 Modern Treeview。
     - 依 display_mode 設定 `member_tree.configure(show=...)`；flat 模式渲染前移除 children。
   - Model：`get_display_nodes("flat")` 改為輸出 children=[]；（選配）提供 `full_path`。
   - Presenter：移除 `gui_version` 相關邏輯與欄位；同步更新 context schema。

4) 通過測試後的重構：
   - 刪除 `_switch_to_legacy_gui()`、`_switch_to_v7_gui()`、`_on_gui_version_change()` 與相關 UI 元件。
   - 完全移除 GUI 版本選單；將相關字串鍵（若有）標註為 deprecated 或移除。
   - 更新文件（v6/v8 文件中 legacy/modern 的描述，標註 v23 起 Modern 為唯一介面）。

5) 文件與使用說明：
   - 更新 `docs/development/v6_GUI_view.md`/`v8_GUI_integration.md` 的 GUI 版本切換章節。
   - 新增本文件連結與實作狀態。

---

### 風險與回退策略
- 風險：既有 UI 測試與文件廣泛引用 `legacy` 與版本切換，需全面更新；headless CI 下 Treeview `show` 驗證需穩健。
- 回退：以 feature flag 臨時恢復 GUI 版本選單（非預設顯示），僅供內部測試；正式版本不建議回退至 Legacy。

---

### 現有測試需同步調整清單（精準）

以下列出受影響的既有測試與建議調整方式（已確定移除 Legacy 與版本切換選單）：

- tests/view/test_struct_view.py
  - 刪除：`test_gui_version_switch_ui_and_presenter_call`、`test_gui_version_switch_ui_visibility`、任何使用 `_on_gui_version_change` 的測試段落。
  - 搜尋並移除：任何對 `self.view.gui_version_var`、`self.view.gui_version_menu` 的引用。
  - 搜尋並移除：任何對 `"gui_version": "legacy"` 初始 context 的強制斷言（整體去除 gui_version）。
  - 新增：初始化即為 Modern 的測試（驗證 `modern_tree`/`member_tree` 存在、可插入節點）。
  - 新增/調整：Tree/Flat 視覺差異測試（`show` 設定與 children 結構）。

- tests/presenter/test_struct_presenter.py
  - 刪除：`on_switch_gui_version` 相關測試與任何直接引用該 API 的測試資料。
  - 更新：`get_default_context` 期望（不含 `gui_version`）。
  - 保持：`on_switch_display_mode` 測試；可補強對 `expanded_nodes`/`selected_node` 重置的斷言。

- tests/presenter/test_v2p_contract.py
  - 不需檢查 `gui_version`；可選擇性補強對 tree/flat 切換後 nodes 結構差異的合約測試（flat 無 children）。

- tests/presenter/test_v7_presenter.py
  - 無直接依賴 gui_version；保持不變。

- 新增：tests/model/test_struct_model_display_nodes.py（可新建）
  - 驗證 `StructModel.get_display_nodes("flat")` 回傳的每個節點 `children == []`。
  - 若啟用 `full_path` 欄位，驗證 flat 模式節點含此欄並值正確（路徑組合）。

- 其他：
  - 若實作在 flat 模式新增 `full_path` 欄，需同步更新 View 層對 `MEMBER_TREEVIEW_COLUMNS` 的測試（欄位一致性檢查）。
  - 若改動 GUI 版本選單（移除/改名），需同步更新任何查找該 widget 的測試（避免硬依賴）。

建議流程：一次性移除 Legacy 與 GUI 版本切換並同步更新測試；如需降低風險，可在短期開發分支中先保留 feature flag 但預設關閉，不在主分支暴露。

---

### 完成定義（DoD）
- 所有新增/調整測試通過（含 headless/CI）。
- 已完全移除 Legacy 與 GUI 版本切換：
  - 不存在 `gui_version_var/gui_version_menu`、`_on_gui_version_change`、`_switch_to_legacy_gui/_switch_to_v7_gui`。
  - Presenter context 與 schema 不含 `gui_version`。
- Tree 與 Flat 在 UI 呈現明顯不同：
  - Tree：`show="tree headings"`、可展開巢狀。
  - Flat：`show="headings"`、無子項。
- 文件已更新，並記錄相容性注意事項與移除項目列表。

