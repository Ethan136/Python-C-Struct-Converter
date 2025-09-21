# v28 規劃：統一「Input Bytes」欄位固定於下方

## 問題描述（現況）
- 匯入 .h 頁籤的輸入區包含兩種模式：`hex_grid_frame`（1/4/8-byte 格）與 `flex_frame`（字串 Bytes）。
- 目前在模式切換時，使用 `pack_forget()` 再 `pack()` 重插入，導致該輸入區被插入到之後建立的元件之後（如 Parse/Export 按鈕、Member/Debug/Layout 區域），因此視覺位置有時在上方、有時在下方，缺乏一致性。

根因：`pack_forget()` 後再 `pack()`，會依照呼叫時間重新決定佈局順序，與初始建立順序不同，造成輸入區位置飄移。

## 目標
- 將「Input Bytes」輸入區（無論 `grid` 或 `flex` 模式）固定顯示在匯入 .h 頁籤的「最下方」（Parse/Export 按鈕之後、Debug/Layout 之前或之後需明確定義）。
- 本規劃採「頁籤底部固定區（footer）」方案，避免 pack 重新插入導致順序變動。

## 介面調整設計（提案 A：固定 Footer 容器）
- 在 `StructView._create_file_tab` 中，建立下列主要區塊：
  - `control_frame`（控制列）
  - `file_info_frame`（檔案路徑/選擇）
  - `action_frame`（Parse/Export 按鈕）
  - `content_frame`（Member/Debug/Layout 等主要內容）
  - `input_footer_frame`（新）：「Input Bytes」固定顯示於此，並永遠置於頁籤底部。
- 將現有 `hex_grid_frame` 與 `flex_frame` 移入 `input_footer_frame`，由 `_on_input_mode_change` 僅以顯示/隱藏（`pack()`/`pack_forget()` 或 `grid_remove()`）切換兩者，但不對 `input_footer_frame` 本身做 pack/順序變動。
- 具體順序：
  1) control_frame
  2) file_info（Browse 按鈕 + 路徑 Label）
  3) action_frame（Parse Data / Export CSV）
  4) content_frame（Member、Debug、Layout）
  5) input_footer_frame（固定最底部）

備選（提案 B：grid 版面）
- 以 `grid(row=N)` 固定行號來放置 `input_footer_frame`，內容使用 `pack` 或 `grid` 皆可；本次先採提案 A，成本較低。

## 行為細項
- 初始模式：沿用現行預設（目前預設 `flex_string`）。
  - `input_footer_frame` 內部：`flex_frame` 顯示；`hex_grid_frame` 隱藏。
- 切換模式：
  - 僅在 `input_footer_frame` 內部切換 `flex_frame`/`hex_grid_frame` 的顯示，不再對 `hex_grid_frame` 或 `flex_frame` 進行「離開 footer 的 pack」操作。
- Parse/Export 按鈕位置：固定在 `action_frame`，不隨輸入模式變動。

## 影響範圍
- 主要變更檔：`src/view/struct_view.py`
- 若測試包含對 `pack`/順序的假設，需要更新或放寬。建議新增針對位置一致性的 UI 測試。

## TDD 與驗收
- 新增/更新測試：
  - View 測試：切換模式多次後，`input_footer_frame` 仍存在且位於底部；`flex_frame` 與 `hex_grid_frame` 僅在 footer 內切換顯示。
  - Minimal 測試可用 `object.__new__(StructView)` 與 dummy widgets 驗證狀態旗標（例如：記錄 parent/pack_info）而不需啟動完整 Tk。
- 回歸：
  - 既有 v26 的 `test_view_flexible_input_minimal.py` 應不受影響；如有依賴初始可見性，調整為檢查 footer 內的顯示狀態。

## 具體實作步驟
1) 在 `StructView._create_file_tab` 末端建立 `input_footer_frame = tk.Frame(main_frame)` 並 `pack(fill="x", side="bottom")`。
2) 將現有 `hex_grid_frame` 與 `flex_frame` 的父容器改為 `input_footer_frame`；初始化時僅切換兩者可見性，不再對 `hex_grid_frame`/`flex_frame` 本身做跨區塊的 `pack`。
3) 調整 `_on_input_mode_change`：
   - 切換時只做：`self.hex_grid_frame.pack_forget()` / `self.flex_frame.pack_forget()`，然後在 footer 內 `pack(fill="x", pady=2)` 顯示對應區塊。
   - 不再觸碰 `parse_button`、`export_csv_button` 或其他主要內容區塊的 `pack`。
4) 視需要微調 `Debug Bytes`/`Layout` 的擺位，保持內容區與 footer 的清楚分界。

## 風險與回滾
- 風險：不同平台（macOS/Windows/Linux）之 Tk pack 渲染差異；透過簡易檢查 `winfo_parent` 與 `pack_slaves()` 次序驗證。
- 回滾策略：保留現行 pack 方式 behind feature flag（環境變數），必要時快速切回原行為。

## 發行
- 版本：v28
- 文件：本檔案（docs/development/v28_fix_input_bytes_position.md）
- 附註：不影響 Model/Presenter 流程；純 UI 佈局調整。

---

## 需要修改的模組與檔案
- `src/view/struct_view.py`
  - 僅此檔需改動（UI 佈局調整）。
