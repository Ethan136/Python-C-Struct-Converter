# v6 GUI for Nested Struct and Union — Presenter（邏輯/資料流/狀態管理）

## 1. AST node 結構與資料流
- AST node 結構：id, name, type, children, is_struct, is_union, value, offset, size, bitfield info...
- Model 已支援巢狀 AST，Presenter 可直接取得並遞迴處理。

## 2. Presenter 對外 API 設計
- get_struct_ast()：取得 AST 結構。
- get_display_nodes(mode='tree'|'flat')：取得顯示用 node tree。
- on_node_expand(node_id)：處理節點展開事件。
- on_switch_display_mode(mode)：切換新舊顯示模式。
- get_member_value(node_id)：取得欄位值。

## 3. AST to Treeview node 轉換邏輯
- 遞迴將 AST 結構轉為 GUI 可用的 node tree。
- 支援 struct/union/array/bitfield 等巢狀結構。
- 可根據顯示模式（tree/flat）切換不同 node 結構。

## 4. 狀態同步與資料 context
- Presenter 維護 context，統一管理 struct layout、member value、raw data 狀態。
- 切換新舊顯示時，確保資料同步與狀態一致。

## 5. mock View 實作建議
- Presenter 可用 mock View 驗證資料流、狀態管理、AST 轉換邏輯。
- 可用單元測試驗證 API 行為與資料同步。

## 6. 事件處理與 context 更新流程（進階細節）

- 每個事件（on_node_click, on_expand, on_switch_display_mode, on_refresh, on_load_file, undo/redo）都應有明確的 context 更新邏輯。
- 建議用 pseudo code 或流程圖描述「事件→context→推送」的完整鏈路。
- 事件處理範例：
```python
# 點擊節點
def on_node_click(self, node_id):
    self.context["selected_node"] = node_id
    self.context["debug_info"]["last_event"] = "on_node_click"
    self.context["debug_info"]["last_event_args"] = {"node_id": node_id}
    self.push_context()

# 展開節點
def on_expand(self, node_id):
    if node_id not in self.context["expanded_nodes"]:
        self.context["expanded_nodes"].append(node_id)
    self.context["debug_info"]["last_event"] = "on_expand"
    self.context["debug_info"]["last_event_args"] = {"node_id": node_id}
    self.push_context()

# 切換顯示模式
def on_switch_display_mode(self, mode):
    self.context["display_mode"] = mode
    self.context["expanded_nodes"] = ["root"]
    self.context["selected_node"] = None
    self.context["debug_info"]["last_event"] = "on_switch_display_mode"
    self.context["debug_info"]["last_event_args"] = {"mode": mode}
    self.push_context()

# 載入檔案（異步）
async def on_load_file(self, file_path):
    self.context["loading"] = True
    self.context["debug_info"]["last_event"] = "on_load_file"
    self.context["debug_info"]["last_event_args"] = {"file_path": file_path}
    self.push_context()
    try:
        ast = await self.parse_file(file_path)
        self.context["ast"] = ast
        self.context["error"] = None
    except Exception as e:
        self.context["error"] = str(e)
        self.context["debug_info"]["last_error"] = str(e)
    self.context["loading"] = False
    self.push_context()

# undo/redo
def on_undo(self):
    if self.context["history"]:
        self.context = self.context["history"].pop()
        self.context["debug_info"]["last_event"] = "on_undo"
        self.push_context()
```

---

## 7. AST 結構與 Presenter 轉換細節（整併自 v6_GUI_for_nested_struct_and_union.md）
- AST node 結構：id, name, type, children, is_struct, is_union, value, offset, size, bitfield info...
- Presenter 需呼叫 Model 的 parse_struct_definition_ast，取得巢狀 AST 結構。
- 遞迴將 AST 結構轉為 GUI 可用的 node tree，支援 struct/union/array/bitfield 等巢狀結構。
- 可根據顯示模式（tree/flat）切換不同 node 結構。
- Presenter 維護 context，統一管理 struct layout、member value、raw data 狀態，切換新舊顯示時確保資料同步與狀態一致。
- V/P 需改動分析：View 新增樹狀 Treeview、封裝元件、切換框架，Presenter 負責 AST 轉換、資料同步、狀態管理。
- 單元測試：AST 轉換正確性、狀態同步、切換顯示模式、事件處理、與 View 的 API 對接。 

## 7. Presenter 測試與 mock 建議

