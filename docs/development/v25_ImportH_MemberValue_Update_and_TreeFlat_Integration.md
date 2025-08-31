### V25: 匯入 .h — Member Value 更新與 Tree/Flat 整合排查計畫

#### 0）文件目的與範圍（先規劃文件，先不實作）
- 目的：針對 Import .H（匯入 .h）流程中的 member value 顯示與同步問題建立排查計畫，先明確問題、假設、可重現步驟、量測點與驗收標準；本文件僅規劃與排查紀錄，不涉及實作。
- 涵蓋項目：
  1) Struct Layout 欄位在重新 parse data 後未更新 member value。
  2) Tree view 與 Flat view 無法正常顯示 member value。
  3) 評估是否建議將 Tree/Flat 功能整合至 Struct Layout。
- 關聯文件（背景與既有設計）：
  - `docs/development/v22_Unify_MemberValue_and_StructLayout.md`
  - `docs/development/v23_Modern_Replaces_Legacy_and_TreeFlat_Visual_Diff_TDD.md`
  - `docs/development/v24_CSV_Columns_Unify_With_GUI.md`
- 名詞定義：
  - Struct Layout 欄位：在 Import .H 的 Layout/Member 統一表格中顯示的欄位集合（名稱/型別/位移/大小/bitfield/值等）。
  - Member Value：使用者輸入或由資料解析流程推導後在 GUI 呈現的值（含十六進位/原始值表徵）。
  - Parse Data：重新解析結構與資料來源（.h、輸入 bytes/hex、設定等），更新 Model/Presenter/View 的同步流程。
  - Tree/Flat：兩種顯示模式，前者顯示巢狀樹狀結構，後者以單層列表顯示展平結果。

---

#### 1）問題：Struct Layout 欄位可顯示 member value，但在輸入值更新後重新 parse data，Struct Layout 未更新 value

- 現象摘要：
  - 初次載入後 Struct Layout 已能顯示 member value。
  - 使用者輸入數值（或外部值來源變更）後觸發重新 parse data，Struct Layout 欄位未反映新值（疑似維持舊值或空值）。

- 初步假設（Hypotheses）：
  - H1：Presenter 僅刷新資料模型但未觸發 View 的 value 欄位重繫結或重繪。
  - H2：Model 的值快取（或 value provider）未在 parse 後重建，導致舊引用仍被使用。
  - H3：Row key/column id 與資料字典鍵名不一致，造成 value 映射失敗（名稱或大小寫、別名差異）。
  - H4：Layout 與 Value 來源不同步（例如 layout rows 來自舊批次、value 來自新批次）。
  - H5：深/淺拷貝問題，parse 後產生的新 rows 未被 View 採用（仍持有舊列表參考）。
  - H6：事件順序競態（parse 完成晚於 UI 更新、或 UI 在 parse 前就完成渲染）。

- 可重現步驟（Repro）：
  1) 匯入 .h，顯示 Struct Layout 與 Member Value。
  2) 在值輸入欄或對應對話框中更新某欄位數值。
  3) 觸發重新 parse data（同資料、同結構，僅值變化）。
  4) 觀察該欄位 value 是否隨之更新。

- 排查清單（檔案/關鍵點，名稱以實際專案為準）：
  - View 層：`src/view/struct_view.py`
    - 檢查 columns 與資料鍵名對應、value 欄位是否從資料模型取值而非 UI 本地狀態。
    - 確認渲染刷新路徑：parse 完成 → presenter 通知 → view 重建 rows/更新 cells。
  - Presenter 層：`src/presenter/struct_presenter.py`
    - parse 完成後是否廣播最新 rows/values，並確保 UI 訂閱者收到事件。
    - 重新 parse 時有無重建 value provider/context 中的值映射。
  - Model 層：`src/model/struct_model.py`
    - 生成 layout rows 與 value 欄位的責任界線與輸出鍵名；是否存在舊列表引用復用。
  - 值來源：`src/value/*` 或 `src/utils/*`（若有）
    - 值計算、十六進位字串、位元欄位（bitfield）拆解後的同步機制。

- 量測與日誌（觀測點）：
  - parse 前後：輸入值快照、rows 長度與第一筆/目標欄位之值。
  - presenter → view 通知：事件觸發次數、時間戳、內容摘要（欄位 id 與值）。
  - view 重繪：實際寫入 Treeview/Table 的 cell 值（可在測試替身中驗證）。

