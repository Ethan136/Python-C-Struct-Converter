# Presenter Layer 說明文件

本目錄包含 C++ Struct 解析工具的 Presenter 層，負責協調 Model 與 View 的互動與應用邏輯。

## 檔案說明

### struct_presenter.py
- **用途**：
  - 提供 StructPresenter 類別，負責處理使用者事件、驗證輸入、協調 Model 與 View 的資料流。
- **執行機制**：
  - `browse_file` 處理檔案選擇，呼叫 Model 載入 struct，並更新 View。
  - `parse_hex_data` 驗證與轉換使用者輸入，呼叫 Model 解析 hex 資料，並將結果顯示於 View。
  - `on_unit_size_change`、`on_endianness_change` 處理 UI 狀態變更。
- **與其他模組關聯**：
  - 直接呼叫 Model（struct_model.py）進行資料處理。
  - 控制 View（struct_view.py）顯示結果與錯誤訊息。
  - 使用 InputFieldProcessor 處理欄位輸入。

## 相關設計文檔
- [MVP 架構說明](../../docs/architecture/MVP_ARCHITECTURE_COMPLETE.md)
- [Presenter/Model 職責差異](../MODEL_PRESENTER_DIFFERENCES.md) 