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