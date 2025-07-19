# v6 GUI for Nested Struct and Union — View（UI/顯示層設計）

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

## 6. 進階 UI/UX 功能建議

- **搜尋與高亮**：支援節點名稱/型別搜尋，context 增加 `search`、`highlighted_nodes` 欄位，View 根據這些欄位高亮顯示搜尋結果。
- **欄位排序與自訂顯示**：允許用戶自訂欄位順序、顯示/隱藏，對應 context 的 `user_settings`。
- **多選節點**：支援多選，context 增加 `selected_nodes: List[str]`。
- **批次操作**：如展開/收合全部、拖曳排序，對應事件與 context 欄位。
- **debug 面板**：根據 context 的 `debug_info` 顯示最近事件、API trace、context 快照等。

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

## 9. Treeview 遞迴顯示與互動設計規劃（2024/07）

### 9.1 目標
- Treeview 元件支援巢狀 parent-child node 遞迴插入，完整顯示 struct/union/array/bitfield 等複雜結構。
- 支援展開/收合、節點點擊、[struct]/[union] 標籤、icon、顏色等互動與視覺效果。
- UI/UX 一致，便於後續擴充搜尋/高亮、多選、批次操作等功能。

### 9.2 Treeview 元件設計
- 採用 tkinter.ttk.Treeview，遞迴插入 parent/child node。
- 每個節點顯示：
  - 名稱（name）
  - 型別（type）
  - [struct]/[union] 標籤（label 或 icon）
  - 顏色/粗體區分 struct/union/bitfield
- 支援展開/收合（點擊 icon 或節點）
- 支援節點點擊事件（on_node_click）
- 支援展開/收合事件（on_expand/on_collapse）
- 支援 context 狀態同步（expanded_nodes、selected_node 等）

### 9.3 主要開發步驟
1. **Treeview 遞迴插入**
   - 實作遞迴函式，根據 AST/Treeview node 結構插入 parent/child node。
   - 節點 id 與 context.expanded_nodes/selected_node 綁定。
2. **展開/收合互動**
   - 綁定展開/收合事件，更新 context.expanded_nodes 並推送給 Presenter。
   - UI 上同步顯示展開/收合狀態。
3. **節點點擊互動**
   - 綁定節點點擊事件，更新 context.selected_node 並推送給 Presenter。
   - UI 上高亮顯示選取節點。
4. **[struct]/[union] 標籤與 icon/顏色**
   - 根據 node.type/is_struct/is_union 設定 label、icon、顏色。
   - 可用不同顏色/粗體/圖示區分 struct/union/bitfield。
5. **context 狀態同步**
   - Treeview 根據 context.expanded_nodes/selected_node 自動展開/高亮。
   - 支援 context diff/patch（可先 mock）。
6. **單元測試與 mock**
   - 測試遞迴插入、展開/收合、點擊、context 狀態同步。
   - 使用 mock Presenter/View 驗證資料流與互動。

### 9.4 擴充建議
- 預留搜尋/高亮、多選、批次操作、右鍵選單等擴充點。
- Treeview node 結構支援 version/extra 欄位，便於未來擴充。

--- 

### 9.5 Treeview 遞迴插入演算法與範例
- 遞迴函式設計：
  ```python
  def insert_treeview_node(tree, parent_id, node):
      # node: dict, 需包含 id, label, type, children, icon, extra
      item_id = tree.insert(parent_id, 'end', iid=node['id'], text=node['label'], values=(...), image=icon_map.get(node['icon']))
      for child in node.get('children', []):
          insert_treeview_node(tree, item_id, child)
  # 用法：insert_treeview_node(tree, '', root_node)
  ```
- parent_id 為空字串時代表 root。
- 可根據 node['type'] 決定 label 樣式、icon、顏色。

### 9.6 事件綁定與 context callback 範例
- 綁定展開/收合事件：
  ```python
  def on_treeview_open(event):
      item_id = event.widget.focus()
      presenter.on_expand(item_id)
  def on_treeview_close(event):
      item_id = event.widget.focus()
      presenter.on_collapse(item_id)
  tree.bind('<<TreeviewOpen>>', on_treeview_open)
  tree.bind('<<TreeviewClose>>', on_treeview_close)
  ```
- 綁定節點點擊事件：
  ```python
  def on_treeview_select(event):
      selected = event.widget.selection()
      if selected:
          presenter.on_node_click(selected[0])
  tree.bind('<<TreeviewSelect>>', on_treeview_select)
  ```
- context 狀態同步：
  - 展開/收合時，根據 context.expanded_nodes 自動展開/收合對應節點。
  - 節點選取時，根據 context.selected_node 高亮顯示。

### 9.7 UI/UX 細節建議
- [struct]/[union] 標籤：
  - label 文字加上 [struct] 或 [union]，或用不同 icon。
  - struct 節點可用藍色、union 用綠色，bitfield 用橘色。
- 高亮顯示：
  - 選取節點用粗體/背景色高亮。
  - 搜尋/高亮可用黃色底色。
- icon 設計：
  - 可用小圖示區分 struct/union/bitfield/array。
  - icon_map 可用 pillow/tkinter.PhotoImage 預載。
- 欄位順序與顯示：
  - name/type/offset/size/bitfield 等欄位可自訂顯示順序。

### 9.8 context 狀態同步資料流
- View 觸發事件（展開/收合/點擊）→ 呼叫 Presenter 對應方法（on_expand/on_collapse/on_node_click）→ Presenter 更新 context 並推送給 View → View 根據 context 重繪 Treeview 狀態。
- 範例資料流：
  ```python
  # View
  tree.bind('<<TreeviewOpen>>', lambda e: presenter.on_expand(tree.focus()))
  # Presenter
  def on_expand(self, node_id):
      if node_id not in self.context['expanded_nodes']:
          self.context['expanded_nodes'].append(node_id)
      self.push_context()
  # View
  def update_display(self, nodes, context):
      # 根據 context.expanded_nodes 展開對應節點
      for node_id in context['expanded_nodes']:
          tree.item(node_id, open=True)
      # 根據 context.selected_node 高亮
      tree.selection_set(context['selected_node'])
  ```

### 9.9 單元測試與擴充建議
- 單元測試重點：
  - 遞迴插入正確性（巢狀結構完整顯示）
  - 展開/收合事件正確推送 context
  - 點擊節點正確更新 context.selected_node
  - context 狀態同步時 UI 正確反映
- 擴充建議：
  - 搜尋/高亮：context 增加 search/highlighted_nodes，View 根據 context 高亮顯示
  - 多選/批次操作：context 增加 selected_nodes，View 支援多選
  - 右鍵選單/自訂操作：Treeview 綁定右鍵事件，彈出 context menu
  - context diff/patch：僅重繪有變動的節點，提升效能 