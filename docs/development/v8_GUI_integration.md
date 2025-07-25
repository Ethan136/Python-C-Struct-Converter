# v8 GUI Integration Plan

## 背景
- 目前 GUI 的 "手動匯入 .H" tab 可切換 legacy、modern、v7 三種介面。
- v7 與 modern 版面相同，差異僅在 v7 透過 `VirtualTreeview` 支援大量節點虛擬化，並加入快捷鍵與右鍵選單。
- `StructView._switch_to_v7_gui()` 內僅呼叫 `_switch_to_modern_gui()`，顯示兩者可共用布局。
- `StructViewV7` 繼承自 `StructView`，額外掛載虛擬化與操作邏輯。

## 建議
1. **合併介面**：在 modern 介面中預設啟用（或提供開關）虛擬化與快捷鍵，讓使用者不需再選擇 v7。
2. **整併測試**：將 `test_struct_view_v7.py` 的案例併入 `test_struct_view.py`，以參數或 fixture 控制虛擬化情境。
3. **簡化選單**：OptionMenu 僅保留 legacy 與 modern（整合後），或將 v7 視為 modern 的別名。

## 實作步驟
- 將 `StructViewV7` 的虛擬化、快捷鍵、右鍵選單邏輯併入 `StructView`。
- 移除或標記 `StructViewV7` 為相容層，避免重複維護。
- 更新 `StructView._switch_to_modern_gui()`，直接建立 `VirtualTreeview` 並綁定相關事件。
- 重構測試，確保虛擬化與一般情況都被覆蓋。
- 更新文件與使用說明，讓使用者了解 v7 功能已整合至 modern。

## 詳細實作
以下列出需調整的檔案與重點內容：
1. **`src/view/struct_view.py`**
   - 在 `__init__` 新增 `enable_virtual` 及 `virtual_page_size` 參數，預設開啟虛擬化。
     `virtual_page_size` 建議 50~200 之間，可依結構大小調整。
     若舊程式仍使用 `StructViewV7`，可於 `src/view/__init__.py` 提供別名：
     ```python
     StructViewV7 = StructView  # 向下相容
     ```
   - 匯入 `VirtualTreeview`，新增 `_enable_virtualization()` 將 `modern_tree` 包裝成虛擬樹。
   - 移除 OptionMenu 中的 `v7` 選項，僅保留 `legacy` 與 `modern`。
   - 在 `_switch_to_modern_gui()` 內呼叫 `_enable_virtualization()`，並整合快捷鍵與右鍵選單綁定邏輯。
   - _create_file_tab_frame() 移除 `v7` 項目並更新 GUI 版本選項。
   - 修改 `show_treeview_nodes()` 在啟用虛擬化時呼叫 `VirtualTreeview.set_nodes()`。
   - 新增 `_flatten_nodes()` 協助將節點展平成列表。
   - 在 `_init_presenter_view_binding()` 加入 Ctrl-F/Ctrl-L/Delete/Ctrl-A 快捷鍵。
   - 改寫 `_bind_member_tree_events()` 以支援右鍵選單。
   - 新增 `_show_node_menu()` 與 `_select_all_nodes()` 實作節點操作。

2. **`src/view/struct_view_v7.py`**
   - 改為薄 wrapper 或標記為 deprecated；僅繼承 `StructView` 並傳入 `enable_virtual=True`。
3. **`src/view/__init__.py`**
   - 若移除 `StructViewV7`，需改以 `StructView` 或別名輸出以保持相容。
4. **`tests/view/test_struct_view_v7.py`**
   - 測試案例移入 `test_struct_view.py`，透過 fixture 或參數化驗證虛擬化行為。
5. **相關文件與 README**
   - 更新 GUI 說明，指出 v7 已併入 modern，並調整使用方式。
### 需要改動的函式
- `StructView.__init__`
- `StructView._create_file_tab_frame`
- `StructView._switch_to_modern_gui`
- `StructView._enable_virtualization` *(新增)*
- `StructView.show_treeview_nodes`
- `StructView._flatten_nodes` *(新增)*
- `StructView._init_presenter_view_binding`
- `StructView._bind_member_tree_events`
- `StructView._show_node_menu` *(新增)*
- `StructView._select_all_nodes` *(新增)*
- `StructView._switch_to_v7_gui` (改為呼叫 `_switch_to_modern_gui`)
- `StructViewV7.__init__`
- `StructViewV7._switch_to_v7_gui`
- `view.__init__` 中的 `__all__`
- 測試檔 `test_struct_view_v7.py` (併入 `test_struct_view.py`)

