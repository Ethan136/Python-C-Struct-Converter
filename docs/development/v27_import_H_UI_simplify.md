# 基本規範
- 使用者需求列於「需求草稿」，AI 不改動本段。
- 文件結構與語氣參考 v26 文件，並加入完整 TDD 計畫。

# 需求草稿（使用者需求）
- 讓「匯入 .h」功能頁面更簡潔。
- Debug Bytes 保留在原本位置。
- 32-bit Pointer 常用，不收進進階設定，需保留在核心設定列。
- Target Struct 寬度維持 18。
- 其餘設定列過寬，採你方建議進行精簡與分行。

# 功能規格（V27 匯入 .h 頁面精簡）
- 控制列重構為兩列：
  1) 核心列（常用）
     - 輸入模式（Input Mode，預設 `flex_string`）
     - Endianness
     - Target Struct（寬度 18）
     - 32-bit Pointer 切換（保留在核心列）
     - Browse、Parse、Export CSV（位置行為不變）
  2) 進階列（以「顯示進階設定」Checkbutton 展開/收合）
     - Display Mode（tree/flat）
     - Search、Filter
     - Expand/Collapse（All/Selected）
     - Batch Delete

- 輸入模式與顯示：
  - 預設 `flex_string`。
  - `flex_string`：顯示單一字串輸入框與預覽，隱藏「單位大小（1/4/8 Bytes）」；
  - `grid`：顯示 hex grid 與「單位大小」，隱藏 flex 輸入框。

- Debug Bytes：
  - 保留現有位置與更新邏輯。
  - `flex_string` 解析成功後持續顯示 bytes 預覽與警告/裁切摘要。

- i18n 新增鍵（已於 `src/config/ui_strings.xml` 增補）：
  - `label_input_mode`：輸入模式：
  - `label_flex_input`：Flexible Hex Input
  - `label_show_advanced`：顯示進階設定

- 版面：
  - 控制列 padding 輕微緊縮（橫向更精簡）。
  - Target Struct 下拉維持 `width=18`。

# 影響檔案
- `src/view/struct_view.py`
  - 控制列切分 `core_row`、`adv_toggle_row`、`advanced_row`。
  - `input_mode_var` 預設改為 `flex_string`。
  - `_on_input_mode_change` 依模式顯示/隱藏 unit 與對應輸入區。
  - Display/Search/Filter/批次按鈕移入進階列；32-bit Pointer 留在核心列。
- `src/config/ui_strings.xml`
  - 新增 `label_input_mode`、`label_flex_input`、`label_show_advanced`。

# TDD 計畫（V27）
- 原則：延續 v26 測試風格；GUI 測試以 `DISPLAY` 為條件跳過；Presenter 測試不依賴 Tk。

## View 測試
- 預設模式與可見性
  - `test_default_mode_flex_and_unit_hidden`
    - 建立 `StructView` 後，`get_input_mode()` 回傳 `flex_string`。
    - 斷言單位標籤與單位選單處於隱藏（可用 `winfo_manager()==''` 或替代旗標）。
- 模式切換
  - `test_switch_to_grid_shows_unit_and_hex_grid`
    - 切換 Input Mode 為 `grid`，斷言：hex grid 顯示、flex 輸入框隱藏、單位顯示。
  - `test_switch_to_flex_hides_unit_and_shows_flex_input`
    - 切回 `flex_string`，斷言反向行為。
- 進階列
  - `test_toggle_advanced_row_visibility`
    - 勾選「顯示進階設定」後，Display Mode 選單等控件顯示；取消則隱藏。
- 核心固定控件
  - `test_pointer_32bit_toggle_in_core_row`
    - 斷言 32-bit Pointer Checkbutton 不受進階收合影響保持可見。
  - `test_target_struct_width_is_18`
    - 斷言 `target_struct_combo['width'] == 18`（或 Entry 回退時同值）。
- Debug Bytes
  - `test_debug_bytes_updates_in_flex_parse`
    - 模擬 `presenter.parse_flexible_hex_input()` 成功回覆後呼叫 `_on_parse_file()`，斷言 Debug 區包含 `Flex Bytes (len=...)` 或警告摘要。
- i18n
  - `test_i18n_labels_present`
    - 斷言 Input Mode 與 Flexible Hex Input 標題來自 `get_string`（非硬編字）。

## Presenter 測試（最小）
- `test_set_input_mode_updates_context`
  - 驗證 `set_input_mode('grid'|'flex_string')` 寫入 `context['extra']['input_mode']`。
- `test_parse_flexible_hex_input_sets_last_flex_hex`
  - Mock View 與 Model，成功解析時 `context.extra.last_flex_hex` 被更新。

## 整合測試（Import .h 流程）
- `test_import_h_flex_then_export_csv`
  - 載入簡易 .h（3 bytes），在 `flex_string` 模式輸入 `0x01,0x0302`；
  - 解析後 `hex_raw` 與 grid 模式一致；
  - 匯出 CSV 成功，並帶入正確 endianness 與 hex_input。
- `test_import_h_grid_vs_flex_equivalence`
  - grid 與 flex 模式下輸入等值資料，輸出等價（`hex_raw` 一致）。
- `test_flow_with_advanced_hidden`
  - 收合進階列執行解析/匯出不受影響。

# 測試注意
- `pytest.mark.skipif(not os.environ.get('DISPLAY'))` 避免 headless 失敗。
- 可用 `object.__new__(StructView)` + 注入必要屬性，覆蓋純 UI 方法以最小化 Tk 依賴（沿用現有策略）。

# 風險與相容性
- 僅 UI 佈局調整，不改 Presenter/Model 合約。
- 若控件可見性判斷在不同平台行為差異，測試可降級為檢查內部旗標或以 try/except 緩衝。

# 驗收標準
- 預設為 `flex_string`；單位控制在預設狀態下隱藏。
- 勾選「顯示進階設定」可看到 Display/Search/Filter/批次控件；取消則收起。
- 32-bit Pointer 永在核心列；Target Struct width=18。
- Debug Bytes 位置與行為維持原有；flex 解析成功有摘要更新。
- grid 與 flex 模式的等值輸入輸出一致；CSV 匯出可用。