import re
import tkinter as tk
from tkinter import filedialog
from src.config import get_string
from src.model.input_field_processor import InputFieldProcessor
import time
from collections import OrderedDict
import os
import threading
from src.presenter.context_schema import validate_presenter_context
import copy
import functools


class HexProcessingError(Exception):
    """Custom exception for hex part processing errors."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind

class StructPresenter:
    def __init__(self, model, view=None, lru_cache_size=None):
        self.model = model
        self.view = view # This will be set by main.py after view is instantiated
        self.input_processor = InputFieldProcessor()
        # 支援從參數、環境變數初始化 cache size
        if lru_cache_size is not None:
            self._lru_cache_size = lru_cache_size
        else:
            env_size = os.environ.get("STRUCT_LRU_CACHE_SIZE")
            self._lru_cache_size = int(env_size) if env_size is not None else 32
        self._layout_cache = OrderedDict()  # (members_key, total_size) -> layout
        self._cache_hits = 0
        self._cache_misses = 0
        self._last_layout_time = None
        self._last_hit_key = None  # 新增：記錄最近命中 key
        self._last_evict_key = None  # 新增：記錄最近淘汰 key
        self._auto_cache_clear_timer = None
        self._auto_cache_clear_enabled = False
        self._auto_cache_clear_interval = None
        self._auto_cache_clear_lock = threading.Lock()
        self._observers = set()  # 新增: 支援多 observer
        # Observer pattern: 註冊自己為 model observer
        if hasattr(self.model, "add_observer"):
            self.model.add_observer(self)
        # context 初始化
        self.context = self.get_default_context()
        self._debounce_timer = None
        self._debounce_lock = threading.Lock()
        self._debounce_interval = 0.1  # 100ms
        self._pending_context = None
        self._history_maxlen = 200

    def add_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.discard(observer)

    def notify_observers(self, event_type, **kwargs):
        for obs in list(self._observers):
            if hasattr(obs, "update"):
                obs.update(event_type, self, **kwargs)

    def update(self, event_type, model, **kwargs):
        """Observer callback: 當 model 狀態變更時自動呼叫。"""
        if event_type == "file_struct_loaded":
            # 只有 file_struct_loaded 才呼叫 get_display_nodes
            if self.view and hasattr(self.view, "update_display"):
                self.view.update_display(self.model.get_display_nodes("tree"), getattr(self, "context", {}))
        # 其他事件只做 cache 失效與 observer 通知
        if event_type in ("manual_struct_changed", "file_struct_loaded"):
            self.invalidate_cache()
        self.notify_observers(event_type, **kwargs)
        # 可根據 event_type 擴充自動行為

    def invalidate_cache(self):
        self._layout_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def _make_cache_key(self, members, total_size):
        key = tuple(sorted((
            m.get('name', '<invalid>'),
            m.get('type', '<invalid>'),
            m.get('bit_size', 0)
        ) for m in members))
        return (key, total_size)

    def _process_hex_parts(self, hex_parts, byte_order):
        """Convert list of hex input parts to a hex string and debug lines."""
        final_hex_parts = []
        debug_bytes = []

        for raw_part, expected_chars in hex_parts:
            if not re.match(r"^[0-9a-fA-F]*$", raw_part):
                raise HexProcessingError(
                    "invalid_input",
                    f"Input '{raw_part}' contains non-hexadecimal characters."
                )

            chunk_byte_size = expected_chars // 2

            try:
                # 新版：直接用 process_input_field 產生 bytes
                bytes_for_chunk = self.input_processor.process_input_field(raw_part, chunk_byte_size, byte_order)
                int_value = int.from_bytes(bytes_for_chunk, byte_order)
            except ValueError:
                raise HexProcessingError(
                    "invalid_input",
                    f"Could not convert '{raw_part}' to a number."
                )
            except OverflowError:
                raise HexProcessingError(
                    "value_too_large",
                    f"Value 0x{raw_part} is too large for a {chunk_byte_size}-byte field."
                )

            final_hex_parts.append(bytes_for_chunk.hex())
            debug_bytes.append(bytes_for_chunk)

        debug_lines = []
        for i, chunk in enumerate(debug_bytes):
            hex_chars = [f"{b:02x}" for b in chunk]
            debug_lines.append(f"Box {i+1} ({len(chunk)} bytes): {' '.join(hex_chars)}")

        return "".join(final_hex_parts), debug_lines

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title=get_string("dialog_select_file"),
            filetypes=(("Header files", "*.h"), ("All files", "*.*" ))
        )
        if not file_path:
            return {'type': 'error', 'message': '未選擇檔案'}

        try:
            with open(file_path, 'r') as f:
                struct_content = f.read()
            struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(file_path)
            return {
                'type': 'ok',
                'file_path': file_path,
                'struct_name': struct_name,
                'layout': layout,
                'total_size': total_size,
                'struct_align': struct_align,
                'struct_content': struct_content
            }
        except Exception as e:
            return {'type': 'error', 'message': f"載入檔案時發生錯誤: {e}"}

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

    def on_unit_size_change(self, *args):
        # This method is called when the unit size dropdown changes
        if self.model.total_size > 0: # Only rebuild if a struct is loaded
            # 只回傳 unit_size，讓 View 決定如何處理
            unit_size = self.view.get_selected_unit_size() if self.view else None
            return {"unit_size": unit_size}
        return {"unit_size": None}

    def on_endianness_change(self, *args):
        # This method is called when the endianness dropdown changes
        # Trigger re-parsing with the new endianness
        self.parse_hex_data()

    def parse_hex_data(self):
        if not self.model.layout:
            return {'type': 'error', 'message': '尚未載入 struct 定義檔案'}

        hex_parts_with_expected_len = self.view.get_hex_input_parts()

        byte_order_str = self.view.get_selected_endianness()
        byte_order_for_conversion = 'little' if byte_order_str == "Little Endian" else 'big'

        try:
            hex_data, debug_lines = self._process_hex_parts(hex_parts_with_expected_len, byte_order_for_conversion)
        except HexProcessingError as e:
            title_map = {
                "invalid_input": "無效輸入",
                "value_too_large": "數值過大",
                "overflow_error": "溢位錯誤",
                "conversion_error": "轉換錯誤",
            }
            return {'type': 'error', 'message': f"{title_map.get(e.kind, '錯誤')}: {str(e)}"}

        if len(hex_data) > self.model.total_size * 2:
            return {'type': 'error', 'message': f"輸入資料長度 ({len(hex_data)}) 超過預期總大小 ({self.model.total_size * 2})"}

        try:
            parsed_values = self.model.parse_hex_data(hex_data, byte_order_for_conversion)
            return {'type': 'ok', 'debug_lines': debug_lines, 'parsed_values': parsed_values}
        except Exception as e:
            return {'type': 'error', 'message': f"解析 hex 資料時發生錯誤: {e}"}

    def validate_manual_struct(self, struct_data):
        return self.model.validate_manual_struct(struct_data["members"], struct_data["total_size"])

    def on_manual_struct_change(self, struct_data):
        errors = self.model.validate_manual_struct(struct_data["members"], struct_data["total_size"])
        return {"errors": errors}

    def on_export_manual_struct(self):
        struct_data = self.view.get_manual_struct_definition() if self.view else None
        struct_name = struct_data.get("struct_name", "MyStruct") if struct_data else "MyStruct"
        h_content = self.model.export_manual_struct_to_h(struct_name)
        return {"h_content": h_content}

    def parse_manual_hex_data(self, hex_parts, struct_def, endian):
        try:
            unit_size = struct_def.get('unit_size')
            byte_order = 'little' if endian == "Little Endian" else 'big'
            hex_data, debug_lines = self._process_hex_parts(hex_parts, byte_order)
            self.model.set_manual_struct(struct_def['members'], struct_def['total_size'])
            layout = self.model.calculate_manual_layout(struct_def['members'], struct_def['total_size'])
            parsed_values = self.model.parse_hex_data(hex_data, byte_order, layout=layout, total_size=struct_def['total_size'])
            return {'type': 'ok', 'debug_lines': debug_lines, 'parsed_values': parsed_values}
        except HexProcessingError as e:
            title_map = {
                "invalid_input": "無效輸入",
                "value_too_large": "數值過大",
                "overflow_error": "溢位錯誤",
                "conversion_error": "轉換錯誤",
            }
            return {'type': 'error', 'message': f"{title_map.get(e.kind, '錯誤')}: {str(e)}"}
        except Exception as e:
            return {'type': 'error', 'message': f"解析 hex 資料時發生錯誤: {e}"}

    def compute_member_layout(self, members, total_size):
        """計算 struct member 的 layout，回傳 layout list，含 LRU cache 機制。"""
        cache_key = self._make_cache_key(members, total_size)
        print(f"[DEBUG] cache_key: {cache_key}")
        print(f"[DEBUG] cache keys before: {list(self._layout_cache.keys())}")
        if self._lru_cache_size > 0 and cache_key in self._layout_cache:
            self._cache_hits += 1
            # LRU: move to end
            self._layout_cache.move_to_end(cache_key)
            self._last_hit_key = cache_key  # 新增
            print(f"[DEBUG] cache hit: {cache_key}")
            return self._layout_cache[cache_key]
        try:
            start = time.perf_counter()
            layout = self.model.calculate_manual_layout(members, total_size)
            elapsed = time.perf_counter() - start
            self._last_layout_time = elapsed
        except Exception:
            # 不記錄 miss，不快取
            raise
        if self._lru_cache_size > 0:
            self._layout_cache[cache_key] = layout
            self._layout_cache.move_to_end(cache_key)
            while len(self._layout_cache) > self._lru_cache_size:
                evicted = self._layout_cache.popitem(last=False)
                self._last_evict_key = evicted[0]  # 新增
                print(f"[DEBUG] evicted: {evicted[0]}")
        else:
            # cache size 0，不儲存任何項目
            self._layout_cache.clear()
        self._cache_misses += 1
        print(f"[DEBUG] cache keys after: {list(self._layout_cache.keys())}")
        return layout

    def get_last_layout_time(self):
        """回傳最近一次 layout 計算（非 cache）所花秒數（float）。"""
        return self._last_layout_time

    def get_cache_stats(self):
        """回傳 (hit, miss) 統計。"""
        return self._cache_hits, self._cache_misses

    def reset_cache_stats(self):
        self._cache_hits = 0
        self._cache_misses = 0

    def calculate_remaining_space(self, members, total_size):
        """計算剩餘可用空間（bits, bytes）。"""
        used_bits = self.model.calculate_used_bits(members)
        total_bits = total_size * 8
        remaining_bits = max(0, total_bits - used_bits)
        remaining_bytes = remaining_bits // 8
        return remaining_bits, remaining_bytes

    def get_cache_keys(self):
        """回傳目前 LRU cache 的所有 key（list）。"""
        return list(self._layout_cache.keys())

    def get_lru_state(self):
        """回傳 LRU cache 狀態 dict，包含 capacity, current_size, last_hit, last_evict。"""
        return {
            "capacity": self._lru_cache_size,
            "current_size": len(self._layout_cache),
            "last_hit": self._last_hit_key,
            "last_evict": self._last_evict_key
        }

    def set_lru_cache_size(self, size):
        """動態調整 LRU cache 容量，並自動淘汰多餘項目。"""
        if not isinstance(size, int) or size < 0:
            raise ValueError("Cache size must be a non-negative integer")
        self._lru_cache_size = size
        # 淘汰多餘項目
        while len(self._layout_cache) > self._lru_cache_size:
            evicted = self._layout_cache.popitem(last=False)
            self._last_evict_key = evicted[0]
        # 若設為 0，直接清空 cache
        if self._lru_cache_size == 0:
            self._layout_cache.clear()

    def get_lru_cache_size(self):
        """回傳目前 LRU cache 容量。"""
        return self._lru_cache_size

    def enable_auto_cache_clear(self, interval_sec):
        """啟用定時自動清空 cache，interval_sec 為秒數。"""
        with self._auto_cache_clear_lock:
            self.disable_auto_cache_clear()  # 先停用舊的 timer
            self._auto_cache_clear_enabled = True
            self._auto_cache_clear_interval = interval_sec
            def _clear_and_restart():
                with self._auto_cache_clear_lock:
                    if not self._auto_cache_clear_enabled:
                        return
                    self.invalidate_cache()
                    # 重新啟動 timer
                    self._auto_cache_clear_timer = threading.Timer(self._auto_cache_clear_interval, _clear_and_restart)
                    self._auto_cache_clear_timer.daemon = True
                    self._auto_cache_clear_timer.start()
            self._auto_cache_clear_timer = threading.Timer(self._auto_cache_clear_interval, _clear_and_restart)
            self._auto_cache_clear_timer.daemon = True
            self._auto_cache_clear_timer.start()

    def disable_auto_cache_clear(self):
        """停用自動清空 cache。"""
        with self._auto_cache_clear_lock:
            self._auto_cache_clear_enabled = False
            if self._auto_cache_clear_timer is not None:
                self._auto_cache_clear_timer.cancel()
                self._auto_cache_clear_timer = None
            self._auto_cache_clear_interval = None

    def is_auto_cache_clear_enabled(self):
        """查詢自動清空 cache 是否啟用。"""
        with self._auto_cache_clear_lock:
            return self._auto_cache_clear_enabled

    @staticmethod
    def get_default_context():
        import time
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
            },
            "can_edit": True,
            "can_delete": True,
            "user_role": "admin"
        }

    def reset_context(self):
        self.context = self.get_default_context()
        self.push_context()

    def push_context(self, immediate=False):
        import time
        # 非 undo/redo 事件時，push context 前清空 redo_history
        if self.context["debug_info"].get("last_event") not in ("on_undo", "on_redo"):
            self.context["redo_history"] = []
        self.context["last_update_time"] = time.time()
        # 更新 context_history, api_trace
        if "debug_info" in self.context:
            import copy
            history = self.context["debug_info"].setdefault("context_history", [])
            # --- 避免 reference loop ---
            ctx_copy = copy.deepcopy(self.context)
            if "debug_info" in ctx_copy:
                ctx_copy["debug_info"]["context_history"] = []
                ctx_copy["debug_info"]["api_trace"] = []
            history.append(ctx_copy)
            if len(history) > self._history_maxlen:
                del history[0:len(history)-self._history_maxlen]
            api_trace = self.context["debug_info"].setdefault("api_trace", [])
            api_trace.append({
                "api": self.context["debug_info"].get("last_event"),
                "args": self.context["debug_info"].get("last_event_args"),
                "timestamp": time.time()
            })
            if len(api_trace) > self._history_maxlen:
                del api_trace[0:len(api_trace)-self._history_maxlen]
        from src.presenter.context_schema import validate_presenter_context
        validate_presenter_context(self.context)
        # Debounce/throttle 推送
        if immediate or self._debounce_interval == 0:
            if self.view and hasattr(self.view, "update_display"):
                nodes = self.model.get_display_nodes(self.context["display_mode"]) if self.model and hasattr(self.model, "get_display_nodes") else None
                self.view.update_display(nodes, self.context.copy())
            return
        with self._debounce_lock:
            self._pending_context = (self.model.get_display_nodes(self.context["display_mode"]) if self.model and hasattr(self.model, "get_display_nodes") else None, self.context.copy())
            if self._debounce_timer is None:
                self._debounce_timer = threading.Timer(self._debounce_interval, self._debounce_push)
                self._debounce_timer.daemon = True
                self._debounce_timer.start()

    def _debounce_push(self):
        with self._debounce_lock:
            if self.view and hasattr(self.view, "update_display") and self._pending_context:
                nodes, context = self._pending_context
                self.view.update_display(nodes, context)
            self._debounce_timer = None
            self._pending_context = None

    def event_handler(event_name=None):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                # 自動記錄 last_event/last_event_args
                if event_name:
                    self.context["debug_info"]["last_event"] = event_name
                    # 嘗試自動推測 event_args
                    import inspect
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())[1:]  # 跳過 self
                    event_args = {k: v for k, v in zip(params, args)}
                    event_args.update(kwargs)
                    self.context["debug_info"]["last_event_args"] = event_args
                try:
                    result = func(self, *args, **kwargs)
                except Exception as e:
                    self.context["error"] = str(e)
                    self.context["debug_info"]["last_error"] = str(e)
                    self.push_context()
                    raise
                self.push_context()
                return result
            return wrapper
        return decorator

    @event_handler("on_node_click")
    def on_node_click(self, node_id):
        self.context["selected_node"] = node_id

    @event_handler("on_expand")
    def on_expand(self, node_id):
        if node_id not in self.context["expanded_nodes"]:
            self.context["expanded_nodes"].append(node_id)

    @event_handler("on_switch_display_mode")
    def on_switch_display_mode(self, mode):
        self.context["display_mode"] = mode
        self.context["expanded_nodes"] = ["root"]
        self.context["selected_node"] = None

    @event_handler("on_collapse")
    def on_collapse(self, node_id):
        if node_id in self.context["expanded_nodes"]:
            self.context["expanded_nodes"].remove(node_id)

    @event_handler("on_refresh")
    def on_refresh(self):
        # 清空 highlighted_nodes，確保 refresh 後 UI 狀態回到預設
        if "highlighted_nodes" in self.context:
            self.context["highlighted_nodes"] = []
        # 其餘 refresh 行為（如有）

    @event_handler("set_readonly")
    def set_readonly(self, readonly: bool):
        self.context["readonly"] = readonly

    @event_handler("on_edit_node")
    def on_edit_node(self, node_id, new_value):
        perm = self._check_permission("edit")
        if perm is not None:
            return perm
        # ...實際編輯邏輯略...
        return {"success": True}

    @event_handler("on_delete_node")
    def on_delete_node(self, node_id):
        perm = self._check_permission("delete")
        if perm is not None:
            return perm
        # ...實際刪除邏輯略...
        return {"success": True}

    def on_undo(self):
        # 將當前 context 推入 redo_history
        if self.context.get("history") and len(self.context["history"]):
            if "redo_history" not in self.context:
                self.context["redo_history"] = []
            self.context["redo_history"].append(self.context.copy())
            self.context = self.context["history"].pop()
        # 補寫 last_event/last_event_args，確保 contract 一致
        self.context["debug_info"]["last_event"] = "on_undo"
        self.context["debug_info"]["last_event_args"] = {}
        self.push_context()

    def on_redo(self):
        # 支援 redo_history，與 undo 對稱
        if self.context.get("redo_history") and len(self.context["redo_history"]):
            if "history" not in self.context:
                self.context["history"] = []
            self.context["history"].append(self.context.copy())
            self.context = self.context["redo_history"].pop()
        # 補寫 last_event/last_event_args，確保 contract 一致
        self.context["debug_info"]["last_event"] = "on_redo"
        self.context["debug_info"]["last_event_args"] = {}
        self.push_context()

    def _check_permission(self, action):
        # action: "delete"、"edit"、... 依 context 欄位 can_delete/can_edit/user_role 判斷
        if action == "delete" and not self.context.get("can_delete", False):
            self.context["error"] = "Permission denied"
            self.context["debug_info"]["last_error"] = "PERMISSION_DENIED"
            self.push_context()
            return {"success": False, "error_code": "PERMISSION_DENIED", "error_message": "No permission to delete."}
        if action == "edit" and not self.context.get("can_edit", False):
            self.context["error"] = "Permission denied"
            self.context["debug_info"]["last_error"] = "PERMISSION_DENIED"
            self.push_context()
            return {"success": False, "error_code": "PERMISSION_DENIED", "error_message": "No permission to edit."}
        # 其他權限可擴充
        return None

    def get_member_value(self, node_id):
        def _find(node):
            if node.get("id") == node_id:
                return node.get("value")
            for child in node.get("children", []):
                v = _find(child)
                if v is not None:
                    return v
            return None
        ast = self.context.get("ast")
        if not ast:
            return None
        return _find(ast)

    def get_struct_ast(self):
        # 若 context 已有 ast，直接回傳
        if "ast" in self.context:
            return self.context["ast"]
        # 否則呼叫 model 取得
        if hasattr(self.model, "get_struct_ast"):
            ast = self.model.get_struct_ast()
            self.context["ast"] = ast
            return ast
        return None

    def get_debug_context_history(self):
        return self.context.get("debug_info", {}).get("context_history", [])

    def get_debug_api_trace(self):
        return self.context.get("debug_info", {}).get("api_trace", [])

    def get_display_nodes(self, mode):
        """對外 API：根據 mode 回傳顯示用 node tree，符合 contract 測試與文件規範。"""
        if hasattr(self.model, "get_display_nodes"):
            return self.model.get_display_nodes(mode)
        return []
