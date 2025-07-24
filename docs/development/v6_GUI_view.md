# v6 GUI for Nested Struct and Union — View（UI/顯示層設計）

## [優先開發] 只需修改 View 的功能

### 1. Treeview/表格欄位設定一致性與共用化  ✅已完成
- 所有 tab（如 file/manual/debug）都統一引用 MEMBER_TREEVIEW_COLUMNS，動態顯示/隱藏欄位時只重建 widget。
- 已完成，並有單元測試驗證欄位一致性。

### 2. UI/UX 細節優化  ✅已完成
- 展開/收合、icon、顏色、[struct]/[union] 標籤的顯示方式。
- Treeview 樹狀結構的顯示細節、樣式、icon、顏色等。
- 已完成，並有測試覆蓋。

### 3. 頁面可嵌入多組顯示元件（多 Treeview/多視窗）  ✅已完成
- UI 支援多組 Treeview，資料來源可共用 context。
- 已完成，支援多組 Treeview 實例，context 可共用或獨立，測試已覆蓋。

### 4. UI callback 綁定、UI 測試查找 widget、處理中禁用互動設計
- callback 綁定、widget 查找已完成。
- 處理中（context["loading"] 或 context["pending_action"]）時，禁用所有互動（如按鈕、Treeview 事件、輸入框等），顯示「處理中...請稍候」提示，結束時恢復。

### 5. 多選節點與批次操作  ✅已完成
- 支援多選節點（selected_nodes），UI/狀態同步。
- 已完成「批次刪除」、「批次展開」、「批次收合」功能，UI 按鈕已補齊，TDD 覆蓋。

### 6. Treeview 拖曳排序  ✅已完成
- 支援同層級節點拖曳排序，callback 與 UI/狀態同步，TDD 覆蓋。

### 7. 欄位排序與自訂顯示  ✅已完成
- 支援用戶自訂欄位順序、顯示/隱藏，context["user_settings"] 控制，測試已覆蓋。

### 8. 搜尋與高亮  ✅已完成
- 支援節點名稱/型別搜尋，context["search"]、["highlighted_nodes"]，UI 高亮同步，測試已覆蓋。

### 9. 新舊 GUI 切換  ✅已完成
- 支援 legacy/modern GUI 切換，context["gui_version"]，資料同步，測試已覆蓋。

### 10. AST 節點唯一性修正  ✅已完成
- AST id 產生方式已修正，Treeview 重建前清空節點，避免 id 重複，文件已記錄。

### 11. 單元測試與 UI 測試  ✅已完成
- 各項功能皆有 TDD 驗證，測試覆蓋 loading、error、readonly、undo/redo、diff/patch 等狀態。

---

## 後續開發建議（2024/07）

- [ ] **debug 面板強化**：顯示 context["debug_info"] 內容、API trace、context 快照，支援自動/手動刷新，補強測試。
- [ ] **處理中禁用互動設計**：僅針對 context["loading"] 或 context["pending_action"] 為 True 時，禁用所有互動，結束時恢復。
- [ ] **View/context 解耦與效能**：context diff/patch 機制優化，只重繪有變動的節點，context version 自動升級/降級與警告。
- [ ] **文件同步**：持續同步 stub/mock、context schema、UI 測試設計原則。

---

## 1. UI 元件設計
- Treeview 樹狀顯示元件，支援 parent-child node 遞迴插入。
- member value、struct layout、debug input raw data 封裝為獨立元件。
- 切換框架（tab、radio button、dropdown），可切換新舊顯示元件。

## 2. UI/UX 細節
- 展開/收合、icon、顏色、[struct]/[union] 標籤。
- 支援欄位資訊分層顯示，提升可讀性。
- 頁面可嵌入多組顯示元件，方便切換與比對。

## 3. View 事件 callback 設計
- on_node_click(node_id)：點擊節點事件。
- on_switch_display_mode(mode)：切換新舊顯示模式。
- on_refresh()：手動刷新顯示。
- 其他互動事件（如展開/收合、hover、右鍵選單等）。

