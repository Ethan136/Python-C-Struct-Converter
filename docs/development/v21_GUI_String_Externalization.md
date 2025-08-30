## v21 GUI 字串外部化與 i18n 規劃（僅規劃，暫不實作）

### 目標
- 將 GUI 硬編碼字串全面改為從 XML 載入，統一字串來源，降低跨檔同步成本。
- 為未來多語系（i18n/L10n）鋪路，並減少 UI 文字改動造成的回歸風險。

---

### 背景
- 目前多處 UI 文案仍為硬字串（如按鈕標籤、標題、對話框訊息）。
- 專案已具備字串資源機制：`src/config/ui_strings.xml`、`src/config/ui_strings.py`（`load_ui_strings`, `get_string`）。
- v20 修正導入了新的 GUI 文案（例如 CSV 匯出相關對話框與按鈕），適合在 v21 一併外部化，避免「兩處硬字串靠協作」的問題。

---

### 範圍
- 檔案：
  - `src/view/struct_view.py`: 所有硬字串（標籤、按鈕、欄位標題、對話框文字）。
  - `src/presenter/struct_presenter.py`: 任何 messagebox、filedialog 的文字常數。
  - 必要時其他 view/presenter 檔案中的零星 UI 文字。
- 設定：
  - 於程序啟動時（例如 `src/main.py` 或 app 入口）呼叫 `load_ui_strings("src/config/ui_strings.xml")`。
- XML 字串檔：
  - 補齊 v20 新增字串鍵值；整理命名規則與層次。

非目標（本次不處理）
- 實際語言切換 UI（語系選單）。
- 多檔語系載入（先維持單一 XML）。

---

### 命名與組織建議
- 命名規則：`<區塊>_<用途>`，例如：
  - `filetab_unit_size_label`, `filetab_endianness_label`, `filetab_target_struct_label`
  - `filetab_parse_button`, `filetab_export_csv_button`
  - `dialog_export_done_title`, `dialog_export_done_body`, `dialog_export_error_title`
  - `layout_frame_title`, `member_values_frame_title`, `debug_bytes_frame_title`
- 統一使用英文 key，值可為中文（預設語言）。
- 在 XML 中分群（可用註解）對應畫面區塊，便於維護。

---

### 交付內容
1) 更新並擴充 `src/config/ui_strings.xml` 的鍵值，覆蓋 v20 以來所有新字串。
2) 啟動路徑新增 `load_ui_strings` 呼叫（若尚未在入口檔統一載入）。
3) 將 `struct_view.py`、`struct_presenter.py` 內所有 UI 文案改為 `get_string("key")`。
4) 補充文件：在 `docs/` 紀錄鍵名對照與新增規範。

---

### 實作步驟（建議順序）
1) 鍵名盤點：
   - 以 grep 搜尋 `struct_view.py`、`struct_presenter.py` 中的硬字串；
   - 產生鍵名草表（對應位置與用途）。
2) XML 更新：
   - 在 `ui_strings.xml` 補齊所有鍵；
   - 維持已存在鍵名的相容；新增者遵循命名規範。
3) 啟動載入：
   - 確認入口確實呼叫 `load_ui_strings("src/config/ui_strings.xml")`；若無則新增。
4) 替換呼叫點：
   - 將 UI 硬字串逐一改為 `get_string("...")`；
   - 對話框/檔案對話框亦改為取字串資源。
5) 走查與調整：
   - 檢查是否有遺漏的硬字串；
   - 對於含格式參數的訊息，預留 `{}` 或 `%(name)s`（若將來需要）。

---

### 測試計畫
- 單元測試：
  - `config` 層：`load_ui_strings` 能正確載入 XML；缺鍵回傳 key 名字自身（現行行為）。
  - `view` 層（以 DISPLAY 為條件跳過 headless）：
    - 建立 `StructView`，驗證關鍵元件文字與 XML 對應；
    - 重要彈窗（成功/失敗）以 monkeypatch 取字串來源，不觸發真彈窗。
- 靜態檢查（選擇性）：
  - lint/腳本檢查 `struct_view.py` 是否尚存明顯硬字串（白名單除外，如數字/符號）。

---

### 相容性與風險
- 以 `get_string` 包裝時，若鍵缺失會顯示鍵名本身，有助快速發現漏填但不會崩潰。
- 主要風險在於遺漏鍵或鍵名拼寫不一致；以測試與檢查工具降低風險。

