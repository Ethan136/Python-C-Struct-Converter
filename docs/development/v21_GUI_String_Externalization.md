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