## 4. mock Presenter 實作建議
- View 可用 mock Presenter 提供的 AST node/tree，專注於 UI prototype。
- 可用假資料模擬各種巢狀結構、union、bitfield、array 等情境。

## 5. 單元測試建議
- Treeview 遞迴插入測試。
- 切換框架顯示正確性測試。
- 事件 callback 行為測試。
- UI/UX 一致性與回退測試。 

## 6. Treeview 與元件封裝細節（整併自 v6_GUI_for_nested_struct_and_union.md）
- Treeview parent-child 結構，支援展開/收合、巢狀 struct/union 遞迴插入。
- name 欄位可加註 [struct]/[union] 標籤，或用不同顏色/粗體顯示。
- 切換框架可用 tab、radio button、dropdown 或 toggle button 實作。
- 封裝 member value、struct layout、debug input raw data 為獨立元件，統一 API（如 set_data, get_data, refresh, clear），方便切換時資料同步。
- 頁面可嵌入多組顯示元件，方便切換與比對。
- UI/UX 優化：展開/收合、icon、顏色、[struct]/[union] 標籤。
- 事件 callback 設計：on_node_click, on_switch_display_mode, on_refresh, 其他互動事件（如展開/收合、hover、右鍵選單等）。

### 6.1 Treeview/表格欄位設定一致性與共用化（2024/07 補充）
- **所有 Treeview 欄位結構、標題、寬度、順序，集中定義於單一設定（如 MEMBER_TREEVIEW_COLUMNS）**：
  ```python
  MEMBER_TREEVIEW_COLUMNS = [
      {"name": "name", "title": "欄位名稱", "width": 120},
      {"name": "value", "title": "值", "width": 100},
      {"name": "hex_value", "title": "Hex Value", "width": 100},
      {"name": "hex_raw", "title": "Hex Raw", "width": 150},
  ]
  ```
- **所有 tab（如 file/manual/debug）都只根據這份設定產生 Treeview**，不再於各自 tab 動態設定 heading text。
- **動態顯示/欄位顯示/隱藏時，只重建 widget 並傳入正確 columns，不再動態改 heading text**。
- **這樣可保證 UI/UX 一致、易於維護與擴充**，未來要加欄位、改標題、調寬度，只需改一份設定。
- **測試驗證**：只需驗證同一份欄位設定產生的 Treeview 標題、寬度、順序一致。

## 6. 進階 UI/UX 功能建議

- **搜尋與高亮**：支援節點名稱/型別搜尋，context 增加 `search`、`highlighted_nodes` 欄位，View 根據這些欄位高亮顯示搜尋結果。
- **欄位排序與自訂顯示**：允許用戶自訂欄位順序、顯示/隱藏，對應 context 的 `user_settings`。
- **多選節點**：支援多選，context 增加 `selected_nodes: List[str]`。
- **批次操作**：如展開/收合全部、拖曳排序，對應事件與 context 欄位。
- **debug 面板**：根據 context 的 `debug_info` 顯示最近事件、API trace、context 快照等。

### 欄位排序與自訂顯示（細節規劃 2024/07 補充）

#### 1. user_settings["treeview_columns"] schema 範例
```python
# 儲存於 context["user_settings"]["treeview_columns"]
[
  {"name": "name", "visible": True, "order": 0},
  {"name": "value", "visible": True, "order": 1},
  {"name": "hex_value", "visible": False, "order": 2},
  {"name": "hex_raw", "visible": True, "order": 3}
]
```
- name: 欄位名稱（對應 MEMBER_TREEVIEW_COLUMNS）
- visible: 是否顯示
- order: 顯示順序（數字越小越前面）

