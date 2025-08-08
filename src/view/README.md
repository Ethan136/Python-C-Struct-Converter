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

- 手動 struct 設定頁面（tab）僅有單一 struct member value 輸入欄位，無多欄位動態編輯功能，符合早期簡單設計。
- Debug tab 為預設顯示，所有使用者皆可在 tab bar 上看到並檢查 cache、LRU、refresh 等資訊。
- 原本的自訂 memory layout 表格已移除。
- 此行為已通過自動化測試驗證（見 tests/test_struct_view_padding.py）。

## Cache 觸發與效能優化（2024/07）
- 任何 struct 成員或 size 變動（新增、刪除、修改、複製、移動、重設）時，皆會呼叫 presenter.invalidate_cache()，確保 layout cache 正確失效。
- 依賴介面：presenter 必須實作 invalidate_cache、compute_member_layout。
- TDD 驗證：所有觸發點皆有自動化測試（見 tests/test_struct_view.py），確保 cache 行為與 UI 操作同步。

## GUI 整合與虛擬化（v8 更新）

- 舊版 `v7` 介面已完全併入 modern GUI，可透過 `enable_virtual` 參數開關大量節點虛擬化功能。
- `StructView` 預設啟用虛擬化，使用 `VirtualTreeview` 以減少顯示大量節點時的資源消耗。
- `StructViewV7` 僅保留為相容別名，實際等同於 `StructView(enable_virtual=True)`。

## 相關設計文檔
- [MVP 架構說明](../../docs/architecture/MVP_ARCHITECTURE_COMPLETE.md) 