- 驗收標準（Acceptance Criteria）：
  - AC1：更新值後重新 parse，Struct Layout value 欄位與輸入一致，且無陣痛閃爍/殘留舊值。
  - AC2：多欄位更新或批次更新時，所有受影響欄位一致更新。
  - AC3：Bitfield/陣列/巢狀結構的 value 也正確更新。

- 排查結果與根因（Findings & Root Cause）：
  - R1：Presenter 在重新 parse 後僅更新內部狀態，未對 View 發出 rows/value 的刷新通知；View 仍持有舊 rows 參照，導致 value 未更新。
  - R2：部分 rows 在 parse 後仍使用 legacy 鍵名（如 `field_name`）而非 V22/V24 統一鍵名（如 `name`），造成 value 映射不一致，顯示失敗或維持舊值。

- 修正方向（規劃，先不實作）：
  - 在 parse 完成事件中重建 unified rows（含 `value`、`hex_value`、`hex_raw`、`is_bitfield`），並以明確事件廣播促使 View 重繪（避免沿用舊列表參照）。
  - 統一鍵名為 V22/V24 規範，移除/適配 legacy 鍵名於渲染路徑的影響，確保 columns 與資料鍵名完全一致。
  - 補強測試：更新值→parse→View cells 反映新值（涵蓋 bitfield/陣列/巢狀）。

  - 狀態：已確認根因，待後續實作修復並補測試。

---

#### 2）問題：Tree view 與 Flat view 無法正常顯示 member value（需排查）

- 現象摘要：
  - Tree 與 Flat 兩種模式下，value 欄位無法如預期顯示（空白、錯位或沿用舊值）。

- 初步假設（Hypotheses）：
  - H1：Tree/Flat 兩種 nodes 生成路徑使用不同資料鍵名，導致 value 欄位對不到。
  - H2：Flat 展平過程移除或覆蓋了 value 欄位。
  - H3：兩種模式下 columns 配置不同步（例如少了 `value`/`hex_value`/`hex_raw`）。
  - H4：View 模式切換時未觸發重建/重繫結（沿用另一模式的資料來源）。
  - H5：虛擬化/延遲渲染導致可見範圍外的 cells 未正確填值。

- 可重現步驟（Repro）：
  1) 載入含巢狀結構的 .h，並提供輸入值。
  2) 切換 Tree/Flat 模式，觀察 value 欄位是否正確。
  3) 更新一筆輸入值並重新 parse，再次切換模式觀察更新是否同步。

- 排查清單（檔案/關鍵點）：
  - View：`src/view/struct_view.py`
    - `display_mode` 切換對 columns 與資料繫結的影響。
    - Tree/Flat nodes 的渲染來源是否共享同一筆 rows/字典鍵名。
  - Model：`src/model/struct_model.py`
    - `get_display_nodes("tree"|"flat")` 是否保留 `value` 相關欄位。
  - Columns 定義集中化（若已依 V22/V24）：
    - 確認 `value/hex_value/hex_raw` 與 `is_bitfield` 一致存在且順序正確。

- 測試計畫（新增/強化）：
  - View 測試：在 tree 與 flat 下斷言第一列/特定路徑節點的 `value` 與 `hex_value` 正確。
  - Presenter 測試：切換模式後，rows 的 `value` 欄位仍存在且同步。
  - Model 測試：展平函式不移除 `value` 欄位。

- 驗收標準：
  - AC1：Tree/Flat 兩模式均能顯示正確的 `value`/`hex_value`/`hex_raw`。
  - AC2：模式切換後不需要再次 parse 即能保有最新值。
  - AC3：大量節點下仍維持正確與流暢（虛擬化存在時亦成立）。

---

#### 後續執行項目（追蹤）
- 針對（2）Tree/Flat 顯示 value 問題先暫緩，待（1）修復規劃落地後執行：
  - T2-1：以統一 rows 與鍵名驗證 tree/flat 兩路徑顯示 value 是否恢復。
  - T2-2：若仍有問題，針對展平流程與 columns 差異新增最小重現測試與修復計畫。
  - T2-3：補充虛擬化/大量節點情境測試，確保 value 欄位 lazy render 正確。

#### 3）是否建議將 Tree/Flat 功能整合到 Struct Layout？（架構評估）

- 目標：降低重複、消除模式差異造成的 value 同步問題，提升一致性與可測性。