#### 2. UI 操作流程
- 右鍵點擊 Treeview 標題列，彈出欄位顯示/隱藏選單（checkbutton 控制 visible）
- 拖曳欄位標題可調整順序（order）
- 設定變動時，View 呼叫 presenter.on_update_user_settings(new_settings)
- 設定會即時套用並儲存於 context["user_settings"]

#### 3. 資料流/事件流
- View 觸發 on_update_user_settings → Presenter 更新 context["user_settings"] → 推送新 context 給 View → View 依據 user_settings 重建 Treeview
- Treeview displaycolumns 依 user_settings 排序與 visible 決定

#### 4. 預設值與 fallback
- 若 user_settings 缺失，使用 MEMBER_TREEVIEW_COLUMNS 預設順序與顯示
- 欄位設定異常時自動回退預設

#### 5. 測試驗證重點
- 切換欄位順序、顯示/隱藏時，Treeview displaycolumns 正確
- user_settings 儲存/還原正確
- 預設值 fallback 行為正確
- 欄位設定異常時不會造成 UI crash

#### 6. 其他建議
- 欄位順序/顯示設定可考慮持久化（如寫入本地設定檔）
- 欄位寬度、顏色等進階設定可後續擴充

---

## 7. View 測試與 mock 建議

- 每個 UI 元件（Treeview、debug 面板、切換框架）都需有單元測試，覆蓋 loading、error、readonly、undo/redo 等狀態。
- 使用 mock Presenter 模擬各種 context 狀態，驗證 UI 行為。
- 建議測試 context diff/patch 機制，確保只重繪有變動的部分。
- 測試用例建議：
    - 搜尋/高亮時節點正確顯示。
    - 切換顯示模式時 UI 正確切換。
    - 展開/收合全部、批次操作正確反映在 UI。
    - debug 面板能正確顯示 debug_info 內容。

---

## 8. View 與 context 解耦

- View 僅根據 context 重繪，不直接依賴 Presenter 內部狀態。
- 建議設計 context diff/patch 機制，提升效能。
- View 可根據 context version 決定是否需要自動升級/降級 context 結構。
- 若 context 結構不符，View 應顯示警告或請求 Presenter 重送 context。 

## 9. Codebase 對齊狀態

- View 端所有 callback、context 欄位、mock/stub、readonly/error/debug 狀態皆有單元測試覆蓋。
- contract test 路徑：`tests/presenter/test_v2p_contract.py`
- context schema 驗證路徑：`src/presenter/context_schema.py`
- 若有 API/欄位/事件異動，請先更新本文件並同步調整 codebase 與測試。 

## 10. 測試與開發注意事項（2024/07 補充）

### 10.1 tkinter callback 綁定原則
- 所有 tkinter 控制元件（如 OptionMenu、Entry、Button 等）的 callback 必須在 View class 內明確定義，避免動態注入或 class 外 patch。
- 綁定時機需在元件建立後立即完成，確保事件能正確觸發。

### 10.2 context 欄位型別規範
- context 欄位（如 selected_nodes、highlighted_nodes、expanded_nodes）必須為 list/str/None 等明確型別，嚴禁傳入 MagicMock、物件或其他非預期型別。
- Treeview.selection_set、tag 設定等需傳入正確型別，否則 tkinter 會報 TclError。

### 10.3 測試 presenter/context 實作原則
- 測試用 presenter/context 應用 stub/mock class，context 為 dict，get() 回傳正確型別。
- 嚴禁直接用 MagicMock 當 dict，避免型別污染導致 UI 渲染錯誤。
- 測試 presenter 應明確實作互動方法（如 on_search、on_expand_all 等），並記錄呼叫。

### 10.4 測試與 UI 初始化注意事項
- 測試需確保 UI 元件（tab/frame/Treeview）已建立再進行互動驗證。
- headless/CI 環境下，tkinter widget 的 focus/可見性驗證可降級為存在性檢查。
- 測試需考慮 patch tkinter 內建方法（如 messagebox、after/after_cancel）以避免副作用。

