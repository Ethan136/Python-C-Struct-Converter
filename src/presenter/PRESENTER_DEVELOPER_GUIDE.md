# StructPresenter Developer Guide

本文件說明 `src/presenter/struct_presenter.py` 的主要事件流程、狀態管理、錯誤處理設計，協助開發者維護與擴充 Presenter 層。

## 主要類別
- `StructPresenter`：負責協調 Model 與 View，處理所有 UI 事件與資料流。

## 主要事件流程
- `browse_file`：
  1. 觸發檔案選擇對話框
  2. 載入 .h 檔案內容，呼叫 model 解析
  3. 更新 view 顯示 struct layout、debug、重建 hex grid
- `parse_hex_data`：
  1. 取得 hex 輸入欄位資料
  2. 驗證格式、補零、轉 bytes（呼叫 InputFieldProcessor）
  3. 呼叫 model 解析 hex，顯示解析結果與 debug bytes
  4. 處理長度錯誤、格式錯誤、溢位等例外
- `on_unit_size_change` / `on_endianness_change`：
  - 切換單位/位元組序時，重建 hex grid 或重新解析
- `on_manual_struct_change` / `parse_manual_hex_data`：
  - 處理手動 struct tab 的成員變更、hex 解析、layout 計算
- `on_export_manual_struct`：
  - 匯出手動 struct 為合法 C header 檔案

## 狀態管理
- 由 Presenter 控制 struct layout、hex 輸入、解析結果的資料流
- 根據事件動態更新 view 狀態（如啟用/停用按鈕、清空欄位、顯示錯誤）
- Model 僅負責資料處理，View 僅負責顯示，狀態流由 Presenter 協調

## 錯誤處理設計
- 針對 hex 輸入錯誤、長度錯誤、溢位、檔案讀取錯誤等，皆捕獲例外並顯示 user-friendly 訊息
- 自訂 HexProcessingError 例外類別，細分錯誤型態
- 所有錯誤皆由 Presenter 處理，View 僅負責顯示

## 擴充指引
- 新增事件：於 Presenter 增加對應方法，於 View callback 呼叫
- 擴充資料驗證/轉換：可於 Presenter 增加前置處理，再呼叫 Model
- 支援新功能：建議先設計 Model 處理邏輯，再於 Presenter 增加協調與狀態流
- 若需新增 UI 狀態，建議集中於 Presenter 控制，避免 View/Model 交叉依賴

## 參考
- 主要事件實作：`browse_file`、`parse_hex_data`、`on_unit_size_change`、`on_endianness_change`、`parse_manual_hex_data` 等
- 錯誤處理：`HexProcessingError`、try/except 區塊 