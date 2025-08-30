## V23 - Modern 取代 Legacy，並區分 Tree 與 Flat 顯示（TDD 計畫）

### 背景與目標
- 目前 Import .H 頁籤中，Modern 與 Legacy 視覺幾乎一致，且 Tree/Flat 模式在 UI 上差異不明顯。
- V23 目標：
  - 1) 以 Modern 完全取代 Legacy（Legacy 僅保留為別名或移除選項）。
  - 2) 讓 Tree 與 Flat 在 UI 呈現上明顯區分。

### 高層策略
- 移除 GUI 版本選單的 `legacy`，預設即為 Modern；或保留 `legacy` 作為 Modern 的別名（行為一致）。
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

#### A. Modern 取代 Legacy
1) View 初始化與選單
   - 測試：Import .H 控制列不再提供 `legacy` 選項；或選 `legacy` 時行為等同 `modern`。
   - 檔案：`tests/view/test_struct_view.py` 新增/調整用例。
   - 斷言：
     - 若移除 legacy：GUI 版本選單僅含 `modern`。
     - 若保留為別名：切換到 `legacy` 會呼叫 `_switch_to_modern_gui()`，`member_tree` 指向 `modern_tree`。

2) Presenter 行為
   - 檔案：`tests/presenter/test_struct_presenter.py`
   - 斷言：`on_switch_gui_version("legacy")` 與 `("modern")` 導致相同的 context 結果，或 `legacy` 無法設定（若選單移除）。

3) 現有相容測試
   - 檔案：`tests/view/test_struct_view.py`（GUI 版本切換測試需更新）。
   - 調整：若移除 legacy，刪除或調整相關斷言；若保留別名則更新為期待 modern 行為。

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
- A. 移除或統一 GUI 版本選單：
  - 移除 `legacy` 選項，只保留 `modern`；或將 `legacy` 切換路徑導向 `_switch_to_modern_gui()`。
  - 更新 `self.gui_version_var` 預設值與選項清單。
  - 若移除 legacy：刪除 `_switch_to_legacy_gui()` 未被使用的邏輯；若保留別名，方法可留但內部直接調用 `_switch_to_modern_gui()`。

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
- A. `on_switch_gui_version(version)`：
  - 若移除 legacy：限制 `version` 僅允許 `modern`，或將 `legacy` 正規化為 `modern`。
  - 更新 context 與 `validate_presenter_context` 一致。

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
- `tests/view/test_struct_view.py`：補齊上述 A/B 測試。
- `tests/presenter/test_struct_presenter.py`：更新 GUI 版本切換測試。
- `tests/model/test_struct_model_display_nodes.py`（新增）：驗證 flat nodes 無 children 與（選配）full_path。

---

### 逐步 TDD 流程（細項）

1) 新增/調整測試：Modern 取代 Legacy
   - 編寫 View 測試：
     - 若移除 legacy：斷言選單僅含 `modern`。
     - 若保留別名：斷言切到 `legacy` 後 `member_tree is modern_tree`。
   - 編寫 Presenter 測試：
     - `on_switch_gui_version("legacy")` 行為等同 `"modern"`（或拋錯，取決於策略）。

2) 新增測試：Tree vs Flat 視覺差異
   - Tree：`show` 包含 `tree`；巢狀可展開。
   - Flat：`show == "headings"`；所有節點無子項。

3) 實作最小變更：
   - View：依 mode 設定 `member_tree.configure(show=...)`；flat 模式渲染前移除 children。
   - Model：`get_display_nodes("flat")` 改為輸出 children=[]；（選配）提供 `full_path`。
   - Presenter：正規化 `legacy -> modern` 或限定版本集合。

4) 通過測試後的重構：
   - 若選擇移除 legacy：
     - 刪除 `_switch_to_legacy_gui()` 未使用分支。
     - 移除 GUI 選單中的 `legacy` 值。
     - 更新文件（v6/v8 文件中 legacy/modern 的描述，標註 v23 起 modern 為唯一介面）。

5) 文件與使用說明：
   - 更新 `docs/development/v6_GUI_view.md`/`v8_GUI_integration.md` 的 GUI 版本切換章節。
   - 新增本文件連結與實作狀態。

---

### 風險與回退策略
- 風險：既有 UI 測試對 `legacy` 的期望需更新；headless CI 下 Treeview `show` 驗證需穩健。
- 回退：保留 `legacy` 作為 modern 別名，先不移除選項，只調整行為；待驗證穩定再移除選項。

---

### 完成定義（DoD）
- 所有新增/調整測試通過（含 headless/CI）。
- Modern 成為預設 UI；Legacy 行為與現況一致或被移除。
- Tree 與 Flat 在 UI 呈現明顯不同：
  - Tree：`show="tree headings"`、可展開巢狀。
  - Flat：`show="headings"`、無子項。
- 文件已更新，並記錄相容性注意事項。