### 10.5 建議
- 開發與測試時，嚴格遵循上述規範，確保 UI/互動穩定、可維護，並利於 CI/CD 自動化驗證。 

## [2024-07-08] 測試與開發規範補充

### 1. Presenter/Context 型別規範
- 所有測試用 presenter/context 必須型別正確，不能用 MagicMock 當 dict，context 欄位必須為 str/list/None 等 tkinter 支援型別。
- 測試用 PresenterStub 應集中定義於一處（如 tests/conftest.py 或 presenter_stubs.py），所有測試引用同一份，避免遺漏 method。

### 2. UI 測試查找與驗證建議
- UI 測試查找 widget 時，建議用 widget name、tag 或 view 提供的 getter/helper，避免直接遍歷 widget tree。
- selectmode 驗證建議用 str(tree.cget("selectmode")) == "extended"。
- Treeview selection 驗證時，context["selected_node"]、["selected_nodes"] 必須與實際插入 id 一致。

### 3. Treeview 禁用/唯讀設計
- ttk.Treeview 不支援 state 屬性，不能用 state="disabled"。如需禁用互動，應用 unbind、覆寫 handler 或 ignore event。
- 測試驗證禁用時，應檢查互動 handler 是否被移除或覆寫，而非驗證 state。

### 4. 文件同步與 CI
- 文件需同步規範 stub/mock、context schema、UI 測試設計原則。
- 建議 CI 加入型別檢查、lint、pytest-cov 等，確保 stub/mock/型別一致性。 

---

## [2024-12-19] 新舊 GUI 切換選單設計規劃

### 1. 設計目標
- **新舊 GUI 並存**：提供用戶在「舊版平面顯示」與「新版樹狀顯示」之間切換的能力
- **資料同步**：切換時確保 struct 資料、解析結果、context 狀態完全同步
- **漸進式升級**：用戶可隨時回退到舊版，確保功能不中斷
- **基本樹狀顯示**：支援巢狀 struct/union 的基本樹狀顯示功能

### 2. UI 元件設計

#### 2.1 切換選單位置與樣式
```python
# 在主視窗頂部新增切換選單
GUI_VERSION_OPTIONS = [
    {"value": "legacy", "label": "舊版 GUI (平面顯示)", "description": "傳統平面表格顯示"},
    {"value": "modern", "label": "新版 GUI (樹狀顯示)", "description": "樹狀巢狀結構顯示"}
]

# 切換選單元件
self.gui_version_var = tk.StringVar(value="legacy")
self.gui_version_menu = ttk.OptionMenu(
    self, 
    self.gui_version_var, 
    "legacy", 
    *[opt["value"] for opt in GUI_VERSION_OPTIONS],
    command=self._on_gui_version_change
)
```

#### 2.2 簡化的顯示切換機制
```python
def _on_gui_version_change(self, version):
    """處理 GUI 版本切換"""
    if self.presenter and hasattr(self.presenter, "on_switch_gui_version"):
        # 通知 presenter 切換 GUI 版本
        self.presenter.on_switch_gui_version(version)
    
    # 更新 context
    self.context["gui_version"] = version
    
    # 切換顯示模式
    if version == "modern":
        self._switch_to_modern_gui()
    else:  # legacy
        self._switch_to_legacy_gui()

def _switch_to_legacy_gui(self):
    """切換到舊版平面顯示"""
    # 隱藏新版元件，顯示舊版元件
    if hasattr(self, "modern_frame"):
        self.modern_frame.pack_forget()
    if hasattr(self, "member_tree"):
        self.member_tree.pack(fill="x")

def _switch_to_modern_gui(self):
    """切換到新版樹狀顯示"""
    # 隱藏舊版元件，顯示新版元件
    if hasattr(self, "member_tree"):
        self.member_tree.pack_forget()
    if hasattr(self, "modern_frame"):
        self.modern_frame.pack(fill="both", expand=True)
    else:
        self._create_modern_gui()

def _create_modern_gui(self):
    """建立新版樹狀顯示 GUI"""
    self.modern_frame = tk.Frame(self.tab_file)
    
    # 建立樹狀 Treeview
    self.modern_tree = ttk.Treeview(
        self.modern_frame,
        columns=("name", "type", "value", "offset", "size"),
        show="tree headings",
        height=10
    )
    self.modern_tree.heading("name", text="欄位名稱")
    self.modern_tree.heading("type", text="型別")
    self.modern_tree.heading("value", text="值")
    self.modern_tree.heading("offset", text="Offset")
    self.modern_tree.heading("size", text="Size")
    self.modern_tree.pack(fill="both", expand=True)
    
    # 綁定展開/收合事件
    self.modern_tree.bind("<<TreeviewOpen>>", self._on_modern_tree_open)
    self.modern_tree.bind("<<TreeviewClose>>", self._on_modern_tree_close)
```

