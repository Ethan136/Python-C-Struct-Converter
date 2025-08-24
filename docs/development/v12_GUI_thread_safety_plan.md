# v12 - GUI Thread-Safety Plan: 完全排除 Tkinter `_tkinter.TclError: Item ... already exists`

## 問題摘要

- 錯誤：`_tkinter.TclError: Item <iid> already exists`
- 堆疊：來源於 `StructPresenter._debounce_push` 以 `threading.Timer` 背景執行緒呼叫 `view.update_display(...)`，而 `update_display → show_treeview_nodes → tree.insert(...)` 在非主執行緒操作 Tk 物件，或與另一個同時重繪競態，導致同一 IID 重複插入。
- 本質：Tkinter UI 操作必須在主執行緒。現況存在（1）非主執行緒重繪、（2）快速連續重繪造成的競態條件。

## 目標

1. 任何 UI 改動都在 Tk 主執行緒執行。
2. 重繪「單一航班」（single-flight），確保同一時間僅一個重繪在進行；之後的重繪會取代前次排程。
3. Treeview IIDs 不重複：重繪前完整清空或在必要時刪除既存 IID。

## 範圍

- `src/presenter/struct_presenter.py`：debounce 與所有觸發 View 更新的路徑。
- `src/view/struct_view.py`：Treeview 重繪流程的序列化與保護。
- 不影響 Model 與 Parser/Layout 的核心邏輯。

## 設計方案

### A. 以 Tk `after` 取代背景 `threading.Timer`

- 變更 `StructPresenter.push_context()`：
  - 移除 `threading.Timer(self._debounce_interval, self._debounce_push)`。
  - 新增主執行緒排程：
    - 保留 `self._pending_context = (nodes, context)`。
    - 若已有排程 `self._after_id`，則 `self.view.after_cancel(self._after_id)`，再重設。
    - 以 `self._after_id = self.view.after(int(self._debounce_interval*1000), self._flush_pending_ui)` 排程。
- 新增 `StructPresenter._flush_pending_ui()`：於主執行緒執行，讀取並清空 `self._pending_context`，最後呼叫 `self._schedule_view_update(nodes, context)`。
- 新增 `StructPresenter._schedule_view_update(nodes, context)`：統一使用 `self.view.after(0, lambda: self.view.update_display(nodes, context))`，杜絕任何背景執行緒直接觸碰 View。

### B. 將所有 View 更新改為主執行緒排程

- `StructPresenter.update(event_type, ...)`、`browse_file()` 完成後的自動顯示、任何自動 refresh/notify 流程，一律改透過 `_schedule_view_update`。
- 保留 `immediate=True` 路徑時，也僅在目前執行緒已確定為主執行緒才可直呼；否則一律走 `after(0, ...)`。

### C. Treeview 重繪序列化與 IID 防護

- `StructView.show_treeview_nodes(...)`：
  - 重繪前先 `tree.delete(*tree.get_children(""))` 全量清空。
  - 插入前增加防護：若 `tree.exists(iid)` 則先 `tree.delete(iid)`（理論上不會發生，作為最後保險）。
  - 加入「正在重繪」旗標：
    - `self._rendering = True` 期間避免重入；若收到新一次更新，記錄為 `self._pending_nodes_for_render`，結束時用 `after_idle` 觸發下一次渲染。
- 可選：使用遞增 `render_token`，`update_display` 帶入 token，僅處理最後一次 token 的渲染結果。

### D. 測試計畫

- 單元測試（Presenter）：
  - 模擬多次快速 `push_context()`，確認僅最後一次內容會進入 `update_display`，且不丟擲例外。
  - 為 View 建立 Dummy 實作，`after()` 立即執行 callback，以便同步測試。
- 整合測試（Presenter ↔ View）：
  - 以小的 `debounce_interval` 觸發高頻更新，驗證不產生 `_tkinter.TclError`。
  - 驗證「tree/flat 切換」與「展開/收合」在高頻更新下不重複插入 IID。

### E. 回滾與旗標

- 新增旗標 `USE_MAIN_THREAD_SCHEDULER = True`：
  - 若必要可快速回退至舊行為（預設為 True）。
- `debounce_interval` 可設為 0 以停用 debounce（純 after(0)）。

## 任務拆解（TODO）

1. Presenter：
   - 移除 `threading.Timer`，改以 `after` + `_after_id` 管理排程。
   - 實作 `_flush_pending_ui()` 與 `_schedule_view_update()`；將所有 View 更新改走 `_schedule_view_update()`。
2. View：
   - `show_treeview_nodes()` 增加 `tree.exists(iid)` 防護與 `_rendering`/排隊邏輯。
   - 確認所有 Treeview 重繪先 `delete(*get_children(""))`。
3. 測試：
   - 新增 Presenter 單元測試與整合測試，覆蓋快速連續更新與模式切換。
4. 文件：
   - 在開發文件補充 thread-safety 原則：所有 UI 需走 main-thread `after`。

## 風險與緩解

- 風險：排程取消/取代時機錯誤可能造成 UI 更新延遲或跳格。
  - 緩解：以 token/flag 確保最後一次更新一定被處理；新增 debug 記錄（最後一次 after id、最後一次 render token）。
- 風險：外部模組直接呼叫 `update_display`。
  - 緩解：集中對外 API，並在 code review 中規範只用 `_schedule_view_update`。

## 成功標準

- 自動與手動操作下，再也不出現 `_tkinter.TclError: Item ... already exists`。
- 在高頻率 `push_context()` 與 tree/flat 切換壓力測試下保持穩定，無視覺閃爍與 UI 卡死。