---

### 時程與分工（建議）
- 預估工時：1～2 人日（包含盤點、替換、測試）。
- 在 v21 單獨分支實施，避免與其他功能交錯。

---

### 後續（v22+）
- 多語系支援：
  - 以多份 `ui_strings.<lang>.xml` 匯入；
  - 依環境變數或設定檔選擇語系。
- 字串格式化機制：
  - 統一使用 `str.format` 或 `%(name)s` 風格；
  - 測試覆蓋參數化訊息。

---

### TDD 重構計畫（改動順序＋各階段預期測試結果）

以下採用「小步快跑、測試先行」原則，將外部化工作拆成多個可快速驗證的階段。每一階段都應：
- 先新增或調整測試（紅燈）
- 最小實作讓測試轉綠（綠燈）
- 重構/清理（保持綠燈）

所有命令均在專案根目錄執行。

#### 階段 0：基線校驗（不改動）
- 動作：
  - 執行全部測試。
- 指令：
```bash
pytest -q
```
- 預期：
  - 既有測試全部通過（綠燈）。
  - 若出現與 DISPLAY 有關的 GUI 測試被跳過屬正常現象（headless）。

#### 階段 1：config 層 API 行為測試（防退化）
- 測試新增：`tests/config/test_ui_strings.py`
  - `test_load_ui_strings_success`: 載入 `src/config/ui_strings.xml` 後，至少含有 `app_title`, `dialog_select_file` 等鍵。
  - `test_get_string_fallback_to_key`: 取得不存在鍵時，回傳鍵名本身。
  - `test_load_nonexistent_file_raises`: 當路徑不存在時丟出 `FileNotFoundError`。
- 指令：
```bash
pytest -q tests/config/test_ui_strings.py
```
- 預期：
  - 以上測試綠燈（`src/config/ui_strings.py` 現狀已符合）。

#### 階段 2：Presenter 錯誤標題與訊息本文外部化（邏輯層不觸 UI）
- 目標：將 `StructPresenter` 內錯誤標題映射、檔案對話框標題，以及常見錯誤訊息本文改為使用 `get_string`。
- 涉及檔案：`src/presenter/struct_presenter.py`
- 現況摘錄（僅示意）：
```12:55:src/presenter/struct_presenter.py
from src.config import get_string
...
file_path = filedialog.askopenfilename(
    title=get_string("dialog_select_file"),
    filetypes=(("Header files", "*.h"), ("All files", "*.*" ))
)
...
title_map = {
    "invalid_input": "無效輸入",
    "value_too_large": "數值過大",
    "overflow_error": "溢位錯誤",
    "conversion_error": "轉換錯誤",
}
```
- 測試新增：`tests/presenter/test_presenter_i18n.py`
  - `test_browse_file_dialog_title_uses_xml_key`: 以 monkeypatch `src.config.ui_strings.get_string` 回傳 sentinel，呼叫 `browse_file` 時檢查 `askopenfilename(title=sentinel)` 被呼叫。
  - `test_parse_hex_error_title_uses_xml_key`: 觸發 `invalid_input` 等錯誤碼，期待回傳的錯誤訊息以 `get_string('dialog_invalid_input')` 之值為標題開頭。
- 期望紅燈原因：
  - 錯誤標題目前為硬字串中文映射。
- 實作改動：
  - 將 `title_map` 值改為 `get_string('dialog_invalid_input')` 等對應鍵。
  - 將錯誤訊息本文改為 `get_string(...).format(...)`，例如：
    - `msg_no_file_selected`
    - `msg_not_loaded`
    - `msg_file_load_error`（參數：`{error}`）
    - `msg_input_too_long`（參數：`{length}`, `{expected}`）
    - `msg_hex_parse_error`（參數：`{error}`）
  - 確認所有錯誤訊息標題/本文皆源自 `get_string`。必要的鍵若缺則補。
- 綠燈依據：上述測試通過。

#### 階段 3：View 視窗標題與分頁標籤外部化（基礎可見文字）
- 目標：將 `StructView` 的 `title` 與 Tab 文字改為 `get_string`。
- 涉及檔案：`src/view/struct_view.py`
- 新增鍵（XML）：
  - `window_title`（如：`C Struct GUI`）
  - `tab_load_h`（載入.H檔）
  - `tab_manual_struct`（手動設定資料結構）
  - `tab_debug`（Debug 分頁）