### 3. 新版 GUI 基本功能

#### 3.1 樹狀巢狀顯示
- **巢狀 struct/union 展開**：支援多層級結構展開
- **[struct]/[union] 標籤**：清楚標示節點類型
- **基本 icon**：不同類型節點使用不同 icon
- **展開/收合**：支援節點展開與收合

#### 3.2 基本搜尋
- **簡單搜尋**：支援節點名稱搜尋
- **高亮顯示**：搜尋結果高亮顯示

### 4. Context 擴充
```python
# 在 context schema 中新增
"gui_version": {"type": "string", "enum": ["legacy", "modern", "v7"]}
```

### 5. 實作步驟（按照策略文件）

#### 5.1 AST 結構傳遞
- 確認 parser/model 能回傳巢狀 AST 結構

#### 5.2 Treeview 遞迴插入
- 實作遞迴插入函式，將 AST 轉為 Treeview node

#### 5.3 GUI prototype
- 新增切換選單，支援新舊顯示切換

#### 5.4 優化顯示
- 加上 icon、顏色、[struct]/[union] 標籤

#### 5.5 保留現有 GUI
- 提供選單切換新舊頁面

### 6. 基本測試

#### 6.1 切換機制測試
```python
def test_gui_version_switch(self):
    """測試 GUI 版本切換"""
    # 測試切換選單存在
    self.assertIsNotNone(self.view.gui_version_var)
    
    # 測試切換到新版
    self.view._on_gui_version_change("modern")
    self.assertEqual(self.presenter.context["gui_version"], "modern")
    
    # 測試切換到舊版
    self.view._on_gui_version_change("legacy")
    self.assertEqual(self.presenter.context["gui_version"], "legacy")
```

#### 6.2 樹狀顯示測試
```python
def test_modern_treeview_display(self):
    """測試新版樹狀顯示"""
    # 切換到新版
    self.view._on_gui_version_change("modern")
    
    # 驗證樹狀元件存在
    self.assertIsNotNone(self.view.modern_tree)
    
    # 驗證基本功能
    self.assertTrue(hasattr(self.view, "_on_modern_tree_open"))
    self.assertTrue(hasattr(self.view, "_on_modern_tree_close"))
```

### 7. 注意事項

#### 7.1 資料同步
- **切換時資料同步**：確保切換 GUI 版本時，struct 資料完全同步
- **context 相容**：確保新舊 GUI 都能正確處理 context 結構

#### 7.2 回退機制
- **錯誤處理**：切換失敗時提供明確的錯誤訊息
- **回退機制**：新機制有 bug 可隨時切回舊顯示

### 8. 符合策略文件的範圍

- ✅ **新舊 GUI 並存**：符合「新舊顯示機制並存，切換框架可隨時回退」
- ✅ **基本樹狀顯示**：符合「支援巢狀 struct/union 樹狀顯示」
- ✅ **資料同步**：符合「切換新舊顯示時，資料 context 必須同步」
- ✅ **簡單實作**：符合策略文件的 6 個簡單開發步驟
- ✅ **worktree 對應**：符合「gui_switch_container：設計切換容器，實作新舊顯示切換」 

