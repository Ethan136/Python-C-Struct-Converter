# StructView GUI Developer Guide

本文件說明 `src/view/struct_view.py` 的主要 GUI 元件、事件流程與擴充方式，協助開發者維護與擴充 GUI。

## 主要類別
- `StructView(tk.Tk)`: 主視窗類別，包含所有 GUI 元件與事件 callback。

## 主要元件結構
- **Tab 控制**：
  - `.H檔載入` Tab：支援載入 C/C++ struct header 檔案，顯示 struct layout、hex 輸入、解析結果。
  - `手動 struct 定義` Tab：支援手動建立 struct，動態新增/刪除成員，顯示 layout 與解析。
- **成員表格**：Treeview 顯示 struct 成員名稱、型別、offset、size、bitfield 等資訊。
- **Hex 輸入區**：依 struct 大小與單位自動產生多個 Entry 欄位，支援 chunked 輸入。
- **Debug/解析結果區**：Text/Treeview 顯示原始 bytes、解析值、layout 對應。

## 主要事件 callback
- `_on_browse_file`：選擇 .h 檔案，觸發 presenter 載入與 layout 顯示。
- `_on_parse_file`：解析 hex 輸入，顯示 struct 成員值。
- `_on_unit_size_change` / `_on_endianness_change`：切換單位/位元組序，重建 hex grid 或重新解析。
- `_add_member` / `_delete_member` / `_update_member_*`：手動 struct 成員增刪改。
- `on_export_manual_struct`：匯出手動 struct 為 .h 檔。
- `_on_parse_manual_hex`：解析手動 struct 的 hex 輸入。

## UI 流程簡述
1. 使用者選擇 .h 檔案 → presenter 載入 struct → 顯示 layout → 產生 hex 輸入欄位
2. 使用者輸入 hex → 按下解析 → presenter 處理 → 顯示解析結果與 debug bytes
3. 手動 struct tab：動態增刪成員、設定 struct 名稱/大小 → 產生 layout 與 hex 輸入欄位
4. 匯出手動 struct → 產生合法 C header 檔案內容

## 擴充指引
- 新增 UI 元件：於對應 tab/frame 增加 tkinter 控制項，並於 callback 中處理事件
- 擴充事件：於 presenter 增加對應方法，並在 view callback 中呼叫
- 調整 layout：可修改 Treeview 欄位、Entry 欄位產生邏輯
- 支援新功能：建議先於 presenter/model 增加邏輯，再於 view 增加 UI 與事件

## Cache 觸發與效能優化
- 主要觸發點：_add_member、_delete_member、_update_member_*、_move_member_up/down、_copy_member、_reset_manual_struct。
- 這些操作皆會呼叫 presenter.invalidate_cache()，確保 layout cache 失效。
- 依賴介面：presenter 必須實作 invalidate_cache、compute_member_layout。
- TDD 測試：所有觸發點、cache 行為、異常情境皆有自動化測試（見 tests/test_struct_view.py）。

## 參考
- 主要元件初始化：`StructView.__init__`、`_create_tab_control`、`_create_file_tab_frame`、`_create_manual_struct_frame`
- 事件 callback 實作：`_on_browse_file`、`_on_parse_file`、`_on_unit_size_change`、`_on_endianness_change`、`_add_member`、`_on_parse_manual_hex` 等 