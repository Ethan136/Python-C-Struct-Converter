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

## 相關設計文檔
- [MVP 架構說明](../../docs/architecture/MVP_ARCHITECTURE_COMPLETE.md) 