- 測試新增/更新：
  - `tests/view/test_struct_view_input_footer_position.py`（新增）
  - `tests/view/test_view_flexible_input_minimal.py`（如有依賴初始可見性，微調）

## 需要修改的函式與調整點
- `StructView._create_file_tab(self)`：
  - 新增固定底部容器 `input_footer_frame`，作為 Input Bytes 區域的專屬 footer。
  - 調整 `hex_grid_frame`、`flex_frame` 的父容器為 `input_footer_frame`。
  - 固定頁籤內的主要順序：`control_frame` → `file_info` → `action_frame(parse/export)` → `content_frame(member/debug/layout)` → `input_footer_frame`。
  - 初始顯示：依目前預設 `flex_string` 顯示 `flex_frame`，隱藏 `hex_grid_frame`。

- `StructView._on_input_mode_change(self, mode)`：
  - 僅在 `input_footer_frame` 內切換顯示：
    - `flex_string`：`hex_grid_frame.pack_forget(); flex_frame.pack(fill="x", pady=2)`
    - `grid`：`flex_frame.pack_forget(); hex_grid_frame.pack(fill="x", pady=2)`
  - 不再變動 `parse_button`、`export_csv_button` 或其他區塊的 pack 順序。

- `StructView._create_manual_struct_frame(self, parent)`：
  - 不需改動。此規劃僅針對匯入 .h 頁籤（File tab）。

## 需要新增的輔助函式（View）
- `StructView._create_input_footer(self, parent) -> tk.Frame`
  - 建立並回傳 `input_footer_frame`，集中管理 footer 相關 pack 參數（side="bottom"、fill="x"）。

- `StructView._show_footer_flex(self)` 與 `StructView._show_footer_grid(self)`（可選，讓 `_on_input_mode_change` 更精簡）
  - 僅在 footer 內切換顯示對應 frame。

備註：若不想新增額外方法，可直接在 `_create_file_tab` 與 `_on_input_mode_change` 內實作上述邏輯；但抽出 helper 有助於可讀性與測試。

## 需新增/更新的測試
- 新增：`tests/view/test_struct_view_input_footer_position.py`
  - 覆蓋點：
    - 構造最小 `StructView` 與 Dummy presenter，不啟動真正 Tk（沿用既有 minimal 策略）。
    - 斷言 `hex_grid_frame` 與 `flex_frame` 的父容器同為 `input_footer_frame`。
    - 初始狀態為 `flex_string`：`flex_frame` 顯示、`hex_grid_frame` 隱藏。
    - 切換至 `grid` 再切回 `flex_string` 多次後，仍維持在 footer 內切換顯示，未影響 `parse_button`、`export_csv_button`、`debug/layout` 的相對順序。
    - 可透過記錄 `pack_slaves()` 次序或以屬性旗標模擬驗證（視 minimal 測試對 Tk 可用性而定）。

- 更新（視需要）：`tests/view/test_view_flexible_input_minimal.py`
  - 若有假設輸入區初始位置或可見性，改為：
    - 僅檢查 `get_input_mode()` 預設、`flex_input` 欄位可讀取、`show_flexible_preview` 行為等；
    - 或增加對 footer 內切換顯示的驗證（非必要則不加）。

## TDD 開發流程（步驟）
1) 寫測試（失敗紅燈）：`test_struct_view_input_footer_position.py`
   - 建立 View（minimal），斷言：
     - 存在 `input_footer_frame`；
     - `hex_grid_frame`、`flex_frame` 的父容器為 footer；
     - 初始 `flex_frame` 顯示、`hex_grid_frame` 隱藏；
     - 切換 `grid`/`flex_string` 多次後，兩者仍在 footer 內切換顯示且未影響其他元件順序。

2) 小步實作（綠燈）：
   - 在 `_create_file_tab` 末端加入 `input_footer_frame`，並將現有兩個 frame 改掛在 footer。
   - 調整初始顯示：僅切換 footer 內部顯示。

3) 重構：
   - 視需要抽出 `_create_input_footer`、`_show_footer_flex/grid`。
   - 確保 `_on_input_mode_change` 不再變動 parse/export/其他區塊的 pack 順序。

4) 擴充測試：
   - 在新測試中加入多次切換的序列與順序檢查；
   - 若 minimal 環境無法直接檢查 Tk pack，則以可觀察旗標（例如在 `pack` 時設置屬性）或 Monkey-patch `pack` 以記錄呼叫順序進行驗證。

5) 回歸測試：
   - 執行既有 view/presenter/model 測試，確認行為不變；
   - 尤其是 v26 的 flexible input 測試（解析、預覽、Debug Bytes 顯示）。

6) 文件更新：
   - 若實作時順序或細節與此規劃有差異，回寫本文件的「實作細節」與「測試」段落。

## 驗收準則（Acceptance Criteria）
- 使用者在匯入 .h 頁籤切換輸入模式時，Input Bytes 區域始終固定在頁面底部，視覺不再跳動。
- 多次切換模式仍維持固定位置與正確顯示/隱藏。
- Parse/Export 按鈕與 Member/Debug/Layout 的順序不受影響。
- 所有既有測試與新測試皆為綠燈。