- 方案選項：
  - A）維持分離：Tree 與 Flat 各自維護 columns 與資料來源。
    - 優點：變更影響範圍可控，符合既有分層。
    - 缺點：重複邏輯多，容易發生不同步（值、欄位順序、鍵名）。
  - B）輕度整合：集中 columns 與資料映射（layout+value 單一真相來源），兩模式共用同一套 rows，僅在 View 層決定是否顯示樹欄/展平視圖。
    - 優點：大幅降低不同步；沿用現有 View 組件，改動風險中。
    - 缺點：需要審視展平的效能與節點 id 穩定性。
  - C）完全整合：Struct Layout 成為單一表格元件，同一套資料在元件內提供 tree/flat 雙模式切換（內部封裝展平與樹化）。
    - 優點：單一元件、體驗一致、測試集中。
    - 缺點：重構幅度較大，需處理虛擬化、選取/展開狀態同步、效能微調。

- 初步建議（Plan 階段結論，先補處理）：
  - 決策：採 C（完全整合），直接於 Struct Layout 內提供 tree/flat 雙模式。
    1) Columns/資料映射統一為單一真相來源（沿用 V22/V24 定義與順序）。
    2) 在 Struct Layout 元件內封裝樹化/展平邏輯與狀態同步（展開/選取/滾動/虛擬化）。
    3) 提供明確 API：`display_mode = {"tree"|"flat"}`、`set_rows(rows)`、`refresh_values()`。
    4) 移除 Tree/Flat 獨立渲染路徑，僅保留 Struct Layout 一條渲染管線以避免不同步。
  - 理由：直接消除重複與不同步源頭，提升一致性與可測試性；風險集中於單元件內，便於覆蓋測試與效能優化。

- 決策依據與檢核：
  - 兼容性：既有測試是否需要最小改動即可通過。
  - 效能：大型結構/大量節點下切換模式與滾動流暢度。
  - 維護性：欄位新增/命名變更是否只需修改一處。

---

#### TDD 計畫（V25 主要改動目標）
- 範圍：聚焦（1）重新 parse 後 value 需正確刷新與（3）Struct Layout 內聚（C，內建 tree/flat 雙模式）。（2）Tree/Flat 顯示問題列入「後續執行項目」，待（1）落地後執行。

- 測試層級與檔案規劃：
  - Model 單元測試：`tests/model/test_struct_model_values.py`
  - Presenter 單元/整合：`tests/presenter/test_struct_presenter_parse_refresh.py`
  - Struct Layout 元件/視圖測試：`tests/view/test_struct_layout_component.py`
  - 端到端（E2E，headless）：`tests/e2e/test_import_h_value_refresh_and_modes.py`

- 共同前置（fixtures/resources）：
  - 測試資源：`tests/resources/v25/simple_struct.h`、`tests/resources/v25/nested_bitfield_struct.h`、對應 `*.bin`/hex 輸入。
  - 統一 columns：引用 `src/config/columns.py` 中的 `UNIFIED_LAYOUT_VALUE_COLUMNS`。

- 用例 A：值更新後重新 parse，Struct Layout 應刷新 value（對應（1））
  - A1：`test_presenter_emits_new_rows_on_parse_complete`
    - 步驟：初次 parse 取得 rows → 修改輸入值 → 重新 parse。
    - 斷言：presenter 發出 parse 完成事件且 rows 身分（id/list 參照）改變；rows 中目標欄位之 `value` 與 `hex_value` 更新。
  - A2：`test_view_updates_cells_after_parse_complete`
    - 步驟：掛載 Struct Layout 視圖 → 注入初次 rows → 修改輸入並重新 parse（模擬事件）。
    - 斷言：目標 cell 顯示新 `value`/`hex_value`，不存在舊值殘留；無需重啟視圖即可更新。
  - A3：`test_unified_keys_are_used_in_rows`
    - 斷言：渲染使用的 rows 僅包含統一鍵名（`name`, `type`, `offset`, `size`, `bit_offset`, `bit_size`, `is_bitfield`, `value`, `hex_value`, `hex_raw`）；不含 legacy 鍵名（如 `field_name`）。
  - A4：`test_bitfield_array_nested_values_refresh`
    - 覆蓋 bitfield/陣列/巢狀：更新來源值後，對應節點之 `value` 與 `hex_value` 皆刷新正確。

