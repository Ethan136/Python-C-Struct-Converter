# v10 TDD 規劃：MyStruct 外部載入 .h 的 Tab 無法切換 4/8 Bytes 單位

## 背景與問題描述
- 在 GUI 的「載入 .H 檔」Tab，使用者可選擇單位大小（`1 Byte`、`4 Bytes`、`8 Bytes`）。
- 實際行為：載入 .h 後，單位切換到 `4 Bytes` 或 `8 Bytes` 時，hex 輸入格未正確重建，呈現為清空或依然像 `1 Byte`。
- 預期行為：切換單位後，hex grid 依結構體總大小與選擇的單位重新切分顯示，最後一格可依剩餘位元組動態縮短。

## 目前根因（已定位）
- `src/view/struct_view.py` 的 `_on_unit_size_change` 使用了不存在的 `self.model.total_size`。View 層沒有 `model` 屬性，導致傳入 `0` 重建 grid，表面上像無法切到 `4/8 Bytes`。
- 正確來源應取自 `presenter.model.total_size` 或在 View 端保存載入後的 `total_size`。

## 修正重點（設計）
- 在 `StructView` 保存載入 .h 後的 `total_size`（如 `self.current_file_total_size`）。
- `_on_browse_file` 成功載入後寫入 `current_file_total_size`，失敗時重置為 `0`。
- `_on_unit_size_change` 改為：優先讀 `self.presenter.model.total_size`；若不可用則回退 `self.current_file_total_size`；最後呼叫 `rebuild_hex_grid(total_size, unit_size)`。

## TDD 測試計畫

### 1. 單元測試：View 端單位切換使用正確的 total_size
- 新增檔案或擴寫：`tests/view/test_struct_view_unit_switch.py`
- 測試案例：
  - 建立 `StructView`（以 patch 跳過 GUI 初始化），注入 `presenter` 與 `presenter.model.total_size = 16`，模擬 `get_selected_unit_size()` 回傳 `4`。
  - 觸發 `_on_unit_size_change()`，驗證 `rebuild_hex_grid(16, 4)` 被呼叫一次。
  - 再測一個回退路徑：移除 `presenter.model` 或其 `total_size`，設定 `view.current_file_total_size = 24`，觸發 `_on_unit_size_change()`，驗證 `rebuild_hex_grid(24, 4)` 被呼叫一次。

範例斷言（示意）：
```python
view.rebuild_hex_grid.assert_called_once_with(16, 4)
```
或回退路徑：
```python
view.rebuild_hex_grid.assert_called_once_with(24, 4)
```

### 2. 整合測試：載入後切換 1/4/8 Bytes 的 hex grid 盒數與最後一格長度
- 位置：`tests/view/test_struct_view.py` 內新增或擴充用例。
- 前置：模擬載入 `.h` 結構（可直接設定 `presenter.model.total_size = 9` 並呼叫 `rebuild_hex_grid(9, 1)`）。
- 步驟與驗證：
  - 切到 `4 Bytes`：`rebuild_hex_grid(9, 4)` 後，`len(view.hex_entries) == 3`，且最後一格期望長度 `2`（剩餘 1 byte → 2 hex chars）。
  - 切到 `8 Bytes`：`rebuild_hex_grid(9, 8)` 後，`len(view.hex_entries) == 2`，且最後一格期望長度 `2`。

可參考既有測試 `test_hex_grid_last_entry_dynamic_length` 的風格擴充。

### 3. Presenter 互動行為不變的驗證
- 位置：`tests/presenter/test_struct_presenter.py`。
- 案例：
  - 當 `model.total_size > 0` 時 `on_unit_size_change()` 回傳非 None 的 `unit_size`。
  - 未載入（`model.total_size == 0`）時回傳 `{"unit_size": None}`。
- 確保 View 的邏輯只在 `unit_size` 非 None 時才重建 grid。

## 驗收條件（Acceptance Criteria）
- 載入 .h 後，在「載入 .H 檔」Tab 切換 `1 Byte`、`4 Bytes`、`8 Bytes`：
  - hex grid 會以對應單位重建，分割盒數正確，最後一格長度符合剩餘位元組數（2 hex chars/byte）。
  - 不會出現切換到 `4/8 Bytes` 時 grid 清空的現象。
- 所有新增與既有相關測試通過。

## 風險與回歸檢查
- 確認 MyStruct 手動 Tab 的單位切換（`manual_unit_size_var`）仍照既有測試邏輯正常。
- 確認 Presenter 的 `parse_hex_data()` 與 debug bytes 不受影響。

## 變更影響範圍
- 僅 `src/view/struct_view.py` 的 View 層邏輯（新增 `current_file_total_size` 與更新 `_on_browse_file`、`_on_unit_size_change`）。
- 測試新增或擴寫 `tests/view/` 與 `tests/presenter/` 對應用例。