- 測試新增：`tests/view/test_view_i18n_title_tabs.py`（顯示環境存在時執行）
  - `test_window_title_uses_xml`: 建立 `StructView` 後，斷言 `view.title()` 等於 `get_string('window_title')`。
  - `test_tabs_use_xml`: 斷言兩個分頁標籤文字來源為對應鍵。
- 期望紅燈原因：
  - 現況為硬字串。
- 實作改動：
  - 在 `__init__` 或 `_create_tab_control` 將硬字串改為 `get_string(...)`。
  - 於 `ui_strings.xml` 補上新鍵。
- 綠燈依據：測試全部通過。

#### 階段 4：控制列標籤與下拉選單標籤外部化
- 目標：外部化「單位大小：」「Endianness：」「顯示模式：」「Target Struct：」「GUI 版本：」「搜尋：」「Filter：」等標籤。
- 新增鍵（XML 建議）：
  - `label_unit_size`, `label_endianness`, `label_display_mode`, `label_target_struct`, `label_gui_version`, `label_search`, `label_filter`
- 測試新增：`tests/view/test_view_i18n_controls.py`
  - 對各 `Label` 取 `cget('text')`，斷言其值等於 `get_string` 對應鍵。
- 期望紅燈 → 實作改動：
  - 以 `get_string` 替換 `tk.Label(..., text=...)` 的硬字串。
  - XML 補鍵。
- 綠燈依據：測試通過。

#### 階段 5：按鈕文字外部化（展開/收合/批次）
- 目標：外部化 `展開全部`、`收合全部`、`展開選取`、`收合選取`。
- 新增鍵：`btn_expand_all`, `btn_collapse_all`, `btn_expand_selected`, `btn_collapse_selected`
- 測試新增：`tests/view/test_view_i18n_buttons.py`
  - 檢查 `Button` 的 `cget('text')` 對應 `get_string`。
- 期望紅燈 → 實作改動：
  - 改寫 `tk.Button(..., text=...)` 為 `get_string`。
  - XML 補鍵。
- 綠燈依據：測試通過。

#### 階段 6：Treeview 欄位標題外部化
- 目標：外部化 `MEMBER_TREEVIEW_COLUMNS`, `LAYOUT_TREEVIEW_COLUMNS` 內的 `title`。
- 新增鍵：
  - Members：`member_col_name`, `member_col_value`, `member_col_hex_value`, `member_col_hex_raw`
  - Layout：`layout_col_name`, `layout_col_type`, `layout_col_offset`, `layout_col_size`, `layout_col_bit_offset`, `layout_col_bit_size`, `layout_col_is_bitfield`
- 測試新增：`tests/view/test_view_i18n_treeview_headers.py`
  - 斷言 `tree.heading(col, 'text')` 與 `get_string(對應鍵)` 一致。
- 期望紅燈 → 實作改動：
  - 建立 columns 時以 `get_string` 設定 `heading` 文本。
  - XML 補鍵。
- 綠燈依據：測試通過。

#### 階段 7：View 內 messagebox 與錯誤提示外部化
- 現況摘錄（示意）：
```864:864:src/view/struct_view.py
messagebox.showerror(title, message)
```
```963:966:src/view/struct_view.py
messagebox.showerror("錯誤", "尚未載入 struct，無法匯出 CSV")
```
```1016:1025:src/view/struct_view.py
messagebox.showwarning(...)
messagebox.showerror("匯出失敗", str(e))
```
```1623:1633:src/view/struct_view.py
messagebox.showwarning("Context Warning", warning_msg)
messagebox.showerror("錯誤", str(context["error"]))
```
- 新增鍵：
  - `dialog_error_title`, `dialog_warning_title`, `dialog_export_failed_title`, `dialog_not_loaded_title`, `dialog_not_loaded_body`, `dialog_context_warning_title`, `dialog_export_h_title`
- 測試新增：`tests/view/test_view_i18n_messagebox.py`
  - 以 monkeypatch 攔截 `messagebox.showerror/showwarning`，驗證 title/message 來自 `get_string`。
- 期望紅燈 → 實作改動：
  - 全面以 `get_string` 取代硬字串 title/body，動態訊息以格式化或直接附加異常文字。
  - XML 補鍵。
- 綠燈依據：測試通過。