- 用例 B：Struct Layout 完全整合（C），內建 tree/flat 雙模式（對應（3））
  - B1：`test_struct_layout_api_contract`
    - 呼叫：`set_rows(rows)`、`display_mode = "tree"|"flat"`、`refresh_values(updated_rows)`。
    - 斷言：
      - 設定 rows 後，欄位順序等於 `UNIFIED_LAYOUT_VALUE_COLUMNS`。
      - `refresh_values` 僅更新值，不改變列數與欄位定義；值與十六進位同步更新。
  - B2：`test_display_mode_switch_preserves_values`
    - 步驟：`display_mode=tree` 顯示正確 → 切換 `flat` → 值維持一致，再切回 `tree`。
    - 斷言：任一模式下的可見列，其 `value/hex_value/hex_raw` 與 rows 一致；切換不需再次 parse。
  - B3：`test_tree_flat_share_same_rows_source`
    - 斷言：tree 與 flat 兩模式渲染共用同一套資料來源（以等值/標識驗證），避免兩份平行狀態。
  - B4（選配）：`test_state_persistence_expand_and_selection`
    - 若保留展開/選取狀態：模式切換後，重新套用合理的對映狀態（或明確重置規則）。
  - B5（效能煙霧）：`test_virtualization_smoke_values_visible_rows`
    - 大量節點下（>1000）在 headless 模式驗證可見範圍內的列值正確；不要求滾動模擬，只檢查初次渲染子集。

- 用例 C：E2E（端到端）流程
  - C1：`test_import_h_update_value_then_parse_and_switch_modes`
    - 步驟：匯入 `.h` 與輸入值 → 檢查值呈現 → 更新輸入值 → 重新 parse → 切換 `tree/flat`。
    - 斷言：值於兩模式下皆已更新；CSV/導出（若適用）與 GUI 顯示一致。

- 驗收對應（連結文件 AC）
  - 對應（1）AC1–AC3：A1–A4 覆蓋。
  - 對應（3）整合目標：B1–B3 為必要，B4–B5 視情況啟用。

- 不在本輪範圍：
  - （2）Tree/Flat 原缺陷的個別渲染差異，列為「後續執行項目」的 T2-1/2/3。

---

#### 需改動的檔案與調整內容（按檔案列出）
- 1）`src/config/columns.py`
  - 確認並統一欄位常數：`UNIFIED_LAYOUT_VALUE_COLUMNS = ["name", "type", "offset", "size", "bit_offset", "bit_size", "is_bitfield", "value", "hex_value", "hex_raw"]`。
  - 若尚無：提供 `get_unified_layout_value_columns()` 取得拷貝，避免外部修改原常數。
  - 若需要：補充欄位標題 key 與 i18n 對應（例如 `layout_col_*`、`member_col_*`），集中管理映射。

- 2）`src/model/struct_model.py`
  - 建立/調整統一 rows 生成：`build_unified_rows(ast, value_source) -> list[dict]`。
    - 產出鍵名必須符合 `UNIFIED_LAYOUT_VALUE_COLUMNS`，包含 `is_bitfield`、`value`、`hex_value`、`hex_raw`。
    - 禁止輸出 legacy 鍵名（如 `field_name`）；若內部仍需，請在 model 內部轉換，不外露。
  - 提供展平/樹化輔助：
    - `to_tree_nodes(unified_rows) -> list[TreeNode]`（可保留 children）。
    - `to_flat_nodes(unified_rows) -> list[TreeNode]`（children 為空）。
    - 節點需有穩定 `node_id`（由完整路徑/offset/type 組合），供 View 維持選取/展開狀態。
  - 值計算：集中處理數值到十六進位的轉換（`hex_value`），bitfield/陣列/巢狀皆須覆蓋。
  - 介面契約：對 presenter 提供單一入口（例如 `get_unified_rows(context)`）。

- 3）`src/presenter/struct_presenter.py`
  - 在 parse 完成時：
    - 重新呼叫 model 的 `build_unified_rows(...)` 取得新 rows。
    - 廣播明確事件（例如 `on_parse_complete(rows)` 或呼叫 View 的 `set_rows(rows)`）。
  - 值更新流程：
    - 重建 value provider/context，避免沿用舊快取。
    - 新增/保留 `refresh_values(updated_rows)` 或等效事件，用於不變更 columns 結構時僅更新值。
  - 事件順序：確保 parse 完成後才觸發 View 更新（避免競態）。

