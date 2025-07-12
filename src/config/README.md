# Config Layer 說明文件

本目錄包含 C++ Struct 解析工具的設定層，負責應用程式設定與國際化字串管理。

## 檔案說明

### ui_strings.py
- **用途**：
  - 提供載入與查詢 UI 字串的功能，支援多語系與國際化。
- **執行機制**：
  - `load_ui_strings(path)` 讀取 XML 格式的字串檔，載入至全域字典。
  - `get_string(key)` 依 key 取得對應字串，若無則回傳 key。
- **與其他模組關聯**：
  - 於 main.py 啟動時載入，供 View 與 Presenter 取得顯示字串。
  - XML 字串檔（ui_strings.xml）可擴充多語系。

## 相關設計文檔
- [UI 字串重構規劃](../../docs/development/string_refactor_plan.md) 