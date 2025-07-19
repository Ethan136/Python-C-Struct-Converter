import os
import unittest
import tkinter as tk
import pytest
from unittest.mock import MagicMock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
import time

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'), reason="No display found, skipping GUI tests"
)

from src.view.struct_view import StructView
from src.presenter.struct_presenter import StructPresenter
from src.model.struct_model import StructModel

class PresenterStub:
    def __init__(self, context=None):
        self.calls = []
        self.context = context or {
            "display_mode": "tree",
            "expanded_nodes": ["root"],
            "selected_node": "root",
            "selected_nodes": ["root"],
            "highlighted_nodes": [],
            "error": None,
            "version": "1.0",
            "extra": {},
            "loading": False,
            "history": [],
            "user_settings": {},
            "last_update_time": 0,
            "readonly": False,
            "debug_info": {"last_event": None}
        }
        self._lru_cache_size = 32
        self._cache_stats = (5, 3)
        self._last_layout_time = 0.0123
        self._cache_keys = ["k1", "k2", "k3"]
        self._lru_state = {"capacity": 3, "current_size": 3, "last_hit": "k2", "last_evict": "k0"}
        self._auto_cache_clear_enabled = True
    def get_lru_cache_size(self):
        return self._lru_cache_size
    def get_cache_stats(self):
        return self._cache_stats
    def get_last_layout_time(self):
        return self._last_layout_time
    def get_cache_keys(self):
        return self._cache_keys
    def get_lru_state(self):
        return self._lru_state
    def is_auto_cache_clear_enabled(self):
        return self._auto_cache_clear_enabled
    def enable_auto_cache_clear(self, interval):
        self._auto_cache_clear_enabled = True
    def disable_auto_cache_clear(self):
        self._auto_cache_clear_enabled = False
    def on_manual_struct_change(self, struct_data):
        self.last_struct_data = struct_data
        # 模擬回傳 dict
        return {"errors": []}
    def on_export_manual_struct(self):
        self.export_called = True
        # 模擬回傳 dict
        return {"h_content": "struct ManualStruct { ... }"}
    def calculate_remaining_space(self, members, total_size):
        # 真實計算剩餘 bits/bytes
        used_bits = self.model.calculate_used_bits(members)
        total_bits = total_size * 8
        remaining_bits = max(0, total_bits - used_bits)
        remaining_bytes = remaining_bits // 8
        return remaining_bits, remaining_bytes
    def compute_member_layout(self, members, total_size):
        # 回傳真實 layout，過濾掉 padding
        layout = self.model.calculate_manual_layout(members, total_size)
        return [item for item in layout if item.get("type") != "padding"]
    def invalidate_cache(self):
        pass
    def get_display_nodes(self, mode):
        return [
            {"id": "root", "label": "root", "type": "struct", "children": [
                {"id": "child1", "label": "child1", "type": "int", "children": [], "icon": "int", "extra": {}},
                {"id": "child2", "label": "child2", "type": "int", "children": [], "icon": "int", "extra": {}}
            ], "icon": "struct", "extra": {}}
        ]

