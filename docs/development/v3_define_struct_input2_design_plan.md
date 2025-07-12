## 新功能規劃文件：GUI資料結構輸入方式擴充

### 1. 目標
- 提供使用者在GUI介面上，除了現有的「載入.H檔」外，還能「直接在介面上設定資料結構」。
- 兩種資料結構輸入方式可透過Tab切換。

---

### 2. 功能細節

#### 2.1 Tab切換機制
- 介面上新增Tab元件，分為：
  - 「載入.H檔」Tab（現有功能）
  - 「手動設定資料結構」Tab（新功能）

#### 2.2 手動設定資料結構（新功能）
- 使用者可在GUI上直接設定資料結構，流程如下：

  1. **設定資料結構總大小（size）**
     - 輸入框或下拉選單，讓使用者指定結構體的總bit數或byte數。

  2. **設定Bitfield與對應成員名稱**
     - 動態表格或列表，讓使用者逐一新增bitfield。
     - 每一列包含：
       - bitfield長度（bit數）
       - 對應的struct member名稱
     - 可新增、刪除、調整順序。

  3. **記憶體緊密排列**
     - 由於此模式下不允許padding，所有bitfield會緊密排列，總長度必須等於結構體總大小。
     - 若bitfield總和不等於結構體大小，需提示使用者修正。

#### 2.3 載入.H檔（現有功能保留）
- 保持現有從外部載入C語言.H檔案的機制不變。

---

### 3. 介面設計建議

- Tab元件明顯標示兩種模式。
- 「手動設定資料結構」Tab下，提供：
  - 結構體大小設定區
  - Bitfield設定表格
  - 新增/刪除bitfield按鈕
  - 即時顯示目前bitfield總長度與結構體大小的對比
  - 錯誤提示（如bitfield總長度不符）

---

### 4. 其他注意事項

- 兩種模式下產生的資料結構，後續處理流程應一致。
- 若有需要，可考慮將手動設定的資料結構匯出為.H檔，或直接進行後續轉換。

---

### 5. UI Wireframe（介面線框圖）

#### 5.1 Tab切換主畫面

```
+---------------------------------------------------+
| [載入.H檔] | [手動設定資料結構]                  |
+---------------------------------------------------+
|                                                   |
|  (根據所選Tab顯示對應內容)                        |
|                                                   |
+---------------------------------------------------+
```

#### 5.2 手動設定資料結構Tab內容

```
+---------------------------------------------------+
| 結構體總大小（bits/bytes）：[_________]           |
+---------------------------------------------------+
| Bitfield 設定：                                   |
| +-------+-------------------+----------+          |
| | 長度  | 成員名稱          | 操作     |          |
| +-------+-------------------+----------+          |
| |  8    | version           | 刪除     |          |
| | 16    | id                | 刪除     |          |
| | ...   | ...               | 刪除     |          |
| +-------+-------------------+----------+          |
| [新增Bitfield]                                   |
+---------------------------------------------------+
| Bitfield總長度：24 bits / 結構體大小：24 bits     |
| [提示] Bitfield總長度需等於結構體大小            |
+---------------------------------------------------+
| [儲存] [匯出為.H檔] [重設]                        |
+---------------------------------------------------+
```

#### 5.3 UI設計圖（示意圖）

> 下圖為手動設定資料結構Tab的UI設計示意：

```
+---------------------------------------------------------------+
| [載入.H檔] | [手動設定資料結構]                                |
+---------------------------------------------------------------+
| 結構體總大小： [_____] bits/bytes                             |
+---------------------------------------------------------------+
| Bitfield 設定                                                |
| +-------+-------------------+----------+-------------------+ |
| | #     | 成員名稱          | 長度(bit)| 操作              | |
| +-------+-------------------+----------+-------------------+ |
| | 1     | version           |   8      | [刪除] [上] [下]  | |
| | 2     | id                |   16     | [刪除] [上] [下]  | |
| | ...   | ...               |   ...    | [刪除] [上] [下]  | |
| +-------+-------------------+----------+-------------------+ |
| [新增Bitfield]                                               |
+---------------------------------------------------------------+
| Bitfield總長度：24 bits / 結構體大小：24 bits                 |
| [提示] Bitfield總長度需等於結構體大小                        |
+---------------------------------------------------------------+
| [儲存] [匯出為.H檔] [重設]                                    |
+---------------------------------------------------------------+
```

