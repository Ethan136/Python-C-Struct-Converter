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

- 根據 context 欄位 can_edit, can_delete, user_role 決定允許/拒絕操作。
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