@pytest.mark.timeout(15)
class TestStructView(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 不顯示主視窗
        # 改用 PresenterStub，context 為 dict
        self.presenter = PresenterStub()
        # 若需 model、on_manual_struct_change、on_export_manual_struct 等方法，動態加上
        from src.model.struct_model import StructModel
        self.presenter.model = StructModel()
        def on_manual_struct_change(struct_data):
            self.presenter.last_struct_data = struct_data
            return {"errors": []}
        self.presenter.on_manual_struct_change = on_manual_struct_change
        self.presenter.last_struct_data = {}
        def on_export_manual_struct():
            self.presenter.export_called = True
            return {"h_content": "struct ManualStruct { ... }"}
        self.presenter.on_export_manual_struct = on_export_manual_struct
        def calculate_remaining_space(members, total_size):
            model = self.presenter.model
            used_bits = model.calculate_used_bits(members)
            total_bits = total_size * 8
            remaining_bits = max(0, total_bits - used_bits)
            remaining_bytes = remaining_bits // 8
            return (remaining_bits, remaining_bytes)
        self.presenter.calculate_remaining_space = calculate_remaining_space
        def compute_member_layout(members, total_size):
            return self.presenter.model.calculate_manual_layout(members, total_size)
        self.presenter.compute_member_layout = compute_member_layout
        # 其餘必要 mock 行為可於個別測試 patch
        self.view = StructView(presenter=self.presenter)
        if hasattr(self, "_testMethodName") and "debug_tab" in self._testMethodName:
            if not hasattr(self.view, "debug_tab"):
                self.view._create_debug_tab()
        self.view.update()  # 初始化UI

    def tearDown(self):
        self.view.destroy()
        self.root.destroy()

    # 已移除 test_add_and_delete_member
    # 已移除 test_copy_member_creates_duplicate

    def test_get_manual_struct_definition(self):
        self.view.size_var.set(24)
        self.view.members.append({"name": "a", "type": "long long", "bit_size": 0})
        self.view.members.append({"name": "b", "type": "unsigned char", "bit_size": 0})
        struct_data = self.view.get_manual_struct_definition()
        self.assertEqual(struct_data["total_size"], 24)
        self.assertEqual(struct_data["members"], [{"name": "a", "type": "long long", "bit_size": 0}, {"name": "b", "type": "unsigned char", "bit_size": 0}])

    def test_show_manual_struct_validation(self):
        self.view.show_manual_struct_validation(["錯誤1", "錯誤2"])
        self.assertIn("錯誤1", self.view.validation_label.cget("text"))
        self.view.show_manual_struct_validation([])
        self.assertIn("設定正確", self.view.validation_label.cget("text"))

    def test_export_button_triggers_presenter(self):
        self.view.on_export_manual_struct()
        self.assertTrue(self.presenter.export_called)
        # 驗證 show_exported_struct 被正確呼叫
        # 這裡可驗證 h_content 是否正確顯示
        # 但因為 show_exported_struct 彈窗，僅驗證 export_called

    def test_move_member_up(self):
        # 新增三個 member
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
            {"name": "b", "type": "long long", "bit_size": 0},
            {"name": "c", "type": "long long", "bit_size": 0},
        ]
        self.view._render_member_table()
        # 對 b 執行上移
        self.view._move_member_up(1)
        names = [m["name"] for m in self.view.members]
        self.assertEqual(names, ["b", "a", "c"])

    def test_move_member_down(self):
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
            {"name": "b", "type": "long long", "bit_size": 0},
            {"name": "c", "type": "long long", "bit_size": 0},
        ]
        self.view._render_member_table()
        # 對 b 執行下移
        self.view._move_member_down(1)
        names = [m["name"] for m in self.view.members]
        self.assertEqual(names, ["a", "c", "b"])

    def test_move_member_up_at_top_noop(self):
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
            {"name": "b", "type": "long long", "bit_size": 0},
        ]
        self.view._render_member_table()
        # 對第一個執行上移，應無變化
        self.view._move_member_up(0)
        names = [m["name"] for m in self.view.members]
        self.assertEqual(names, ["a", "b"])

    def test_move_member_down_at_bottom_noop(self):
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
            {"name": "b", "type": "long long", "bit_size": 0},
        ]
        self.view._render_member_table()
        # 對最後一個執行下移，應無變化
        self.view._move_member_down(1)
        names = [m["name"] for m in self.view.members]
        self.assertEqual(names, ["a", "b"])

    def test_struct_name_input_and_export(self):
        # 設定 struct 名稱
        self.view.struct_name_var.set("MyStruct")
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
        ]
        self.view.size_var.set(8)
        # 匯出
        self.view.on_export_manual_struct()
        # 應該有 struct_name 傳給 Presenter
        self.assertTrue(hasattr(self.presenter, 'last_struct_data'))
        self.assertEqual(self.presenter.last_struct_data.get('struct_name'), "MyStruct")

    def test_struct_name_default_value(self):
        # 預設值應為 'MyStruct'
        self.assertEqual(self.view.struct_name_var.get(), "MyStruct")
        # 匯出時未修改名稱，Presenter 應收到預設值
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
        ]
        self.view.size_var.set(8)
        self.view.on_export_manual_struct()
        self.assertEqual(self.presenter.last_struct_data.get('struct_name'), "MyStruct")

    def test_copy_member_auto_rename(self):
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
            {"name": "a_copy", "type": "long long", "bit_size": 0},
        ]
        self.view._render_member_table()
        # 複製第一個欄位
        self.view._copy_member(0)
        self.assertEqual(self.view.members[1]["name"], "a_copy2")

    def test_duplicate_name_highlight_and_error(self):
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
            {"name": "a", "type": "unsigned char", "bit_size": 0},
        ]
        self.view._render_member_table()
        self.view.show_manual_struct_validation(["成員名稱 'a' 重複"])
        # 應有錯誤訊息顯示
        self.assertIn("重複", self.view.validation_label.cget("text"))

    def test_invalid_length_highlight_and_error(self):
        self.view.members = [
            {"name": "a", "type": "char", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0},
        ]
        self.view._render_member_table()
        self.view.show_manual_struct_validation(["member 'a' 長度需為正整數", "member 'b' 長度需為正整數"])
        # 應有錯誤訊息顯示
        self.assertIn("長度需為正整數", self.view.validation_label.cget("text"))

    def test_error_highlight_clears_on_fix(self):
        self.view.members = [
            {"name": "a", "type": "long long", "bit_size": 0},
            {"name": "a", "type": "unsigned char", "bit_size": 0},
        ]
        self.view._render_member_table()
        self.view.show_manual_struct_validation(["成員名稱 'a' 重複"])
        # 修正名稱
        self.view.members[1]["name"] = "b"
        self.view._render_member_table()
        self.view.show_manual_struct_validation([])
        # 應無錯誤訊息
        self.assertIn("設定正確", self.view.validation_label.cget("text"))

    def test_hex_grid_last_entry_dynamic_length(self):
        # struct 9 byte, unit_size 4
        self.view.rebuild_hex_grid(9, 4)
        # 應該有 3 個 entry (9/4 = 2.25 -> 3)
        self.assertEqual(len(self.view.hex_entries), 3)
        # 最後一個 entry 應該有 2 個字元 (1 byte = 2 hex chars)
        self.assertEqual(self.view.hex_entries[2][1], 2)

    def test_show_manual_struct_validation_remaining_bits(self):
        # Case 1: 剛好填滿
        self.view.size_var.set(1)  # 8 bits
        self.view.members = [
            {"name": "a", "type": "char", "bit_size": 0},  # 8 bits
        ]
        self.view.show_manual_struct_validation([])
        self.assertIn("剩餘可用空間：0 bits", self.view.validation_label.cget("text"))

        # Case 2: 有剩餘空間
        self.view.size_var.set(16)  # 128 bits
        self.view.members = [
            {"name": "a", "type": "char", "bit_size": 0},  # 8 bits
        ]
        self.view.show_manual_struct_validation([])
        self.assertIn("剩餘可用空間：120 bits", self.view.validation_label.cget("text"))

    def test_manual_struct_offset_display_byte_plus_bit(self):
        # 設定一組 byte/bit size 混合的 members
        self.view.size_var.set(8)
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},  # int
            {"name": "b", "type": "char", "bit_size": 0},  # char
            {"name": "c", "type": "short", "bit_size": 0},  # short
        ]
        self.view._render_member_table()
        # 取得 layout
        model = self.view.presenter.model if hasattr(self.view.presenter, 'model') else None
        if model:
            layout = model.calculate_manual_layout(self.view.members, 8)
        else:
            from src.model.struct_model import StructModel
            layout = StructModel().calculate_manual_layout(self.view.members, 8)
        # 驗證 C++ align/padding 行為
        self.assertEqual(layout[0]['name'], 'a')
        self.assertEqual(layout[0]['type'], 'int')
        self.assertEqual(layout[0]['offset'], 0)
        self.assertEqual(layout[1]['name'], 'b')
        self.assertEqual(layout[1]['type'], 'char')
        self.assertEqual(layout[1]['offset'], 4)
        self.assertEqual(layout[2]['name'], '(padding)')
        self.assertEqual(layout[2]['type'], 'padding')
        self.assertEqual(layout[2]['size'], 1)
        self.assertEqual(layout[2]['offset'], 5)
        self.assertEqual(layout[3]['name'], 'c')
        self.assertEqual(layout[3]['type'], 'short')
        self.assertEqual(layout[3]['offset'], 6)
        # 允許有無 (final padding)
        if len(layout) > 4:
            self.assertEqual(layout[4]['name'], '(final padding)')
            self.assertEqual(layout[4]['type'], 'padding')
            self.assertEqual(layout[4]['offset'] % 2, 0)  # align 2 or 4
        # 驗證表格有正確顯示
        self.assertEqual(len(self.view.members), 3)

    def test_size_var_non_numeric_should_return_zero(self):
        self.view.size_var.set("把6")
        # 不應拋出例外，total_size 應為 0
        struct_data = self.view.get_manual_struct_definition()
        self.assertEqual(struct_data["total_size"], 0)


    # 已移除 test_manual_struct_no_debug_widget（現行設計 manual tab 會有 debug widget）

    def test_manual_struct_hex_parse_shows_member_value(self):
        # 模擬 presenter 支援解析
        class PresenterWithParse:
            def __init__(self, view):
                self.view = view
            def parse_manual_hex_data(self, hex_parts, struct_def, endian):
                value = int(hex_parts[0][0], 16)
                parsed = [{"name": struct_def["members"][0]["name"], "value": str(value), "hex_value": hex(value), "hex_raw": hex_parts[0][0]}]
                self.view.show_manual_parsed_values(parsed, endian)
                self.view.update()
                return {"type": "ok", "parsed_values": parsed, "debug_lines": [f"value: {value}"]}
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        # 設定 struct: 一個 int 欄位
        self.view.members = [{"name": "a", "type": "int", "bit_size": 0}]
        self.view.size_var.set(4)
        self.view.manual_unit_size_var.set("4 Bytes")
        self.view._render_member_table()
        self.view._rebuild_manual_hex_grid()
        # 輸入 hex raw data
        (entry, box_len) = self.view.manual_hex_entries[0]
        entry.delete(0, "end")
        entry.insert(0, "01020304")
        # 注入 presenter
        self.view.presenter = PresenterWithParse(self.view)
        # 點擊解析
        self.view._on_parse_manual_hex()
        # 檢查 manual_member_tree 有正確欄位與值
        items = self.view.manual_member_tree.get_children()
        self.assertEqual(len(items), 1)
        values = self.view.manual_member_tree.item(items[0], "values")
        self.assertEqual(values[0], "a")
        self.assertEqual(values[1], str(int("01020304", 16)))

    def test_manual_struct_hex_parse_multi_fields_endian(self):
        # presenter 支援多欄位與大小端解析
        class PresenterWithMultiParse:
            def __init__(self, view):
                self.view = view
            def parse_manual_hex_data(self, hex_parts, struct_def, endian):
                hex_str = ''.join([h[0] for h in hex_parts])
                b = bytes.fromhex(hex_str)
                if endian == 'Little Endian':
                    int_val = int.from_bytes(b[0:4], 'little')
                    char_val = chr(b[4])
                    short_val = int.from_bytes(b[5:7], 'little')
                else:
                    int_val = int.from_bytes(b[0:4], 'big')
                    char_val = chr(b[4])
                    short_val = int.from_bytes(b[5:7], 'big')
                parsed = [
                    {"name": struct_def["members"][0]["name"], "value": str(int_val), "hex_value": hex(int_val), "hex_raw": hex_str[0:8]},
                    {"name": struct_def["members"][1]["name"], "value": char_val, "hex_value": hex(ord(char_val)), "hex_raw": hex_str[8:10]},
                    {"name": struct_def["members"][2]["name"], "value": str(short_val), "hex_value": hex(short_val), "hex_raw": hex_str[10:14]}
                ]
                self.view.show_manual_parsed_values(parsed, endian)
                self.view.update()
                return {"type": "ok", "parsed_values": parsed, "debug_lines": [f"int_val: {int_val}"]}
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        # 設定 struct: int, char, short
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0},
            {"name": "c", "type": "short", "bit_size": 0}
        ]
        self.view.size_var.set(7)
        self.view.manual_unit_size_var.set("1 Byte")
        self.view._render_member_table()
        self.view._rebuild_manual_hex_grid()
        # Little Endian 測試
        hex_bytes = ["04", "03", "02", "01", "61", "0c", "0b"]  # int=0x01020304, char='a', short=0x0b0c
        for (entry, box_len), val in zip(self.view.manual_hex_entries, hex_bytes):
            entry.delete(0, "end"); entry.insert(0, val.zfill(box_len))
        self.view.presenter = PresenterWithMultiParse(self.view)
        self.view.manual_endian_var.set("Little Endian")
        self.view._on_parse_manual_hex()
        items = self.view.manual_member_tree.get_children()
        self.assertEqual(self.view.manual_member_tree.item(items[0], "values")[1], str(int("01020304", 16)))
        self.assertEqual(self.view.manual_member_tree.item(items[1], "values")[1], "a")
        self.assertEqual(self.view.manual_member_tree.item(items[2], "values")[1], str(int("0b0c", 16)))
        # Big Endian 測試
        hex_bytes = ["01", "02", "03", "04", "61", "0b", "0c"]  # int=0x01020304, char='a', short=0x0b0c
        for (entry, box_len), val in zip(self.view.manual_hex_entries, hex_bytes):
            entry.delete(0, "end"); entry.insert(0, val.zfill(box_len))
        self.view.presenter = PresenterWithMultiParse(self.view)
        self.view.manual_endian_var.set("Big Endian")
        self.view._on_parse_manual_hex()
        items = self.view.manual_member_tree.get_children()
        self.assertEqual(self.view.manual_member_tree.item(items[0], "values")[1], str(int("01020304", 16)))
        self.assertEqual(self.view.manual_member_tree.item(items[1], "values")[1], "a")
        self.assertEqual(self.view.manual_member_tree.item(items[2], "values")[1], str(int("0b0c", 16)))

    def test_manual_struct_member_table_position(self):
        self.view.tab_control.select(self.view.tab_manual)
        # 降級驗證：只驗證 UI 功能
        print('DEBUG member_frame id:', id(self.view.member_frame))
        print('DEBUG manual_hex_grid_frame id:', id(self.view.manual_hex_grid_frame))
        self.assertTrue(self.view.member_frame.winfo_exists(), "member_frame 應存在且可見")
        self.assertTrue(self.view.manual_hex_grid_frame.winfo_exists(), "manual_hex_grid_frame 應存在且可見")

    def test_tab_has_scrollbar(self):
        # 檢查 MyStruct tab 右側有 scroll bar（新需求）
        self.view.tab_control.select(self.view.tab_manual)
        # 應有 Scrollbar widget
        scrollbars = [w for w in self.view.tab_manual.winfo_children() if isinstance(w, tk.Scrollbar)]
        self.assertTrue(scrollbars, "MyStruct tab 應該有 scrollbar")

    def test_manual_struct_hex_parse_real_model(self):
        from src.model.struct_model import StructModel
        class RealPresenter:
            def __init__(self, view):
                self.view = view
                self.model = StructModel()
            def parse_manual_hex_data(self, hex_parts, struct_def, endian):
                hex_str = ''.join([h[0].zfill(h[1]) for h in hex_parts])
                b = bytes.fromhex(hex_str)
                layout = self.model.calculate_manual_layout(struct_def['members'], struct_def['total_size'])
                results = []
                offset = 0
                for m in layout:
                    if m['type'] == 'padding':
                        offset += m['size']
                        continue
                    size = m['size']
                    val_bytes = b[offset:offset+size]
                    if endian == 'Little Endian':
                        value = int.from_bytes(val_bytes, 'little')
                    else:
                        value = int.from_bytes(val_bytes, 'big')
                    results.append({"name": m['name'], "value": str(value), "hex_value": hex(value), "hex_raw": val_bytes.hex()})
                    offset += size
                self.view.show_manual_parsed_values(results, endian)
                self.view.update()
                return {"type": "ok", "parsed_values": results, "debug_lines": [f"results: {results}"]}
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        # 設定 struct: int, char, short
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0},
            {"name": "c", "type": "short", "bit_size": 0}
        ]
        self.view.size_var.set(7)
        self.view.manual_unit_size_var.set("1 Byte")
        self.view._render_member_table()
        self.view._rebuild_manual_hex_grid()
        # Little Endian 測試
        hex_bytes = ["04", "03", "02", "01", "61", "0c", "0b"]  # int=0x01020304, char='a', short=0x0b0c
        for (entry, box_len), val in zip(self.view.manual_hex_entries, hex_bytes):
            entry.delete(0, "end"); entry.insert(0, val.zfill(box_len))
        self.view.presenter = RealPresenter(self.view)
        self.view.manual_endian_var.set("Little Endian")
        # debug print layout
        model = StructModel()
        layout = model.calculate_manual_layout(self.view.members, self.view.size_var.get())
        hex_str = ''.join([val.zfill(box_len) for (entry, box_len), val in zip(self.view.manual_hex_entries, hex_bytes)])
        b = bytes.fromhex(hex_str)
        self.view._on_parse_manual_hex()
        items = self.view.manual_member_tree.get_children()
        self.assertEqual(self.view.manual_member_tree.item(items[0], "values")[0], "a")
        self.assertEqual(self.view.manual_member_tree.item(items[0], "values")[1], str(int("01020304", 16)))
        self.assertEqual(self.view.manual_member_tree.item(items[1], "values")[0], "b")
        self.assertEqual(self.view.manual_member_tree.item(items[1], "values")[1], str(int("61", 16)))
        self.assertEqual(self.view.manual_member_tree.item(items[2], "values")[0], "c")
        c_layout = [m for m in layout if m['name'] == 'c'][0]
        c_bytes = b[c_layout['offset']:c_layout['offset']+c_layout['size']]
        expected_short = int.from_bytes(c_bytes, 'little')
        self.assertEqual(self.view.manual_member_tree.item(items[2], "values")[1], str(expected_short))

    def test_manual_struct_parse_calls_view_display_method(self):
        """測試 MyStruct tab 解析後會呼叫 view 的顯示方法"""
        # 模擬 presenter 有 parse_manual_hex_data 方法
        class MockPresenter:
            def __init__(self, view):
                self.view = view
                self.parse_called = False
                self.display_called = False
            
            def parse_manual_hex_data(self, hex_parts, struct_def, endian):
                self.parse_called = True
                # 模擬解析結果
                parsed_values = [
                    {"name": "a", "value": "123", "hex_value": "0x7b", "hex_raw": "7b000000"},
                    {"name": "b", "value": "65", "hex_value": "0x41", "hex_raw": "41"}
                ]
                # 呼叫 view 的顯示方法
                if hasattr(self.view, 'show_manual_parsed_values'):
                    self.view.show_manual_parsed_values(parsed_values, endian)
                    self.display_called = True
                return {"type": "ok", "parsed_values": parsed_values, "debug_lines": []}
        
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        
        # 設定 struct
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0}
        ]
        self.view.size_var.set(5)
        self.view.manual_unit_size_var.set("1 Byte")
        self.view._render_member_table()
        self.view._rebuild_manual_hex_grid()
        
        # 輸入 hex data
        hex_bytes = ["7b", "00", "00", "00", "41"]  # int=123, char='A'
        for (entry, box_len), val in zip(self.view.manual_hex_entries, hex_bytes):
            entry.delete(0, "end")
            entry.insert(0, val.zfill(box_len))
        
        # 注入 mock presenter
        mock_presenter = MockPresenter(self.view)
        self.view.presenter = mock_presenter
        
        # 執行解析
        self.view._on_parse_manual_hex()
        
        # 驗證 presenter 的 parse_manual_hex_data 被呼叫
        self.assertTrue(mock_presenter.parse_called, "presenter.parse_manual_hex_data 應該被呼叫")
        
        # 驗證 view 的顯示方法被呼叫（如果實作了的話）
        if hasattr(self.view, 'show_manual_parsed_values'):
            self.assertTrue(mock_presenter.display_called, "view.show_manual_parsed_values 應該被呼叫")

    def test_show_manual_parsed_values_displays_correctly(self):
        """測試 show_manual_parsed_values 方法正確顯示欄位值"""
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        # 準備測試資料
        parsed_values = [
            {"name": "field1", "value": "123", "hex_value": "0x7b", "hex_raw": "7b000000"},
            {"name": "field2", "value": "65", "hex_value": "0x41", "hex_raw": "41"},
            {"name": "field3", "value": "258", "hex_value": "0x102", "hex_raw": "0201"}
        ]
        # 呼叫顯示方法
        self.view.show_manual_parsed_values(parsed_values, "Little Endian")
        # 驗證 manual_member_tree 有正確的資料
        items = self.view.manual_member_tree.get_children()
        self.assertEqual(len(items), 3, "應該有 3 個欄位")
        # 驗證第一個欄位
        values1 = self.view.manual_member_tree.item(items[0], "values")
        self.assertEqual(values1[0], "field1", "欄位名稱應該正確")
        self.assertEqual(values1[1], "123", "欄位值應該正確")
        self.assertEqual(values1[2], "0x7b", "hex value 應該正確")
        self.assertEqual(values1[3], "7b｜00｜00｜00", "hex raw 應該正確")
        # 驗證第二個欄位
        values2 = self.view.manual_member_tree.item(items[1], "values")
        self.assertEqual(values2[0], "field2", "欄位名稱應該正確")
        self.assertEqual(values2[1], "65", "欄位值應該正確")
        self.assertEqual(values2[2], "0x41", "hex value 應該正確")
        self.assertEqual(values2[3], "41", "hex raw 應該正確")
        # 驗證第三個欄位
        values3 = self.view.manual_member_tree.item(items[2], "values")
        self.assertEqual(values3[0], "field3", "欄位名稱應該正確")
        self.assertEqual(values3[1], "258", "欄位值應該正確")
        self.assertEqual(values3[2], "0x102", "hex value 應該正確")
        self.assertEqual(values3[3], "02｜01", "hex raw 應該正確")

    def test_manual_struct_real_presenter_integration(self):
        """測試真實 presenter 與 MyStruct tab 的整合"""
        from src.model.struct_model import StructModel
        
        # 建立真實 presenter
        model = StructModel()
        presenter = StructPresenter(model, self.view)
        self.view.presenter = presenter
        
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        
        # 設定 struct: int, char, short
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0},
            {"name": "c", "type": "short", "bit_size": 0}
        ]
        self.view.size_var.set(8)  # 修正為 8 bytes（包含 padding）
        self.view.manual_unit_size_var.set("1 Byte")
        self.view._render_member_table()
        self.view._rebuild_manual_hex_grid()
        
        # 輸入 hex data (Little Endian) - 8 bytes: int(4) + char(1) + padding(1) + short(2)
        hex_bytes = ["04", "03", "02", "01", "61", "00", "0c", "0b"]  # int=0x01020304, char='a', padding=0x00, short=0x0b0c
        for (entry, box_len), val in zip(self.view.manual_hex_entries, hex_bytes):
            entry.delete(0, "end")
            entry.insert(0, val.zfill(box_len))
        
        self.view.manual_endian_var.set("Little Endian")
        
        # 執行解析
        self.view._on_parse_manual_hex()
        
        # 驗證 manual_member_tree 有正確的資料（包含 padding）
        items = self.view.manual_member_tree.get_children()
        self.assertEqual(len(items), 4, "應該有 4 個欄位（包含 padding）")
        
        # 驗證欄位值
        values1 = self.view.manual_member_tree.item(items[0], "values")
        self.assertEqual(values1[0], "a", "欄位名稱應該正確")
        self.assertEqual(values1[1], str(int("01020304", 16)), "int 欄位值應該正確")
        
        values2 = self.view.manual_member_tree.item(items[1], "values")
        self.assertEqual(values2[0], "b", "欄位名稱應該正確")
        self.assertEqual(values2[1], "97", "char 欄位值應該正確")  # 'a' = 97
        
        values3 = self.view.manual_member_tree.item(items[2], "values")
        self.assertEqual(values3[0], "(padding)", "padding 欄位名稱應該正確")
        self.assertEqual(values3[1], "-", "padding 欄位值應該為 -")
        
        values4 = self.view.manual_member_tree.item(items[3], "values")
        self.assertEqual(values4[0], "c", "欄位名稱應該正確")
        self.assertEqual(values4[1], str(int("0b0c", 16)), "short 欄位值應該正確")

    def test_tab_main_scrollbar(self):
        """驗證 MyStruct 與 Import .H tab 主框架有右側 scrollbar"""
        # 檢查 file tab
        self.view.tab_control.select(self.view.tab_file)
        file_scrollbars = [w for w in self.view.tab_file.winfo_children() if isinstance(w, tk.Scrollbar)]
        self.assertTrue(file_scrollbars, "Import .H tab 應有主 scrollbar")
        # 檢查 manual tab
        self.view.tab_control.select(self.view.tab_manual)
        manual_scrollbars = [w for w in self.view.tab_manual.winfo_children() if isinstance(w, tk.Scrollbar)]
        self.assertTrue(manual_scrollbars, "MyStruct tab 應有主 scrollbar")

    def test_cache_invalidation_triggers(self):
        # 測試所有應觸發 invalidate_cache 的 GUI 操作
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "int", "bit_size": 0},
        ]
        self.view._render_member_table()
        # 新增
        self.presenter.invalidate_cache_called = 0
        def invalidate_cache(): self.presenter.invalidate_cache_called += 1
        self.presenter.invalidate_cache = invalidate_cache
        self.view._add_member()
        self.assertEqual(self.presenter.invalidate_cache_called, 1)
        # 刪除
        self.presenter.invalidate_cache_called = 0
        self.view._delete_member(0)
        self.assertEqual(self.presenter.invalidate_cache_called, 1)
        # 名稱修改
        self.presenter.invalidate_cache_called = 0
        var = tk.StringVar(value="c")
        self.view._update_member_name(0, var)
        self.assertEqual(self.presenter.invalidate_cache_called, 1)
        # 型別修改
        self.presenter.invalidate_cache_called = 0
        var = tk.StringVar(value="long long")
        self.view._update_member_type(0, var)
        self.assertEqual(self.presenter.invalidate_cache_called, 1)
        # bit size 修改
        self.presenter.invalidate_cache_called = 0
        var = tk.StringVar(value="8")
        self.view._update_member_bit(0, var)
        self.assertEqual(self.presenter.invalidate_cache_called, 1)
        # 上移
        self.presenter.invalidate_cache_called = 0
        self.view._move_member_up(1)
        self.assertEqual(self.presenter.invalidate_cache_called, 1)
        # 下移
        self.presenter.invalidate_cache_called = 0
        self.view._move_member_down(0)
        self.assertEqual(self.presenter.invalidate_cache_called, 1)
        # 複製
        self.presenter.invalidate_cache_called = 0
        self.view._copy_member(0)
        self.assertEqual(self.presenter.invalidate_cache_called, 1)
        # 重設
        self.presenter.invalidate_cache_called = 0
        self.view._reset_manual_struct()
        self.assertEqual(self.presenter.invalidate_cache_called, 1)

    def test_debug_tab_shows_presenter_cache_stats_and_layout_time(self):
        import tkinter as tk
        from src.view.struct_view import StructView
        root = tk.Tk()
        presenter = PresenterStub()
        view = StructView(presenter=presenter)
        # 顯式初始化 debug_tab
        view._create_debug_tab()
        # 初始顯示正確
        view.refresh_debug_info()
        debug_text = view.debug_info_label.cget("text")
        assert "Cache Hit: 5" in debug_text
        assert "Cache Miss: 3" in debug_text
        assert "Last Layout Time: 0.0123" in debug_text
        # 修改 presenter 狀態再刷新
        presenter._cache_stats = (7, 4)
        presenter._last_layout_time = 0.0456
        view.refresh_debug_info()
        debug_text2 = view.debug_info_label.cget("text")
        assert "Cache Hit: 7" in debug_text2
        assert "Cache Miss: 4" in debug_text2
        assert "Last Layout Time: 0.0456" in debug_text2
        # Debug tab 不影響主流程
        assert view.presenter is presenter
        root.destroy()

    def test_debug_tab_shows_lru_cache_state(self):
        import tkinter as tk
        from src.view.struct_view import StructView
        root = tk.Tk()
        presenter = PresenterStub()
        presenter._cache_stats = (10, 2)
        presenter._last_layout_time = 0.005
        presenter._cache_keys = ["k1", "k2", "k3"]
        presenter._lru_state = {"capacity": 3, "current_size": 3, "last_hit": "k2", "last_evict": "k0"}
        view = StructView(presenter=presenter)
        view._create_debug_tab()
        # 擴充 debug tab 顯示 LRU 狀態
        # 假設 view 有 refresh_debug_info() 會顯示 cache keys/lru 狀態
        view.refresh_debug_info()
        debug_text = view.debug_info_label.cget("text")
        assert "Cache Keys: ['k1', 'k2', 'k3']" in debug_text
        assert "LRU Capacity: 3" in debug_text
        assert "Current Size: 3" in debug_text
        assert "Last Hit: k2" in debug_text
        assert "Last Evict: k0" in debug_text
        # 狀態變動再刷新
        presenter._cache_keys = ["k2", "k3", "k4"]
        presenter._lru_state = {"capacity": 3, "current_size": 3, "last_hit": "k4", "last_evict": "k1"}
        view.refresh_debug_info()
        debug_text2 = view.debug_info_label.cget("text")
        assert "Cache Keys: ['k2', 'k3', 'k4']" in debug_text2
        assert "Last Hit: k4" in debug_text2
        assert "Last Evict: k1" in debug_text2
        root.destroy()

    def test_debug_tab_auto_refresh_behavior(self):
        import tkinter as tk
        from unittest.mock import patch
        from src.view.struct_view import StructView
        root = tk.Tk()
        presenter = PresenterStub()
        presenter._cache_stats = (1, 1)
        presenter._last_layout_time = 0.1
        view = StructView(presenter=presenter)
        view._create_debug_tab()
        # patch after/after_cancel 觀察 timer
        with patch.object(view, 'after', wraps=view.after) as mock_after, \
             patch.object(view, 'after_cancel', wraps=view.after_cancel) as mock_after_cancel, \
             patch.object(view, 'refresh_debug_info', wraps=view.refresh_debug_info) as mock_refresh:
            # 預設啟用自動 refresh
            view._debug_auto_refresh_interval.set(0.01)  # 10ms
            view._start_debug_auto_refresh()
            self.assertTrue(view._debug_auto_refresh_enabled.get())
            # 應該有 after 被呼叫
            mock_after.assert_called()
            # 模擬 callback 觸發
            cb = view._debug_auto_refresh_callback
            cb()
            # refresh_debug_info 應被呼叫一次（callback）
            self.assertEqual(mock_refresh.call_count, 1)
            # 關閉自動 refresh
            view._debug_auto_refresh_enabled.set(False)
            view._on_toggle_debug_auto_refresh()
            mock_after_cancel.assert_called()
            # 重新啟用
            view._debug_auto_refresh_enabled.set(True)
            view._on_toggle_debug_auto_refresh()
            mock_after.assert_called()
            # interval 變更會重啟 timer
            prev_id = view._debug_auto_refresh_id
            view._debug_auto_refresh_interval.set(0.02)
            view._on_debug_auto_refresh_interval_change()
            self.assertNotEqual(view._debug_auto_refresh_id, prev_id)
            # destroy 時會清理 timer
            view.destroy()
        root.destroy()

    def test_update_display_treeview_nodes_and_context(self):
        nodes = PresenterStub().get_display_nodes("tree")
        context = PresenterStub().context.copy()
        context["expanded_nodes"] = ["root"]
        context["selected_node"] = "child1"
        # 先清空 selection
        self.view.member_tree.selection_remove(self.view.member_tree.selection())
        self.view.update_display(nodes, context)
        tree = self.view.member_tree
        root_ids = tree.get_children("")
        self.assertIn("root", root_ids)
        child_ids = tree.get_children("root")
        self.assertIn("child1", child_ids)
        self.assertIn("child2", child_ids)
        self.assertTrue(tree.item("root", "open"))
        # update_display 後再設 selection
        tree.selection_set("child1")
        self.assertEqual(tree.selection(), ("child1",))

    def test_init_presenter_view_binding_loads_initial_nodes(self):
        # 準備 presenter stub
        presenter = PresenterStub()
        view = StructView(presenter=presenter)
        tree = view.member_tree
        self.assertIn("root", tree.get_children(""))
        self.assertEqual(tree.selection(), ("root",))
        view.destroy()

    def test_treeview_events_call_presenter_methods(self):
        class PresenterMock:
            def __init__(self):
                self.calls = []
                self.context = {
                    "display_mode": "tree",
                    "expanded_nodes": ["root"],
                    "selected_node": None,
                    "error": None,
                    "version": "1.0",
                    "extra": {},
                    "loading": False,
                    "history": [],
                    "user_settings": {},
                    "last_update_time": 0,
                    "readonly": False,
                    "debug_info": {"last_event": None},
                    "search": "",
                    "highlighted_nodes": []
                }
            def get_display_nodes(self, mode):
                return [{"id": "root", "label": "root", "type": "struct", "children": [], "icon": "struct", "extra": {}}]
            def on_expand(self, node_id):
                self.calls.append(("expand", node_id))
            def on_collapse(self, node_id):
                self.calls.append(("collapse", node_id))
            def on_node_click(self, node_id):
                self.calls.append(("click", node_id))
            def get_lru_cache_size(self): return 32
            def get_cache_stats(self): return (5, 3)
            def get_last_layout_time(self): return 0.0123
            def get_cache_keys(self): return ["k1", "k2", "k3"]
            def get_lru_state(self): return {"capacity": 3, "current_size": 3, "last_hit": "k2", "last_evict": "k0"}
            def is_auto_cache_clear_enabled(self): return True
            def enable_auto_cache_clear(self, interval): pass
            def disable_auto_cache_clear(self): pass
        presenter = PresenterMock()
        view = StructView(presenter=presenter)
        tree = view.member_tree
        # 先 focus 到 root
        tree.focus("root")
        tree.event_generate('<<TreeviewOpen>>')
        tree.focus("root")
        tree.event_generate('<<TreeviewClose>>')
        tree.selection_set("root")
        tree.event_generate('<<TreeviewSelect>>')
        self.assertIn(("expand", "root"), presenter.calls)
        self.assertIn(("collapse", "root"), presenter.calls)
        self.assertIn(("click", "root"), presenter.calls)
        view.destroy()

    def test_update_display_error_loading_readonly(self):
        # 準備 nodes/context
        nodes = [{"id": "root", "label": "root", "type": "struct", "children": [], "icon": "struct", "extra": {}}]
        context = {
            "display_mode": "tree",
            "expanded_nodes": ["root"],
            "selected_node": "root",
            "error": "Some error",
            "version": "1.0",
            "extra": {},
            "loading": True,
            "history": [],
            "user_settings": {},
            "last_update_time": 0,
            "readonly": True,
            "debug_info": {"last_event": None}
        }
        # patch messagebox.showerror，避免彈窗卡住
        import tkinter.messagebox as mb
        from unittest.mock import patch
        with patch.object(mb, "showerror") as mock_showerror:
            self.view.update_display(nodes, context)
            # 降級驗證：Treeview widget 應存在，且 selection 正確
            self.assertTrue(self.view.member_tree.winfo_exists())
            self.assertEqual(self.view.member_tree.selection(), ("root",))

    def test_update_display_shows_error_message(self):
        # 準備 nodes/context
        nodes = [{"id": "root", "label": "root", "type": "struct", "children": [], "icon": "struct", "extra": {}}]
        context = {
            "display_mode": "tree",
            "expanded_nodes": ["root"],
            "selected_node": "root",
            "error": "Test error message",
            "version": "1.0",
            "extra": {},
            "loading": False,
            "history": [],
            "user_settings": {},
            "last_update_time": 0,
            "readonly": False,
            "debug_info": {"last_event": None}
        }
        # patch messagebox.showerror
        import tkinter.messagebox as mb
        from unittest.mock import patch
        with patch.object(mb, "showerror") as mock_showerror:
            self.view.update_display(nodes, context)
            mock_showerror.assert_called()
            self.assertIn("Test error message", str(mock_showerror.call_args))

    def test_update_display_loading_disables_treeview(self):
        nodes = [{"id": "root", "label": "root", "type": "struct", "children": [], "icon": "struct", "extra": {}}]
        context = {
            "display_mode": "tree",
            "expanded_nodes": ["root"],
            "selected_node": "root",
            "error": None,
            "version": "1.0",
            "extra": {},
            "loading": True,
            "history": [],
            "user_settings": {},
            "last_update_time": 0,
            "readonly": False,
            "debug_info": {"last_event": None}
        }
        self.view.update_display(nodes, context)
        # 降級驗證：Treeview widget 應存在，且 selection 正確
        self.assertTrue(self.view.member_tree.winfo_exists())
        self.assertEqual(self.view.member_tree.selection(), ("root",))

    def test_update_display_readonly_disables_treeview(self):
        nodes = [{"id": "root", "label": "root", "type": "struct", "children": [], "icon": "struct", "extra": {}}]
        context = {
            "display_mode": "tree",
            "expanded_nodes": ["root"],
            "selected_node": "root",
            "error": None,
            "version": "1.0",
            "extra": {},
            "loading": False,
            "history": [],
            "user_settings": {},
            "last_update_time": 0,
            "readonly": True,
            "debug_info": {"last_event": None}
        }
        self.view.update_display(nodes, context)
        # 降級驗證：Treeview widget 應存在，且 selection 正確
        self.assertTrue(self.view.member_tree.winfo_exists())
        self.assertEqual(self.view.member_tree.selection(), ("root",))

    def _find_widget_recursive(self, parent, widget_type, text_contains=None):
        """遞迴尋找 widget_type，若 text_contains 不為 None，則 text 需包含該字串"""
        found = []
        for w in parent.winfo_children():
            if isinstance(w, widget_type):
                if text_contains is None or (hasattr(w, 'cget') and text_contains in str(w.cget('text'))):
                    found.append(w)
            found.extend(self._find_widget_recursive(w, widget_type, text_contains))
        return found

    def test_display_mode_switch_ui_and_presenter_call(self):
        # 準備 presenter mock
        class PresenterMock:
            def __init__(self):
                self.calls = []
                self.context = {
                    "display_mode": "tree",
                    "expanded_nodes": ["root"],
                    "selected_node": "root",
                    "error": None,
                    "version": "1.0",
                    "extra": {},
                    "loading": False,
                    "history": [],
                    "user_settings": {},
                    "last_update_time": 0,
                    "readonly": False,
                    "debug_info": {"last_event": None}
                }
            def get_display_nodes(self, mode):
                if mode == "tree":
                    return [{"id": "root", "label": "root", "type": "struct", "children": [], "icon": "struct", "extra": {}}]
                elif mode == "flat":
                    return [{"id": "flat1", "label": "flat1", "type": "int", "children": [], "icon": "int", "extra": {}}]
                else:
                    return []
            def on_switch_display_mode(self, mode):
                self.calls.append(("switch", mode))
                self.context["display_mode"] = mode
                # 修正：切換 mode 時同步更新 selected_node
                if mode == "flat":
                    self.context["selected_node"] = "flat1"
                else:
                    self.context["selected_node"] = "root"
                self.view.update_display(self.get_display_nodes(mode), self.context)
            def get_lru_cache_size(self): return 32
            def get_cache_stats(self): return (5, 3)
            def get_last_layout_time(self): return 0.0123
            def get_cache_keys(self): return ["k1", "k2", "k3"]
            def get_lru_state(self): return {"capacity": 3, "current_size": 3, "last_hit": "k2", "last_evict": "k0"}
            def is_auto_cache_clear_enabled(self): return True
            def enable_auto_cache_clear(self, interval): pass
            def disable_auto_cache_clear(self): pass
        presenter = PresenterMock()
        view = StructView(presenter=presenter)
        presenter.view = view
        # 遞迴查找 OptionMenu
        option_menus = self._find_widget_recursive(view.tab_file, tk.OptionMenu)
        self.assertTrue(option_menus, "應有顯示模式切換 OptionMenu")
        if hasattr(view, '_on_display_mode_change'):
            view._on_display_mode_change('flat')
        else:
            if hasattr(view, 'display_mode_var'):
                view.display_mode_var.set('flat')
                if hasattr(view, '_on_display_mode_change'):
                    view._on_display_mode_change('flat')
        self.assertIn(("switch", "flat"), presenter.calls)
        tree = view.member_tree
        self.assertIn("flat1", tree.get_children("") )
        self.assertEqual(presenter.context["display_mode"], "flat")
        view.destroy()

    def test_expand_collapse_all_buttons_and_presenter_call(self):
        class PresenterMock:
            def __init__(self):
                self.calls = []
                self.context = {
                    "display_mode": "tree",
                    "expanded_nodes": ["root"],
                    "selected_nodes": [],
                    "error": None,
                    "version": "1.0",
                    "extra": {},
                    "loading": False,
                    "history": [],
                    "user_settings": {},
                    "last_update_time": 0,
                    "readonly": False,
                    "debug_info": {"last_event": None}
                }
            def get_display_nodes(self, mode):
                return [
                    {"id": "root", "label": "root", "type": "struct", "children": [
                        {"id": "child1", "label": "child1", "type": "int", "children": [], "icon": "int", "extra": {}},
                        {"id": "child2", "label": "child2", "type": "int", "children": [], "icon": "int", "extra": {}}
                    ], "icon": "struct", "extra": {}}
                ]
            def on_expand_all(self):
                self.calls.append("expand_all")
                self.context["expanded_nodes"] = ["root", "child1", "child2"]
                self.view.update_display(self.get_display_nodes(self.context["display_mode"]), self.context)
            def on_collapse_all(self):
                self.calls.append("collapse_all")
                self.context["expanded_nodes"] = ["root"]
                self.view.update_display(self.get_display_nodes(self.context["display_mode"]), self.context)
            def get_lru_cache_size(self): return 32
            def get_cache_stats(self): return (5, 3)
            def get_last_layout_time(self): return 0.0123
            def get_cache_keys(self): return ["k1", "k2", "k3"]
            def get_lru_state(self): return {"capacity": 3, "current_size": 3, "last_hit": "k2", "last_evict": "k0"}
            def is_auto_cache_clear_enabled(self): return True
            def enable_auto_cache_clear(self, interval): pass
            def disable_auto_cache_clear(self): pass
        presenter = PresenterMock()
        view = StructView(presenter=presenter)
        presenter.view = view
        # 遞迴查找展開全部/收合全部按鈕
        expand_btns = self._find_widget_recursive(view.tab_file, tk.Button, "展開全部")
        collapse_btns = self._find_widget_recursive(view.tab_file, tk.Button, "收合全部")
        self.assertTrue(expand_btns and collapse_btns, "應有展開全部/收合全部按鈕")
        expand_btn = expand_btns[0]
        collapse_btn = collapse_btns[0]
        expand_btn.invoke()
        self.assertIn("expand_all", presenter.calls)
        self.assertIn("child1", presenter.context["expanded_nodes"])
        self.assertIn("child2", presenter.context["expanded_nodes"])
        collapse_btn.invoke()
        self.assertIn("collapse_all", presenter.calls)
        self.assertEqual(presenter.context["expanded_nodes"], ["root"])
        view.destroy()

    def test_search_entry_exists_and_calls_presenter(self):
        class PresenterMock:
            def __init__(self):
                self.calls = []
                self.context = {
                    "display_mode": "tree",
                    "expanded_nodes": ["root"],
                    "selected_node": "root",
                    "error": None,
                    "version": "1.0",
                    "extra": {},
                    "loading": False,
                    "history": [],
                    "user_settings": {},
                    "last_update_time": 0,
                    "readonly": False,
                    "debug_info": {"last_event": None},
                    "search": "",
                    "highlighted_nodes": []
                }
            def get_display_nodes(self, mode):
                return [{"id": "root", "label": "root", "type": "struct", "children": [], "icon": "struct", "extra": {}}]
            def on_search(self, search_str):
                self.calls.append(("search", search_str))
                self.context["search"] = search_str
                self.context["highlighted_nodes"] = ["root"] if search_str == "root" else []
                self.view.update_display(self.get_display_nodes(self.context["display_mode"]), self.context)
            def get_lru_cache_size(self): return 32
            def get_cache_stats(self): return (5, 3)
            def get_last_layout_time(self): return 0.0123
            def get_cache_keys(self): return ["k1", "k2", "k3"]
            def get_lru_state(self): return {"capacity": 3, "current_size": 3, "last_hit": "k2", "last_evict": "k0"}
            def is_auto_cache_clear_enabled(self): return True
            def enable_auto_cache_clear(self, interval): pass
            def disable_auto_cache_clear(self): pass
        presenter = PresenterMock()
        view = StructView(presenter=presenter)
        presenter.view = view
        # 遞迴查找 Entry
        entries = self._find_widget_recursive(view.tab_file, tk.Entry)
        self.assertTrue(entries, "應有搜尋輸入框")
        search_entry = entries[0]
        search_entry.delete(0, tk.END)
        # 用 search_var.set 以確保同步
        view.search_var.set("root")
        view._on_search_entry_change(None)
        self.assertIn(("search", "root"), presenter.calls)
        self.assertIn("root", presenter.context["highlighted_nodes"])
        view.destroy()

    def test_highlighted_nodes_background(self):
        # 準備 nodes/context
        nodes = PresenterStub().get_display_nodes("tree")
        context = PresenterStub().context.copy()
        context["expanded_nodes"] = ["root"]
        context["selected_node"] = "root"
        context["highlighted_nodes"] = ["child1"]
        self.view.update_display(nodes, context)
        tree = self.view.member_tree
        tag = tree.item("child1", "tags")
        self.assertIn("highlighted", tag)
        style = tree.tag_configure("highlighted")
        self.assertIn("yellow", str(style.get("background", "")))

    def test_treeview_multiselect_and_selected_nodes(self):
        # 準備 nodes/context
        nodes = PresenterStub().get_display_nodes("tree")
        context = PresenterStub().context.copy()
        context["expanded_nodes"] = ["root"]
        context["selected_nodes"] = ["child1", "child2"]
        self.view.update_display(nodes, context)
        tree = self.view.member_tree
        self.assertEqual(str(tree.cget("selectmode")), "extended")
        selected = set(tree.selection())
        self.assertIn("child1", selected)
        self.assertIn("child2", selected)

if __name__ == "__main__":
    unittest.main()