- 每個事件處理方法都需有單元測試，覆蓋 context 推送、錯誤處理、權限控管、undo/redo 等。
- 使用 mock View 驗證 context 推送與狀態流轉。
- 建議測試用例：
    - 點擊節點後 context["selected_node"] 正確更新。
    - 展開節點後 context["expanded_nodes"] 正確更新。
    - 切換顯示模式 context["display_mode"]、expanded_nodes、selected_node 正確重設。
    - 錯誤處理時 context["error"]、debug_info["last_error"] 正確填寫。
    - 權限不足時拒絕操作並回傳標準錯誤格式。
    - undo/redo 能正確回復 context 狀態。
- 可參考 mock View 實作：
```python
class MockView:
    def update_display(self, nodes, context):
        print(f"View updated: nodes={nodes}, context={context}")
```

---

## 8. context 初始化與重置

- Presenter 應有 context 初始化與 reset 方法，支援 View 請求重置或狀態同步失敗時 fallback。
- context 初始化範例：
```python
def get_default_context():
    return {
        "display_mode": "tree",
        "expanded_nodes": ["root"],
        "selected_node": None,
        "error": None,
        "filter": None,
        "search": None,
        "version": "1.0",
        "extra": {},
        "loading": False,
        "history": [],
        "user_settings": {},
        "last_update_time": time.time(),
        "readonly": False,
        "pending_action": None,
        "debug_info": {
            "last_event": None,
            "last_event_args": {},
            "last_error": None,
            "context_history": [],
            "api_trace": [],
            "version": "1.0",
            "extra": {}
        }
    }

def reset_context(self):
    self.context = get_default_context()
    self.push_context()
```

---

## 9. 權限控管與安全性

- 根據 context 欄位 can_edit, can_delete 決定允許/拒絕操作。
- 權限不足時，Presenter 應回傳標準錯誤格式，並於 context["error"]、debug_info["last_error"] 填寫。
- 範例：
```python
def on_delete_node(self, node_id):
    if not self.context.get("can_delete", False):
        self.context["error"] = "Permission denied"
        self.context["debug_info"]["last_error"] = "PERMISSION_DENIED"
        self.push_context()
        return {"success": False, "error_code": "PERMISSION_DENIED", "error_message": "No permission to delete."}
    # ... 執行刪除 ...
```

---

## 10. debug_info 更新策略

- 每次事件、錯誤、狀態變動時，Presenter 應更新 context["debug_info"]，方便開發與除錯。
- debug_info 可記錄 last_event, last_event_args, last_error, context_history, api_trace 等。
- 建議僅於開發/測試模式下啟用，正式環境可過濾敏感資訊。
- 範例：
```python
def push_context(self):
    self.context["last_update_time"] = time.time()
    # 更新 context_history, api_trace
    if "debug_info" in self.context:
        self.context["debug_info"]["context_history"].append(self.context.copy())
        self.context["debug_info"]["api_trace"].append({
            "api": self.context["debug_info"].get("last_event"),
            "args": self.context["debug_info"].get("last_event_args"),
            "timestamp": time.time()
        })
    self.view.update_display(self.get_display_nodes(self.context["display_mode"]), self.context)
``` 

---

## 11. 現有 Presenter 實作現況與優先建議（2024/07 補充）

### 1. 現有 Presenter 架構與功能
- `src/presenter/struct_presenter.py` 已有 `StructPresenter` 類別，涵蓋：
  - context 狀態管理（含 display_mode, expanded_nodes, selected_node, error, debug_info 等）
  - 事件處理（on_node_click, on_expand, on_switch_display_mode, on_undo, on_delete_node, on_refresh, on_collapse, set_readonly 等）
  - LRU layout cache 機制
  - 權限控管（如 on_delete_node）
  - 與 View 的互動（update_display）
  - 例外處理與 debug_info 更新
- `src/presenter/context_schema.py` 有 context schema 驗證工具。
- `src/view/struct_view.py` 為 tkinter GUI，與 Presenter 互動，負責 UI 呈現與事件 callback。
- 單元測試（`tests/presenter/test_struct_presenter.py`）覆蓋：
  - cache hit/miss/失效/極端情境
  - 事件處理（如 on_manual_struct_change, on_export_manual_struct, parse_manual_hex_data, browse_file 等）
  - 權限控管、例外處理
  - LRU cache 動態調整與自動清空
  - Model/View mock 驗證