## 測試腳本更新細節

- **整合方式**：刪除 `tests/view/test_struct_view_v7.py`，於
  `tests/view/test_struct_view.py` 新增可參數化的 fixture。
  透過 `@pytest.mark.parametrize("enable_virtual", [False, True])`
  為 `StructView` 建立兩種實例，確保虛擬化開關皆被測試。
- **建立共用 fixture**：

  ```python
  @pytest.fixture(params=[False, True])
  def view(request):
      root = tk.Tk(); root.withdraw()
      v = StructView(presenter=DummyPresenter(),
                     enable_virtual=request.param,
                     virtual_page_size=10)
      yield v
      v.destroy(); root.destroy()
  ```

  所有 GUI 測試均以此 `view` fixture 為基礎，無須在測試中自行切換 GUI 版本。
- **更新執行腳本**：`run_all_tests.py` 僅需執行
  `tests/view/test_struct_view.py`；原先忽略或獨立執行
  `test_struct_view_v7.py` 的邏輯可移除。CI 流程亦應採用相同方式。
- **移除過時檔案**：提交時一併刪除 `test_struct_view_v7.py`，避免混淆。

## 拖曳排序在虛擬化下的實作細節

- **VirtualTreeview 擴充**：
  - 於 `virtual_tree.py` 新增 `get_global_index(iid)`，回傳節點在完整
    清單中的索引。
  - 新增 `reorder_nodes(parent_id, from_idx, to_idx)`，供拖曳時更新
    `self.nodes` 的順序並重新渲染。
- **StructView 介接**：
  - 在 `_on_treeview_drag_start` 透過 `self.virtual.get_global_index()`
    取得被拖曳節點的原始索引。
  - `_on_treeview_drag_release` 以同樣方式取得目標位置索引，呼叫
    `self.virtual.reorder_nodes()` 更新順序後再觸發
    `presenter.on_reorder_nodes()`。
  - 如未啟用虛擬化，維持原有邏輯。
- **狀態同步**：重新渲染時需保留選取與展開狀態，可由
  `VirtualTreeview` 在 `_render()` 內讀取並恢復 `tree.selection()`。
- **測試案例**：加入拖曳相關測試，使用上述 fixture 確認在虛擬化與非虛擬化
  環境皆能正確調整節點順序，並確保 presenter 收到的新順序一致。

## Presenter 與相容性議題
- `presenter.on_reorder_nodes()` 目前尚未實作，整合拖曳排序功能時應在
  `struct_presenter.py` 新增此 callback，以更新內部資料並通知觀察者。
- 現有 `v7_presenter.py` 是否保留需明確規劃，可考慮改為呼叫新版 Presenter
  或標記為 deprecated，避免與整合後介面衝突。
- 移除 `_switch_to_v7_gui()` 後，如程式仍依賴 `context["gui_version"] == "v7"`
  等判斷，需調整或遷移至新的狀態欄位，確保既有流程不受影響。


## 其他考量
- 可提供設定選項以停用虛擬化，避免小型結構額外開銷。
- 確認舊專案或腳本若仍使用 `v7` 名稱，能順利切換到新的整合介面。
- 重新檢視 GUI 相關的 CI 測試腳本，確保整合後流程仍可順利執行。
- 手動定義的 `manual_member_tree` 目前仍使用一般 Treeview，若需大量成員也可考慮套用虛擬化，啟用後須再次驗證動態列編輯、解析與大小顯示功能是否受影響。
- 拖曳排序與展開/收合等既有事件在啟用虛擬化後需再次驗證，必要時調整相應函式。
- 測試整併後，`run_all_tests.py` 及 CI 流程應改以參數化方式驗證 `enable_virtual`
  不同情境。
- README、`GUI_DEVELOPER_GUIDE.md` 與 `PRESENTER_DEVELOPER_GUIDE.md` 需同步更新快捷鍵列表及虛擬化參數範例。

---

本文件彙整前述討論，提出在 v8 階段將 modern 與 v7 介面整合的方向與實作要點，以降低維護成本並提升使用體驗。
