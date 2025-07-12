# View Layer 說明文件

本目錄包含 C++ Struct 解析工具的 View 層，負責所有使用者介面與顯示邏輯。

## 檔案說明

### struct_view.py
- **用途**：
  - 提供 StructView 類別，負責建立 Tkinter GUI，顯示 struct 佈局、輸入欄位、解析結果。
- **執行機制**：
  - 初始化時建立檔案選擇、struct 資訊、hex 輸入、結果顯示等元件。
  - 透過 presenter 物件處理使用者互動（如檔案選擇、解析按鈕）。
  - 顯示解析結果、錯誤訊息、debug 資訊。
- **與其他模組關聯**：
  - 由 Presenter 控制，僅負責顯示與事件委派。
  - 透過 get_string 取得國際化字串。

## GUI 顯示行為（2024/07 更新）

- 手動 struct 設定頁面（tab）**只顯示下方標準 struct layout（ttk.Treeview）**，即時顯示所有成員、padding、offset，完全對齊 C++ 標準。
- 原本的自訂 memory layout 表格已移除。
- 此行為已通過自動化測試驗證（見 tests/test_struct_view_padding.py）。

## 相關設計文檔
- [MVP 架構說明](../../docs/architecture/MVP_ARCHITECTURE_COMPLETE.md) 