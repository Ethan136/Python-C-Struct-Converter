# run_all_tests.py 使用說明

## 1. 目的

`run_all_tests.py` 是專案的跨平台自動化測試批次腳本，能安全、方便地分開執行 GUI 測試與非 GUI 測試，並彙總所有測試結果。適用於 Windows、macOS、Linux。

## 2. 問題背景

- 由於 Tkinter GUI 測試（如 `tests/test_struct_view.py`）在 headless 或部分作業系統下，與其他測試同時執行時容易造成 segmentation fault 或 pytest crash。
- 傳統 shell/batch 指令在不同平台下語法不一，維護困難。
- 需有一個簡單、一致的方式，讓所有成員與 CI/CD 都能安全執行完整測試。

## 3. 腳本功能

- 先執行所有非 GUI 測試（排除 `tests/test_struct_view.py`）
- 再單獨執行 GUI 測試（只跑 `tests/test_struct_view.py`）
- 彙總兩者結果，任何一個失敗則整體 exit code 為 1
- 跨平台（Windows、macOS、Linux）皆可直接用 `python` 執行

## 4. 執行方式

在專案根目錄下執行：

```bash
python run_all_tests.py
```

- 終端機會顯示每個階段的測試結果與總結。
- 若所有測試通過，exit code 為 0，否則為 1。

## 5. 腳本原理

- 透過 Python `subprocess` 分別呼叫 pytest：
  - `pytest --ignore=tests/test_struct_view.py` 執行非 GUI 測試
  - `pytest tests/test_struct_view.py` 執行 GUI 測試
- 兩者結果彙總，並於終端機顯示通過/失敗訊息。

## 6. 常見問題

- **Q: 沒有安裝 pytest？**
  - 請先安裝 pytest：
    ```bash
    pip install pytest
    ```
- **Q: GUI 測試自動跳過？**
  - 若在無 DISPLAY 環境（如 headless server），`tests/test_struct_view.py` 會自動 skip，不會造成錯誤。
- **Q: 有多個 GUI 測試檔案怎麼辦？**
  - 可修改腳本，將所有 GUI 測試檔案集中 pattern（如 `test_*view.py`），並於腳本中自動尋找。

## 7. 擴充建議

- 如需支援多個 GUI 測試檔案，可將 GUI 測試 pattern 集中，並於腳本中用 glob 自動尋找。
- 可整合至 CI/CD pipeline，確保每次 push/PR 都能自動驗證所有測試。
- 若需更細緻的測試分組，可於腳本中自訂更多測試分類與執行順序。

## 8. 參考
- 專案設計文件：`docs/development/v3_define_struct_input2_design_plan.md`（第10.2節）
- 腳本原始碼：專案根目錄 `run_all_tests.py` 