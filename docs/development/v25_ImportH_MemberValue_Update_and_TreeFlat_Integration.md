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

- 初步建議（Plan 階段結論，非實作決策）：
  - 建議採 B → C 的路徑：
    1) 先完成 columns/資料映射集中（遵循 V22/V24 的單一真相來源），確保 Tree/Flat 與 Struct Layout 共用同一套 rows 與鍵名。
    2) 確認問題（1）（2）均修復並通過測試後，再評估是否將兩模式完整內聚到 Struct Layout 元件內（C）。
  - 理由：可最小風險消除 value 不同步根因，後續再進一步簡化 UI 架構。

- 決策依據與檢核：
  - 兼容性：既有測試是否需要最小改動即可通過。
  - 效能：大型結構/大量節點下切換模式與滾動流暢度。
  - 維護性：欄位新增/命名變更是否只需修改一處。

---

#### 附錄：時程建議與風險
- 里程碑（僅規劃、可依實際調整）：
  - M1：完成問題（1）與（2）排查與測試覆蓋（1–2 天）。
  - M2：完成 B（輕度整合）所需的 columns/資料映射集中（1–2 天）。
  - M3：評估/原型 C（完全整合），視結果制定實作計畫（1–2 天）。
- 風險與緩解：
  - 鍵名不一致與舊資料結構相容性風險 → 以適配層/映射表過渡，並強化單元測試。
  - 展平效能與虛擬化交互 → 基準測試與可見範圍渲染策略。
  - 事件順序與 UI 更新 → 在 Presenter 加入狀態機或明確的「完成 parse」事件，再觸發 View 渲染。