#### 階段 8：XML 鍵完整性測試（集合校驗）
- 目標：確保 XML 至少包含「鍵名清單（初版）」列出的鍵。
- 測試新增：`tests/config/test_ui_keys_presence.py`
  - 解析 `ui_strings.xml`，斷言必備鍵集合皆存在。
- 期望紅燈 → 實作改動：
  - 在 XML 補足缺失鍵。
- 綠燈依據：測試通過。

#### 階段 9：靜態檢查（避免回歸硬字串）
- 測試新增：`tests/view/test_no_hardcoded_ui_strings.py`
  - 使用簡單正則在 `src/view/struct_view.py` 搜尋 `text="..."` 與 `heading(..., text=...)` 的硬字串；
  - 白名單：數字、空字串、非 UI 文字（例如變數、DEBUG 字樣，必要時維護清單）。
- 期望紅燈 → 實作改動：
- 將殘留硬字串改為 `get_string` 或加入白名單依據評估。
- 綠燈依據：測試通過。

#### 階段 10：全域回歸
- 指令：
```bash
pytest -q
```
- 預期：
  - 全部測試綠燈；
  - Headless 環境下 GUI 測試允許被 skip。

---

### 鍵名清單（初版，實作中可調整命名）
- 基礎與對話框：
  - `app_title`, `window_title`, `dialog_select_file`, `dialog_error_title`, `dialog_warning_title`, `dialog_export_failed_title`, `dialog_not_loaded_title`, `dialog_not_loaded_body`, `dialog_context_warning_title`, `dialog_export_h_title`
  - `dialog_invalid_input`, `dialog_value_too_large`, `dialog_overflow_error`, `dialog_conversion_error`, `dialog_parsing_error`, `dialog_invalid_length`, `dialog_no_struct`
- 分頁與區塊：
  - `tab_load_h`, `tab_manual_struct`, `tab_debug`, `layout_frame_title`, `hex_input_title`, `parsed_values_title`
- 控制列標籤：
  - `label_unit_size`, `label_endianness`, `label_display_mode`, `label_target_struct`, `label_gui_version`, `label_search`, `label_filter`
- 按鈕：
  - `btn_expand_all`, `btn_collapse_all`, `btn_expand_selected`, `btn_collapse_selected`, `parse_button`, `browse_button`
- Treeview 欄位：
  - Members：`member_col_name`, `member_col_value`, `member_col_hex_value`, `member_col_hex_raw`
  - Layout：`layout_col_name`, `layout_col_type`, `layout_col_offset`, `layout_col_size`, `layout_col_bit_offset`, `layout_col_bit_size`, `layout_col_is_bitfield`
- Presenter 訊息（本文）：
  - `msg_no_file_selected`, `msg_not_loaded`, `msg_file_load_error`, `msg_input_too_long`, `msg_hex_parse_error`

---

### 測試實作與檔案規劃
- 新增測試檔路徑建議：
  - `tests/config/test_ui_strings.py`
  - `tests/presenter/test_presenter_i18n.py`
  - `tests/view/test_view_i18n_title_tabs.py`
  - `tests/view/test_view_i18n_controls.py`
  - `tests/view/test_view_i18n_buttons.py`
  - `tests/view/test_view_i18n_treeview_headers.py`
  - `tests/view/test_view_i18n_messagebox.py`
  - `tests/view/test_no_hardcoded_ui_strings.py`

---

### PR 切分與改動順序（實作層級）
- PR1：加測試（階段 1）與微調 `ui_strings.xml`（不破壞現有功能）。
- PR2：Presenter 錯誤標題外部化（階段 2）。
- PR3：View 標題與分頁外部化（階段 3）。
- PR4：控制列標籤外部化（階段 4）。
- PR5：按鈕外部化（階段 5）。
- PR6：Treeview 欄位外部化（階段 6）。
- PR7：messagebox 外部化（階段 7）。
- PR8：XML 鍵完整性測試（階段 8）與靜態檢查（階段 9）。
- PR9：全域回歸與文件更新（階段 10）。

---

### 驗收標準（Definition of Done）
- GUI 內可視文字均來源於 `ui_strings.xml`，缺鍵時 UI 顯示鍵名自身，不崩潰。
- 列出的測試檔全部通過，且新增的靜態檢查無紅燈（或白名單合理）。
- `docs/` 已更新鍵名清單與命名規範，對應實際程式碼。
- CI：`pytest -q` 綠燈；在具 DISPLAY 的 runner 上，View 測試可執行且通過。

