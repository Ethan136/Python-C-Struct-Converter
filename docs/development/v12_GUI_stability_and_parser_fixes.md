# v12 - GUI 穩定性與解析修正（Threading、View 版面、Bitfield 解析）

本文件彙整並規劃 v12 階段的改動與後續工作，涵蓋 GUI thread-safety、modern 模式版面調整，以及 bitfield 解析正確性修正。

## 本次已完成的變更（commits）

- View：modern 模式的成員樹移至上方顯示區（Struct Member Value）
  - 變更：`src/view/struct_view.py` 將 `_create_modern_gui()` 的容器改掛在 `member_frame`，讓紅框顯示內容移至藍框區（更符合視覺與操作流）。
  - 來源：826ca65

- Layout：AST bitfield 正確處理，不再被視為一般欄位重置狀態
  - 變更：`src/model/layout.py` 的 `StructLayoutCalculator._process_regular_member`
    - 若為 bitfield 直接改走 `_process_bitfield_member(member)`；
    - 僅在一般欄位時才重置 bitfield 單元狀態。
  - 效果：`u.bits.b1/b2` 共享同一 storage unit，bit_offset 正確遞增。
  - 來源：6a2f568

- Parser：支援匿名 bitfield（例如 `unsigned int   : 2`）
  - 變更：`src/model/struct_parser.py` 的 `_parse_bitfield_declaration`
    - 調整比對順序：先匹配匿名，再匹配具名，避免將匿名樣式誤判為具名；
    - 限定可解析的匿名型別（`int/unsigned int/char/unsigned char`）。
  - 效果：`u.bits` 中匿名 2bit 會正確佔用 bit 位置；因此 `b2` 的 `bit_offset` 由 3 矯正為 5。
  - 來源：bbcab74

> 註：Presenter 改為 Tk `after` 主執行緒排程（3f07c7d）屬同一 v12 議題；雖不在你指定的 commit 區間內，但在「規劃」章節保留以便完整性。

## 現況行為驗證

- 載入 `examples/v5_features_example.h`：
  - `nested.*`、`nested.inner_union.*`、`arr2d[i][j]` 正確展開；
  - `u.bits.b1`：`is_bitfield=True, offset=76, bit_offset=0, bit_size=3`
  - `u.bits.b2`：`is_bitfield=True, offset=76, bit_offset=5, bit_size=5`（中間匿名 2bit 已被計算在 storage unit 內）。
- modern 模式：成員樹顯示於頁面上方（Struct Member Value 區塊）。

## 規劃與後續工作

### 1) Thread-safety（Presenter/主執行緒排程）

- 目標：所有 UI 更新皆在主執行緒；避免 `TclError` 或節點重繪競態。
- 現況：Presenter 已使用 `view.after(...)` 安排 UI 更新（3f07c7d）。
- 待辦：
  - 以 single-flight 機制取代/整合既有 debounce 設計，確保只保留最後一次更新。
  - 觀察 Debug 報表，若仍有更新重入跡象，加入 token 或旗標輔助除錯。

### 2) Treeview 重繪序列化與 IID 防護（View）

- 於 `StructView.show_treeview_nodes(...)`：
  - 重繪前先全量 `delete(*get_children(""))`；
  - 插入前若 `tree.exists(iid)`，先刪除舊項目（理論上不會發生，作為保險）；
  - 引入 `_rendering`/`_pending_nodes_for_render` 或 `render_token`，確保不重入。

### 3) 測試與驗證

- 單元測試：快速連續 `push_context()` 僅最後一次被處理；
- 整合測試：高頻 UI 更新與 tree/flat 切換不產生例外；
- 手動驗證：
  - modern 模式上方成員樹位置與互動；
  - `v5_features_example.h` 的 `u.bits` bitfield offsets。

## 風險與緩解

- UI 排程取消/覆蓋邏輯錯誤 → 使用 token 與 debug 記錄（last after id / render token）；
- 外部呼叫直接觸發 `update_display` → 封裝對外 API，強制改走 `_schedule_view_update`。

## 附註（Commit 對照）

- 826ca65 view: modern tree 移至 Struct Member Value 區塊
- 6a2f568 layout: 修正 AST bitfield 處理，避免被當一般欄位重置
- bbcab74 parser: 支援匿名 bitfield，修正 `u.bits` 內 bit_offset 計算
- 3f07c7d presenter: 使用 Tk `after` 主執行緒排程（不在本次指定區間，供參考）

> 若需更詳細的改動脈絡，可於 git log 依序查閱以上 commits。