- 4）`src/view/components/struct_layout.py`（新檔，若尚未存在）
  - 單一元件內建 tree/flat 雙模式（決策 C）：
    - API：`set_rows(rows)`、`refresh_values(rows)`、`display_mode = "tree"|"flat"`。
    - Columns 來源：引用 `UNIFIED_LAYOUT_VALUE_COLUMNS`，維持順序與對應。
    - Tree/Flat 渲染：共用同一份 rows 資料，只在視圖層決定是否顯示樹欄與 children。
    - 狀態同步：切換模式時處理展開/選取/滾動位置（最簡策略：重置或最小對映）。
    - 虛擬化（如有）：確保可見列的 `value/hex_value/hex_raw` 正確。

- 5）`src/view/struct_view.py`
  - 以 `StructLayout` 元件取代既有 Tree/Flat 平行渲染管線。
  - 移除重複 columns 定義，統一引用 `UNIFIED_LAYOUT_VALUE_COLUMNS`。
  - 與 presenter 事件對接：parse 完成 → `set_rows`；值變更 → `refresh_values`；模式切換 → 設定 `display_mode`。

- 6）`src/presenter/context_schema.py`（如存在）
  - 移除/更新與 legacy 鍵名或 columns 相關的 schema 欄位，改為以 unified rows 為準。

- 7）i18n/字串資源（實際檔名依專案）：
  - 確保 unified columns 的標題/說明文字存在並一致（`name`、`type`、`offset`...、`hex_raw`）。

- 8）測試檔（依 TDD 計畫新增）
  - `tests/model/test_struct_model_values.py`
  - `tests/presenter/test_struct_presenter_parse_refresh.py`
  - `tests/view/test_struct_layout_component.py`
  - `tests/e2e/test_import_h_value_refresh_and_modes.py`

- 9）工具/匯出（非必要變更，檢查相容）
  - `src/export/csv_export.py` 與 `tools/export_csv_from_h.py` 應已對齊 V24；僅需驗證與 V25 unified rows 不衝突。

---

#### 實作步驟清單（按順序）
1) 模型統一：在 `src/model/struct_model.py` 實作/修正 `build_unified_rows(...)`，並完成 `hex_value`/`hex_raw`、`is_bitfield` 的產生與鍵名統一。
2) Presenter 串接：在 `src/presenter/struct_presenter.py` 於 parse 完成時呼叫 model 並發送 `set_rows`/`on_parse_complete`；在值更新流程改為呼叫 `refresh_values`。
3) 建立 `src/view/components/struct_layout.py` 元件（若無），落地 API 與 tree/flat 內聚；替換 `src/view/struct_view.py` 內的舊管線。
4) Columns 與 i18n：統一由 `src/config/columns.py` 輸出，清理舊 columns 定義；補齊字串資源。
5) 移除 legacy 鍵名外露：檢查所有渲染與匯出路徑，確保不再依賴 `field_name` 等舊鍵。
6) 測試實作：依 TDD 計畫補齊單元/整合/E2E 測試；先紅後綠。
7) 效能與虛擬化驗證：在大量節點下進行煙霧測試，確保可見列值正確與流暢度可接受。
8) 文件更新：同步更新使用說明/遷移筆記（如需）。

---

#### 事件與資料契約（供跨層對齊）
- 事件：
  - `on_parse_complete(rows)`：攜帶全量 unified rows，供 View 首次/重建渲染。
  - `refresh_values(rows)`：僅更新值的版本（columns 結構與列順序不變）。
  - `on_display_mode_change(mode)`：`mode in {"tree", "flat"}`。
- rows 規範（每列至少包含）：
  - `name`, `type`, `offset`, `size`, `bit_offset`, `bit_size`, `is_bitfield`, `value`, `hex_value`, `hex_raw`。
  - 推薦附加：`node_id`（穩定識別）、`full_path`（除錯/顯示用，flat 可選）。
  - 鍵名禁止：`field_name` 等 legacy 名稱不得外露至 View/Presenter 邊界之外。

---
#### 附錄：時程建議與風險
- 里程碑（僅規劃、可依實際調整）：
  - M1：完成問題（1）與（2）排查與測試覆蓋（1–2 天）。
  - M2：完成 C（完全整合）所需之 Struct Layout 內聚（封裝 tree/flat、狀態同步、API）（1–2 天）。
  - M3：效能與虛擬化優化、視覺/互動微調、增補測試與文件（1–2 天）。
- 風險與緩解：
  - 鍵名不一致與舊資料結構相容性風險 → 以適配層/映射表過渡，並強化單元測試。
  - 展平效能與虛擬化交互 → 基準測試與可見範圍渲染策略。
  - 事件順序與 UI 更新 → 在 Presenter 加入狀態機或明確的「完成 parse」事件，再觸發 View 渲染。