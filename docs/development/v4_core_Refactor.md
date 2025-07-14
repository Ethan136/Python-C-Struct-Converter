# v4 程式碼精簡計畫

## 目標
- 合併 GUI 中建立十六進位輸入格的重複程式碼
- 初步盤點其他相似邏輯供後續重構

## 背景
`src/view/struct_view.py` 內的 `rebuild_hex_grid` 與 `_rebuild_manual_hex_grid` 兩個方法功能幾乎相同，僅操作的容器與參數來源不同。維持兩份程式易造成維護負擔。

## 計畫
1. 新增私有方法 `_build_hex_grid(frame, entry_list, total_size, unit_size)`，包裝目前建立格子的邏輯。
2. `rebuild_hex_grid` 及 `_rebuild_manual_hex_grid` 分別呼叫此方法，僅負責取得參數。
3. 確認所有現有測試（特別是 `tests/test_struct_view.py` 中有呼叫 `_rebuild_manual_hex_grid` 的部份）皆能通過。
4. show_parsed_values 與 show_manual_parsed_values 兩個方法已共用 _populate_tree 來顯示 Treeview，減少重複邏輯。
5. GUI 內「.H 檔載入」tab 與「手動 struct 定義」tab 的 hex grid、欄位驗證、Treeview 欄位顯示等行為已完全一致，並於 code 以共用方法與 callback 實作（如 _build_hex_grid、_rebuild_manual_hex_grid、_populate_tree）。
6. 欄位驗證（如 hex 輸入長度、合法字元）與 tab 切換時的自動重建 hex grid、Treeview 欄位一致性等細節，皆已於 src/view/struct_view.py 內完善實作。

## TDD 步驟
1. 執行既有測試確保基準狀態（可能因環境無顯示而失敗）。
2. 依照上述計畫實作 `_build_hex_grid`，修改相關呼叫。
3. 重新執行測試確認無新錯誤。
