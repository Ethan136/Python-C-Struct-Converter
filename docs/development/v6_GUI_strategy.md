# v6 GUI for Nested Struct and Union — Strategy（策略/規劃）

## 1. 目標與需求
- 支援巢狀 struct/union 樹狀顯示，提升複雜結構的可讀性與可維護性。
- 新舊 GUI 並存，開發過程不中斷現有功能，方便平行開發與用戶回退。
- 提升 GUI 架構彈性，便於未來擴充與單元測試。

## 2. 使用情境與預期行為
- 用戶可於「手動匯入 .H」tab 載入複雜 struct/union，並以樹狀方式瀏覽巢狀結構。
- 可切換新舊顯示模式，對比新舊顯示效果。
- union/struct 節點可展開/收合，欄位資訊清楚分層。
- 未來可擴充巢狀結構的互動編輯。

## 3. 開發策略與分工
- 採用 worktree 平行開發，拆分為元件封裝、切換框架、新顯示機制、資料 context 四大 worktree。
- 每個 worktree 專注單一目標，合併前測試全綠，最終整合。
- 主線僅接受單一大步驟的合併，減少衝突。
- 新舊顯示機制並存，切換框架可隨時回退。

## 3.1 平行開發前事前準備（詳見 v6_parallel_dev_checklist.md）

在進行 View (V) / Presenter (P) 平行開發前，必須完成以下事前準備，確保協作順暢：

- Model 層 AST/資料結構已支援巢狀/遞迴，格式與 V2P API 一致
- AST/資料結構有單元測試與資料驅動測試覆蓋
- V2P API/Context/事件流的 mock/stub/contract test 雙邊驗證通過
- Worktree/分支/CI/CD 準備好，能平行開發與測試
- 現有 GUI/Presenter/Model 已 decouple/refactor，無跨層耦合
- 現有測試/快取/狀態管理機制已 review，方便新舊 GUI 共用
- V2P API 文件/contract 已最終 review，欄位、事件、錯誤、權限、debug、版本一致
- （如有）多語系/本地化/a11y 基礎設計已預留

**特別強調：Checklist 狀態必須同步於 YAML/JSON，並於 CI pipeline 自動驗證，所有關鍵項目未全綠不得進入平行開發。每次 worktree/feature branch 合併前，必須 review 並同步 checklist 狀態。**

> 詳細 checklist 與進度追蹤，請見 [v6_parallel_dev_checklist.md](./v6_parallel_dev_checklist.md)

## 4. 注意事項與風險控管
- 資料同步與狀態一致性：切換新舊顯示時，資料 context 必須同步。
- 單元測試與 CI/CD：每個元件、切換機制、AST 轉換皆需測試覆蓋。
- 回退機制：新機制有 bug 可隨時切回舊顯示。
- 風險：AST 結構不完整、資料同步失敗、UI/UX 不一致，需提前設計測試與 fallback。

## 5. worktree 拆分與協作建議
- gui_refactor_components：封裝 member value、struct layout、debug input raw data 為獨立元件。
- gui_switch_container：設計切換容器，實作新舊顯示切換。
- gui_treeview_nested：開發新的樹狀顯示元件，支援巢狀 struct/union。
- gui_data_context：設計 context 物件，統一管理狀態，確保資料同步。
- 合併與協作：主線僅接受單一大步驟合併，worktree 間定期同步，最終整合。 

## 6. 技術建議與開發步驟（整併自 v6_GUI_for_nested_struct_and_union.md）
- 使用 tkinter.ttk.Treeview parent-child 結構，支援展開/收合。
- AST 結構建議直接傳給 GUI，不要先展平成平面 list。
- 可參考檔案總管/JSON Viewer 樹狀顯示方式。
- 遞迴插入函式設計：根據 AST 結構插入 parent/child node。
- 開發步驟建議：
  1. AST 結構傳遞：確認 parser/model 能回傳巢狀 AST 結構。
  2. Treeview 遞迴插入：實作遞迴插入函式，將 AST 轉為 Treeview node。
  3. GUI prototype：新增一個 demo tab，顯示巢狀 struct/union 樹狀結構。
  4. 優化顯示：加上 icon、顏色、展開/收合等細節。
  5. （進階）互動編輯：設計巢狀結構的新增/刪除/編輯 UI。
  6. 保留現有 GUI，提供 tab 或選項切換新舊頁面。

## 7. MVP 架構下的重構考量（整併自 v6_GUI_for_nested_struct_and_union.md）
- 只動 V/P，不動 M 的可行性：Model 必須能回傳巢狀 AST 結構，否則需先 refactor Model。
- 只動 V/P 可做的重構：View 支援新舊顯示切換與樹狀顯示，Presenter 負責 AST 轉換與資料同步。
- 需要重構的模組：View、Presenter（或新元件），Model 若已支援巢狀 AST 可不動。
- 不可避免需動 Model 的情境：Model 只回傳平面展開時，需先補強 Model。
- 建議的下一步：檢查 Model AST 輸出、設計 Presenter AST 轉換、重構 View、如需補強 Model 則先處理。 