- 「新增Bitfield」按鈕可在表格下方，點擊後彈出輸入欄位或直接新增一列。
- 操作欄提供「刪除」、「上移」、「下移」功能，方便調整bitfield順序。
- 錯誤提示（如bitfield總長度不符）以紅色文字顯示於提示區。
- 匯出、儲存、重設按鈕置於底部，操作明確。

---

### 6. 流程圖

#### 6.1 手動設定資料結構流程

```
[進入手動設定Tab]
      |
      v
[輸入結構體總大小]
      |
      v
[新增/編輯Bitfield]
      |
      v
[檢查Bitfield總長度是否等於結構體大小]
      |Yes                |No
      |                   |
      v                   v
[允許儲存/匯出]      [顯示錯誤提示，禁止儲存]
```

---

### 7. 技術細節建議

#### 7.1 前端技術建議
- **框架**：建議使用 React、Vue 或 PyQt（若為桌面應用）
- **UI元件**：Tab、表格、動態表單、即時驗證提示
- **狀態管理**：
  - Tab切換狀態
  - 結構體大小與bitfield列表
  - Bitfield總長度即時計算與驗證
- **匯出功能**：
  - 將手動設定的資料結構轉換為C語言struct格式，並可下載為.H檔

#### 7.2 資料結構建議
- 以物件陣列儲存bitfield資訊：
  ```json
  [
    { "name": "version", "length": 8 },
    { "name": "id", "length": 16 }
  ]
  ```
- 結構體大小單獨存放，bitfield總長度需與之比對
- 匯出時自動產生無padding的C struct bitfield語法

#### 7.3 驗證與提示
- Bitfield總長度與結構體大小不符時，顯示錯誤並禁止儲存/匯出
- 成員名稱不可重複，bitfield長度需為正整數

#### 7.4 其他
- 可考慮支援多語系（如中英文切換）
- 若未來需支援更複雜的struct（如巢狀struct），可預留擴充空間

---

如需更進一步的UI設計圖或程式碼範例，請再告知！ 

---

## 8. 實作細節規劃

### 8.1 需要改動的檔案與內容

- **src/view/struct_view.py**
  - 新增/調整 GUI：Tab 切換、手動設定資料結構的 UI、bitfield 設定表格、互動邏輯
- **src/presenter/struct_presenter.py**
  - 新增/調整 Presenter：Tab 切換事件、手動設定資料結構的資料流、驗證、匯出
- **src/model/struct_model.py**
  - 新增/調整 Model：支援手動 bitfield 結構的資料結構、驗證、無 padding 計算、匯出 .h 檔
- **src/model/input_field_processor.py**
  - 如需自訂 bitfield 輸入處理，則需擴充
