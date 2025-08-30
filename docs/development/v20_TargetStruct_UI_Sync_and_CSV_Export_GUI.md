## v20 Target Struct 切換後 UI 同步 + CSV 匯出 GUI 整合

### 目標
- 修正：切換 Target Struct 後，Struct Layout 與 Hex 輸入格未同步更新的問題。
- 整合：將 v19 的 CSV 匯出能力導入 GUI（匯入 .h 頁籤），支援一鍵匯出欄位定義與（可選）值。

---

### 問題描述（Target Struct UI 同步）
- 現象：同一份 .h 有多個頂層 `struct/union` 時，使用者在「Target Struct」下拉切換後，UI 只更新 TreeView 節點，未更新 Struct Layout 與 Hex Grid。
- 影響：
  - Layout 面板顯示上個選擇的欄位與大小，與當前 root 不一致。
  - Hex 輸入格數量依舊沿用舊的 `total_size`，導致解析長度不符。

#### 根因
- Presenter 與 Model 在 `set_import_target_struct(name)` 已正確重算 `layout/total_size`；
- View 的 `_on_target_struct_change` 僅 `update_display(...)`，未同步呼叫 `show_struct_layout(...)` 與 `rebuild_hex_grid(...)`。

#### 修正
- 檔案：`src/view/struct_view.py`
- 函式：`_on_target_struct_change`
- 新增：
  - 由 `presenter.model` 取 `struct_name/layout/total_size/struct_align`；
  - 呼叫 `show_struct_layout(...)` 更新 UI；
  - 設定 `current_file_total_size = total_size`，依目前 unit size `rebuild_hex_grid(total_size, unit_size)`。

---

### CSV 匯出 GUI 整合（來自 v19 功能）

#### 背景
- v19 引入 `DefaultCsvExportService` 與 `CsvExportOptions`，可將解析結果與（可選）欄位值輸出為 CSV。
- v20 將該能力整合進 GUI 匯入 .h 頁籤。

#### 使用者流程（GUI）
1) 成功載入/切換到某個 Target Struct 後，Layout 成功顯示時，「匯出 CSV」按鈕會啟用。
2) 按下「匯出 CSV」：
   - 彈出檔案儲存對話框以選擇輸出路徑。
   - 由 `presenter.model` 組裝 parsed model（`build_parsed_model_from_struct`）。
   - 擷取目前 Hex 輸入（若有）與端序設定（Little/Big Endian），交由 `DefaultCsvExportService` 計算欄位值。
   - 輸出 CSV，顯示完成訊息（包含筆數與耗時）。

#### 實作重點
- 檔案：`src/view/struct_view.py`
- 變更：
  - 新增匯出按鈕 `export_csv_button`（初始 disabled）。
  - `show_struct_layout(...)` 成功後啟用按鈕；`clear_results()` 時關閉按鈕。
  - 新增 `_on_export_csv()`：
    - 以 `build_parsed_model_from_struct(self.presenter.model)` 建構資料；
    - 蒐集 `get_hex_input_parts()` 與 `get_selected_endianness()`；
    - 呼叫 `DefaultCsvExportService().export_to_csv(parsed_model, {"type":"file","path":...}, CsvExportOptions(...))`。

#### 預設匯出選項（可擴充為 UI）
- `include_header=True`
- `include_layout=True`
- `include_values=True`
- `endianness`: 來自 GUI 選擇（預設 Little）
- `hex_input`: 由 Hex Grid 輸入組成（無輸入時自動略過值計算）

---

### 測試計畫

#### 1) View：Target Struct 同步
- 新增測試：`test_struct_view_target_struct_updates_layout_and_hex_grid`
  - 匯入含多個頂層聚合的 .h；切換 Target Struct；
  - 斷言：`show_struct_layout` 被觸發（可透過 UI 狀態或 Spy）、Hex Grid 以新 `total_size` 重建。
  - 標註 `pytest.mark.skipif(not os.environ.get('DISPLAY'))` 以避免 headless CI 失敗。

#### 2) View：CSV 匯出按鈕與匯出流程
- 新增測試：`test_struct_view_export_csv_button_and_flow`
  - 完成載入並呼叫 `show_struct_layout(...)` 後，檢查 `export_csv_button` 由 disabled 轉為 enabled。
  - monkeypatch `filedialog.asksaveasfilename` 回傳臨時檔路徑；呼叫 `_on_export_csv()`；
  - 斷言檔案存在且非空。
  - 同樣以 `DISPLAY` 條件跳過。

#### 3) Service/Adapter（既有）
- `tests/export/` 既有對 `CsvRowSerializer`、`DefaultCsvExportService`、`build_parsed_model_from_struct` 的測試維持不動。

---

### 風險與相容性
- View 邏輯增補，對 Presenter/Model API 無破壞性；低風險。
- `_on_export_csv` 以 try/except 包覆 GUI 依賴，對 headless 執行不造成例外（測試以 skip 控制）。

---

### 驗收標準
- 切換 Target Struct 後，TreeView/Struct Layout/Hex Grid 三者內容一致。
- 匯出 CSV 能產生檔案；在有 Hex 輸入與端序設定時可計算 `value` 與 `hex_raw` 欄位。

---

### 後續（v20+）
- 將「上下文切換後 UI 同步」抽為共用 helper 以便重用。
- 於 GUI 提供 CSV 選項面板（自訂 delimiter、columns、BOM、排序等）。