### 2. 與本文件規劃的對照
- 文件規劃的 Presenter API、context 結構、事件處理、權限控管、debug_info、單元測試，大多已在現有 code 中落實。
- 事件流程、狀態流、cache、錯誤處理、View 互動、測試覆蓋度都很高。
- context 初始化與 reset、mock View、debug_info 策略、權限控管等也有實作。

### 3. 建議優先處理方向
1. 確認 context 初始化/重置與 schema 驗證是否在所有事件流程中都有呼叫與測試（如 reset_context、get_default_context）。
   - **開發細節**：
     - 檢查 Presenter 是否有 get_default_context/reset_context 方法，並於初始化、重置、重大狀態切換時呼叫。
     - 建議所有事件處理（如 on_switch_display_mode, on_load_file, on_undo, on_refresh）都應考慮 context 的正確初始化或重置。
     - 可於 context 更新後自動呼叫 context_schema 驗證，確保結構正確。
     - 單元測試應覆蓋 context 初始化、重置、異常情境。
2. AST 轉換與顯示模式切換：確認 `get_display_nodes`、AST 轉換邏輯是否完整支援文件規劃的 tree/flat 模式與巢狀 struct/union/bitfield。
   - **開發細節**：
     - 檢查 Presenter 是否有 get_display_nodes(mode) 方法，並能根據 mode='tree'|'flat' 正確遞迴轉換 AST。
     - 測試巢狀 struct/union/array/bitfield 範例，確保顯示正確。
     - 若有新型態（如 bitfield info），需同步 AST 結構與轉換邏輯。
     - 單元測試應覆蓋各種巢狀結構與顯示模式切換。
3. 事件鏈路與 context 推送：檢查所有事件（如 on_node_click, on_expand, on_switch_display_mode, on_load_file, on_undo）是否都會正確推送 context 並更新 debug_info。
   - **開發細節**：
     - 每個事件處理方法結尾應呼叫 push_context 或 update_display，確保 View 能即時取得最新 context。
     - debug_info 應記錄 last_event, last_event_args, context_history, api_trace 等。
     - 建議用 decorator 或 helper function 統一事件推送與 debug_info 更新。
     - 單元測試應驗證事件觸發後 context、debug_info 是否正確。
4. 權限控管與錯誤格式：確認所有需權限的操作（如刪除、編輯）都會正確回傳標準錯誤格式，並於 context["error"]、debug_info["last_error"] 填寫。
   - **開發細節**：
     - 檢查 on_delete_node、on_edit_node 等方法，是否有 can_edit/can_delete 權限判斷。
     - 權限不足時，應回傳 {success: False, error_code, error_message}，並於 context["error"]、debug_info["last_error"] 填寫。
     - 建議統一權限檢查與錯誤格式 helper，方便擴充。
     - 單元測試應覆蓋權限不足、錯誤格式、context/error/debug_info 更新。
5. 單元測試覆蓋：如有新事件或 context 欄位，需補齊測試。
   - **開發細節**：
     - 每新增/修改一個事件或 context 欄位，應同步新增/修改對應單元測試。
     - 覆蓋正常、異常、極端情境（如 cache 滿、權限不足、格式錯誤等）。
     - 測試 Presenter 與 View/Model 的 mock 互動。
     - 可用 coverage 工具檢查測試覆蓋率。
6. View/Presenter API 對接：如有新 API 或 context 欄位，需同步 View 端 callback 與顯示。
   - **開發細節**：
     - 每新增/修改 Presenter API 或 context 欄位，應同步檢查 View 是否有正確 callback 與顯示。
     - 建議用 interface 文件或型別提示（如 dataclass/schema）同步維護 API。
     - 單元測試可 mock View 驗證 update_display、錯誤顯示、狀態同步。

--- 

---

## 9. Codebase 對齊狀態

- 所有 Presenter 事件方法（on_node_click, on_expand, on_collapse, on_switch_display_mode, on_refresh, set_readonly, on_delete_node, on_undo, on_redo）皆已依 API 文件完整實作。
- context 欄位、contract test、mock View、權限控制、錯誤格式、debug_info、undo/redo、readonly 狀態皆有單元測試覆蓋。
- contract test 路徑：`tests/presenter/test_v2p_contract.py`
- context schema 驗證路徑：`src/presenter/context_schema.py`
- 若有 API/欄位/事件異動，請先更新本文件並同步調整 codebase 與測試。 