- 可能需新增/調整 config（如國際化字串）
- **tests/** 相關測試檔案（如 test_struct_view.py、test_struct_model.py 等）
- **docs/development/v3_define_struct_input2_design_plan.md**（設計規格文件，持續同步更新）

### 8.2 需要改動/新增的物件與 function

#### View（struct_view.py）
- 物件/屬性：
  - `self.tab_control`（Tab 控制元件）
  - `self.manual_struct_frame`（手動設定資料結構的 Frame）
  - `self.bitfield_table`（bitfield 設定表格元件）
- function：
  - `_create_tab_control()`：建立 Tab UI
  - `_create_manual_struct_frame()`：建立手動設定資料結構的 UI
  - `get_manual_struct_definition()`：取得手動輸入的 struct 定義
  - `show_manual_struct_validation()`：顯示驗證結果
  - `on_export_manual_struct()`：匯出 .h 檔

#### Presenter（struct_presenter.py）
- 物件/屬性：
  - `self.manual_struct_data`（暫存手動設定的資料結構）
- function：
  - `on_tab_switch()`：Tab 切換事件
  - `on_manual_struct_change()`：手動設定資料結構時的資料流與驗證
  - `on_export_manual_struct()`：呼叫 Model 匯出 .h 檔
  - `validate_manual_struct()`：驗證 bitfield 設定

#### Model（struct_model.py）
- 物件/屬性：
  - `self.manual_struct`（手動設定的 struct 物件）
- function：
  - `set_manual_struct(members, total_size)`：設定手動 struct
  - `validate_manual_struct(members, total_size)`：驗證 bitfield 設定
  - `export_manual_struct_to_h()`：產生 .h 檔內容
  - `calculate_manual_layout(members, total_size)`：無 padding 的 bitfield 記憶體排列

#### 測試
- 新增/擴充單元測試與整合測試，覆蓋：
  - bitfield 設定驗證
  - 無 padding 記憶體排列
  - 匯出 .h 檔格式
  - GUI 互動流程

### 8.3 其他注意事項
- 若現有 GUI 為 Tkinter，Tab 建議用 `ttk.Notebook`
- 若現有 Model 計算有 padding，需為手動模式新增「無 padding」排列邏輯
- 匯出 .h 檔需自動產生正確的 C struct bitfield 語法
- 驗證需即時反饋於 UI，並影響「儲存/匯出」按鈕狀態 

### 8.4 主要 function 介面細節與測試/功能骨架建議

#### View（struct_view.py）

- `def _create_tab_control(self) -> None:`
  - 建立 Tab UI，切換「載入.H檔」與「手動設定資料結構」兩個頁籤。
  - 無參數，無回傳值。
  - 測試：Tab 切換時內容正確顯示。

- `def _create_manual_struct_frame(self) -> None:`
  - 建立手動設定資料結構的 UI（結構體大小、bitfield 表格、操作按鈕）。
  - 無參數，無回傳值。
  - 測試：UI 元件正確渲染，欄位可互動。

- `def get_manual_struct_definition(self) -> dict:`
  - 取得使用者於 UI 輸入的 struct 定義資料。
  - 回傳：dict，格式如 `{ 'total_size': int, 'bitfields': List[{'name': str, 'length': int}] }`
  - 測試：輸入不同資料，回傳內容正確。

- `def show_manual_struct_validation(self, errors: list) -> None:`
  - 顯示驗證錯誤訊息於 UI。
  - 參數：errors（list of str）
  - 測試：錯誤時紅字顯示，正確時顯示通過。

- `def on_export_manual_struct(self) -> None:`
  - 匯出手動設定的 struct 為 .h 檔。
  - 無參數，無回傳值。
  - 測試：匯出內容正確，檔案可下載。

#### Presenter（struct_presenter.py）

- `def on_tab_switch(self, tab_name: str) -> None:`
  - 處理 Tab 切換事件，tab_name 為目前選中的頁籤。
  - 測試：切換時 UI 狀態正確、資料流正確。

- `def on_manual_struct_change(self, struct_data: dict) -> None:`
  - 處理手動 struct 設定變更，進行驗證並更新狀態。
  - 參數：struct_data（dict，格式同 get_manual_struct_definition 回傳）
  - 測試：資料異動時驗證正確、UI 及按鈕狀態正確。

- `def on_export_manual_struct(self) -> None:`
  - 呼叫 Model 匯出 .h 檔，並觸發 View 顯示/下載。
  - 測試：匯出內容正確。

- `def validate_manual_struct(self, struct_data: dict) -> list:`
  - 驗證 bitfield 設定，回傳錯誤訊息 list。
  - 測試：各種錯誤情境皆能正確回報。

#### Model（struct_model.py）

- `def set_manual_struct(self, members: list, total_size: int) -> None:`
  - 設定手動 struct 內容。
  - 測試：設定後屬性正確。

- `def validate_manual_struct(self, members: list, total_size: int) -> list:`
  - 驗證 bitfield 設定（長度總和、名稱唯一、長度正整數等），回傳錯誤訊息 list。
  - 測試：各種錯誤情境皆能正確回報。

- `def export_manual_struct_to_h(self) -> str:`
  - 產生對應的 C struct bitfield 語法（無 padding），回傳 .h 檔內容字串。
  - 測試：產生內容正確。

- `def calculate_manual_layout(self, members: list, total_size: int) -> list:`
  - 計算無 padding 的 bitfield 記憶體排列，回傳 layout list。
  - 測試：排列正確、無 padding。

#### 測試/功能骨架建議
- 每個 function 先寫單元測試（如 pytest/unittest），再實作功能。
- 測試覆蓋：
  - UI 互動（可用 mock 或 integration 測試）
  - bitfield 驗證（如總長度不符、名稱重複、長度非正整數等）
  - 匯出內容格式
  - 記憶體排列正確性
- 建議先產生測試檔案與 function stub，再逐步實作。 

---

## 9. View層開發與測試建議

### 9.1 TDD流程與開發步驟
- 先產生測試 stub（可 mock Presenter，驗證 UI 行為）
- 再實作 View 層功能骨架
- 逐步補齊互動與驗證細節

### 9.2 主要測試案例
- Tab 切換時，正確顯示對應內容
- 手動 struct 設定 UI 元件渲染、欄位可互動
- Bitfield 表格可增刪、資料正確回傳
- 驗證錯誤時紅字顯示，通過時顯示通過
- 匯出按鈕可觸發 Presenter

### 9.3 建議開發步驟
1. 產生 `tests/test_struct_view.py` 的測試骨架（mock Presenter，驗證 UI 行為）
2. 實作 `src/view/struct_view.py` 的 UI 功能骨架
3. 逐步補齊 bitfield 表格、驗證提示、匯出等互動細節

### 9.4 其他建議
- 測試可用 unittest + tkinter widget 測試，或 mock Presenter
- 建議每個互動/功能都先寫測試再實作，確保 UI 可維護性
- 若需進行更完整的整合測試，可考慮在 tests/ 新增 integration 測試，模擬完整流程（不含 UI） 

---

## 10. View層測試失敗排查紀錄

### 問題現象
- 執行 `tests/test_struct_view.py` 時，出現 ImportError：No module named 'config'。
- Traceback 指向 `src/view/struct_view.py` 的 `from config import get_string`。

### 成因分析
- View 層原本設計需支援國際化，部分 UI 文字透過 `get_string` 取得。
- 但在新版骨架與測試 stub 中，Tab 與手動 struct 設定等功能已直接寫死中文字串，未用到 `get_string`。
- 測試時仍會 import `struct_view.py`，而該檔案頂部仍有 `from config import get_string`，導致找不到 config 模組。
- 測試 stub 並不需要國際化功能，僅需 UI 行為。

### 解法建議
1. **暫時移除或註解 `from config import get_string`**：若目前 View 層不需國際化，可直接移除 import。
2. **將 UI 文字直接寫死於骨架**：如現有骨架所示，Tab、標籤等直接用中文字串。
3. **若需保留國際化，則於測試環境 mock get_string**：可用 unittest.mock patch。

### 修正步驟
- 先將 `src/view/struct_view.py` 的 `from config import get_string` 註解或移除。
- 確認所有 UI 文字皆已直接寫死於程式碼。
- 重新執行測試，應可通過。 

### 10.1 GUI測試與其他測試分開執行建議
- 由於 Tkinter GUI 測試在 headless（無螢幕）或 macOS/Linux 環境下，與其他測試一起執行時容易出現 segmentation fault。
- 建議將 `tests/test_struct_view.py` 這類 GUI 測試與其他純邏輯/非GUI測試分開執行。
- 操作方式：
  1. 執行所有非GUI測試：
     ```bash
     pytest --ignore=tests/test_struct_view.py
     ```
  2. 有桌面環境時，單獨執行GUI測試：
     ```bash
     pytest tests/test_struct_view.py
     ```
- 也可在 GUI 測試檔案開頭加上 skip 判斷，無 DISPLAY 時自動跳過。
- 這樣可避免 pytest 在整批測試時因 GUI 測試 crash 而中斷。 

---

### 10.2 跨平台自動化測試批次腳本（run_all_tests.py）

- 為避免 GUI 測試與其他測試同時執行造成失敗，專案新增 `run_all_tests.py` 跨平台 Python 批次腳本。
- 此腳本會自動分開執行所有非 GUI 測試（排除 tests/test_struct_view.py）與 GUI 測試（僅執行 tests/test_struct_view.py），並彙總結果。
- 適用於 Windows、macOS、Linux，無需 shell 指令相容性考量。
- 只需執行：
  ```bash
  python run_all_tests.py
  ```
  即可自動完成所有測試，任何一個失敗則整體 exit code 為 1。
- 優點：
  - 減少人為操作錯誤，確保所有測試都能安全執行
  - 一致的測試流程，方便 CI/CD 或團隊協作
  - 可依未來需求擴充自動尋找多個 GUI 測試檔案
- 腳本內容可參考專案根目錄 `run_all_tests.py`，如需調整可直接修改。 