## [2024-07-09] AST/Treeview 節點唯一性修正規劃

### 問題描述
- 切換新版 GUI 或多次載入 struct/解析資料時，Treeview 會出現 `_tkinter.TclError: Item ... already exists` 錯誤。
- 這是因為 Treeview 的 `iid`（節點 id）重複插入，通常是 AST 結構產生的 id 沒有全域唯一，或 UI 重建時未正確清空舊節點。

### 主要原因
- AST 產生時，巢狀 struct/union/member 的 id 只用 name 或 parent.name 拼接，若多次載入或有同名巢狀結構，id 會重複。
- Treeview 在 update_display/show_treeview_nodes 時，若未先清空所有節點，重複插入同 id 會報錯。

### 修正方案
1. **AST 產生時保證 id 全域唯一**
    - id 可用 parent id + name 或加上 uuid，確保每個節點唯一。
    - ast_to_dict 遞迴時，prefix 應包含完整路徑或隨機 uuid。
2. **Treeview 重建前先清空所有節點**
    - 在 show_treeview_nodes 或 insert_with_highlight 前，呼叫 tree.delete(*tree.get_children())。
    - 確保每次重建不會殘留舊節點。
3. **（可選）Treeview 支援同名節點時自動加序號/uuid**
    - 若同一層有多個同名節點，id 可加序號或 uuid。

### 修正步驟
- [ ] 1. 修改 ast_to_dict，id 產生方式改為 parent_id + name 或加 uuid，保證唯一。
- [ ] 2. 修改 show_treeview_nodes，重建前先清空所有節點。
- [ ] 3. 測試多次載入/切換/解析 struct，Treeview 不再出現 id 重複錯誤。
- [ ] 4. 文件同步修正規範與測試建議。

### 參考
- [Tkinter Treeview 官方文件](https://docs.python.org/3/library/tkinter.ttk.html#treeview)
- [Python uuid 官方文件](https://docs.python.org/3/library/uuid.html) 

## [2024-07-09] 新版 GUI struct member value 顯示為空的排查規劃

### 問題描述
- 新版 GUI（modern Treeview）struct member value 欄位顯示都是空的。

### 排查思路
1. **確認 parse_hex_data 是否有正確寫入 self.member_values**
    - 目前 parse_hex_data 會將 {name: value} 寫入 self.member_values。
    - 需確認所有 struct member（包含巢狀）都正確寫入。
2. **確認 get_display_nodes 是否正確帶出 value**
    - to_treeview_node 用 value_map.get(node["name"], "") 取值。
    - 若 AST 巢狀結構有同名成員，或 id/name 不一致，會導致 value 對不到。
3. **確認新版 GUI Treeview 是否有正確顯示 value 欄位**
    - Treeview columns 有 value 欄位，這部分沒問題。
4. **確認 value 的 key 是否與 AST node 的 name 對應**
    - 若 value_map 的 key 只是 name，巢狀結構時會對不到正確的 value。

### 主要懷疑
- AST node 的 name 可能不是唯一，巢狀結構時 value_map.get(node["name"]) 會對不到正確的 value。
- 解析出來的 value 只對應到最外層 struct，巢狀 struct/union 的 value 沒有被正確寫入。

### 下一步建議
1. **確認 parse_hex_data 產生的 member_values key/value 是否正確，並與 AST node name 對應。**
2. **如有巢狀 struct，需考慮用完整路徑（如 parent.name.child）作為 key。**
3. **可在 get_display_nodes/to_treeview_node 加 debug print，檢查 value_map 和 node["name"] 的對應關係。**

### 備註
- 若 struct 為巢狀結構，建議 value_map 的 key 應改為完整路徑或 AST id，避免同名成員覆蓋。
- 若只有平面 struct 也出現 value 空白，需檢查解析流程與 UI 顯示流程。 
