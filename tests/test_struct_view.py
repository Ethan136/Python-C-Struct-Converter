import os
import unittest
import tkinter as tk
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'), reason="No display found, skipping GUI tests"
)

from src.view.struct_view import StructView
from src.presenter.struct_presenter import StructPresenter

class PresenterStub:
    def __init__(self):
        self.last_struct_data = None
        self.export_called = False
    def on_manual_struct_change(self, struct_data):
        self.last_struct_data = struct_data
    def on_export_manual_struct(self):
        self.export_called = True

class TestStructView(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 不顯示主視窗
        self.presenter = PresenterStub()
        self.view = StructView(presenter=self.presenter)
        self.view.update()  # 初始化UI

    def tearDown(self):
        self.view.destroy()
        self.root.destroy()

    def test_add_and_delete_member(self):
        # 先設定一個舊格式的成員，確保後續新增的成員也是舊格式
        self.view.members = [{"name": "", "byte_size": 0, "bit_size": 0}]
        self.view._render_member_table()
        
        self.view._add_member()
        self.assertEqual(len(self.view.members), 2)
        self.view.members[1]["name_var"].set("foo")
        self.view.members[1]["byte_var"].set(7)
        self.assertEqual(self.view.members[1]["name"], "foo")
        self.assertEqual(self.view.members[1]["byte_size"], 7)
        self.view._delete_member(1)
        self.assertEqual(len(self.view.members), 1)

    def test_get_manual_struct_definition(self):
        self.view.size_var.set(24)
        self.view.members.append({"name": "a", "byte_size": 8, "bit_size": 0})
        self.view.members.append({"name": "b", "byte_size": 16, "bit_size": 0})
        struct_data = self.view.get_manual_struct_definition()
        self.assertEqual(struct_data["total_size"], 24)
        self.assertEqual(struct_data["members"], [{"name": "a", "byte_size": 8, "bit_size": 0}, {"name": "b", "byte_size": 16, "bit_size": 0}])

    def test_show_manual_struct_validation(self):
        self.view.show_manual_struct_validation(["錯誤1", "錯誤2"])
        self.assertIn("錯誤1", self.view.validation_label.cget("text"))
        self.view.show_manual_struct_validation([])
        self.assertIn("設定正確", self.view.validation_label.cget("text"))

    def test_export_button_triggers_presenter(self):
        self.view.on_export_manual_struct()
        self.assertTrue(self.presenter.export_called)

    def test_move_member_up(self):
        # 新增三個 member
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},
            {"name": "b", "byte_size": 8, "bit_size": 0},
            {"name": "c", "byte_size": 8, "bit_size": 0},
        ]
        self.view._render_member_table()
        # 對 b 執行上移
        self.view._move_member_up(1)
        names = [m["name"] for m in self.view.members]
        self.assertEqual(names, ["b", "a", "c"])

    def test_move_member_down(self):
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},
            {"name": "b", "byte_size": 8, "bit_size": 0},
            {"name": "c", "byte_size": 8, "bit_size": 0},
        ]
        self.view._render_member_table()
        # 對 b 執行下移
        self.view._move_member_down(1)
        names = [m["name"] for m in self.view.members]
        self.assertEqual(names, ["a", "c", "b"])

    def test_move_member_up_at_top_noop(self):
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},
            {"name": "b", "byte_size": 8, "bit_size": 0},
        ]
        self.view._render_member_table()
        # 對第一個執行上移，應無變化
        self.view._move_member_up(0)
        names = [m["name"] for m in self.view.members]
        self.assertEqual(names, ["a", "b"])

    def test_move_member_down_at_bottom_noop(self):
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},
            {"name": "b", "byte_size": 8, "bit_size": 0},
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
            {"name": "a", "byte_size": 8, "bit_size": 0},
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
            {"name": "a", "byte_size": 8, "bit_size": 0},
        ]
        self.view.size_var.set(8)
        self.view.on_export_manual_struct()
        self.assertEqual(self.presenter.last_struct_data.get('struct_name'), "MyStruct")

    def test_copy_member_creates_duplicate(self):
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},
            {"name": "b", "byte_size": 16, "bit_size": 0},
        ]
        self.view._render_member_table()
        # 複製第一個欄位
        self.view._copy_member(0)
        self.assertEqual(len(self.view.members), 3)
        self.assertEqual(self.view.members[0]["name"], "a")
        self.assertEqual(self.view.members[1]["name"], "a_copy")
        self.assertEqual(self.view.members[1]["byte_size"], 8)
        self.assertEqual(self.view.members[2]["name"], "b")

    def test_copy_member_auto_rename(self):
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},
            {"name": "a_copy", "byte_size": 8, "bit_size": 0},
        ]
        self.view._render_member_table()
        # 複製第一個欄位
        self.view._copy_member(0)
        self.assertEqual(self.view.members[1]["name"], "a_copy2")

    def test_duplicate_name_highlight_and_error(self):
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},
            {"name": "a", "byte_size": 16, "bit_size": 0},
        ]
        self.view._render_member_table()
        self.view.show_manual_struct_validation(["成員名稱 'a' 重複"])
        # 應有錯誤訊息顯示
        self.assertIn("重複", self.view.validation_label.cget("text"))

    def test_invalid_length_highlight_and_error(self):
        self.view.members = [
            {"name": "a", "byte_size": 0, "bit_size": 0},
            {"name": "b", "byte_size": -1, "bit_size": 0},
        ]
        self.view._render_member_table()
        self.view.show_manual_struct_validation(["member 'a' 長度需為正整數", "member 'b' 長度需為正整數"])
        # 應有錯誤訊息顯示
        self.assertIn("長度需為正整數", self.view.validation_label.cget("text"))

    def test_error_highlight_clears_on_fix(self):
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},
            {"name": "a", "byte_size": 16, "bit_size": 0},
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
        self.view.size_var.set(8)  # 64 bits
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},  # 64 bits
        ]
        self.view.show_manual_struct_validation([])
        self.assertIn("剩餘可用空間：0 bits", self.view.validation_label.cget("text"))

        # Case 2: 有剩餘空間
        self.view.size_var.set(16)  # 128 bits
        self.view.members = [
            {"name": "a", "byte_size": 8, "bit_size": 0},  # 64 bits
        ]
        self.view.show_manual_struct_validation([])
        self.assertIn("剩餘可用空間：64 bits", self.view.validation_label.cget("text"))

    def test_manual_struct_offset_display_byte_plus_bit(self):
        # 設定一組 byte/bit size 混合的 members
        self.view.size_var.set(8)
        self.view.members = [
            {"name": "a", "byte_size": 4, "bit_size": 0},  # int
            {"name": "b", "byte_size": 1, "bit_size": 0},  # char
            {"name": "c", "byte_size": 2, "bit_size": 0},  # short
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

    def test_manual_struct_hex_input_and_parse_debug(self):
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        # 設定 struct size 與 unit size
        self.view.size_var.set(8)
        self.view.manual_unit_size_var.set("4 Bytes")
        self.view._rebuild_manual_hex_grid()
        # 輸入 hex raw data
        for idx, (entry, box_len) in enumerate(self.view.manual_hex_entries):
            entry.delete(0, "end")
            entry.insert(0, "12".zfill(box_len))
        # 點擊解析
        self.view._on_parse_manual_hex()
        # 檢查 debug 區有正確顯示 hex_parts
        debug_text = self.view.manual_debug_text.get("1.0", "end")
        self.assertIn("hex_parts", debug_text)
        self.assertIn("12", debug_text)

    def test_manual_struct_hex_parse_shows_member_value(self):
        # 模擬 presenter 支援解析
        class PresenterWithParse:
            def __init__(self, view):
                self.view = view
            def parse_manual_hex_data(self, hex_parts, struct_def, endian):
                # 假設 struct 有一個 int 欄位，hex_parts = [("01020304", 8)]
                # 解析 hex 並顯示在 manual_member_tree
                value = int(hex_parts[0][0], 16)
                self.view.manual_member_tree.delete(*self.view.manual_member_tree.get_children())
                self.view.manual_member_tree.insert("", "end", values=(struct_def["members"][0]["name"], str(value), hex(value), hex_parts[0][0]))
                self.view.manual_debug_text.config(state="normal")
                self.view.manual_debug_text.delete("1.0", "end")
                self.view.manual_debug_text.insert("1.0", f"value: {value}")
                self.view.manual_debug_text.config(state="disabled")
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
                # struct: int(4 bytes), char(1), short(2)
                hex_str = ''.join([h[0] for h in hex_parts])
                # 4+1+2=7 bytes, 例如: 01020304 61 0b0c (int=0x01020304, char='a'=0x61, short=0x0b0c)
                b = bytes.fromhex(hex_str)
                if endian == 'Little Endian':
                    int_val = int.from_bytes(b[0:4], 'little')
                    char_val = chr(b[4])
                    short_val = int.from_bytes(b[5:7], 'little')
                else:
                    int_val = int.from_bytes(b[0:4], 'big')
                    char_val = chr(b[4])
                    short_val = int.from_bytes(b[5:7], 'big')
                self.view.manual_member_tree.delete(*self.view.manual_member_tree.get_children())
                self.view.manual_member_tree.insert("", "end", values=(struct_def["members"][0]["name"], str(int_val), hex(int_val), hex_str[0:8]))
                self.view.manual_member_tree.insert("", "end", values=(struct_def["members"][1]["name"], char_val, hex(ord(char_val)), hex_str[8:10]))
                self.view.manual_member_tree.insert("", "end", values=(struct_def["members"][2]["name"], str(short_val), hex(short_val), hex_str[10:14]))
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
        # 取得 scrollable_frame
        canvas = [w for w in self.view.tab_manual.winfo_children() if isinstance(w, tk.Canvas)][0]
        scrollable_frame = canvas.winfo_children()[0]
        children = scrollable_frame.winfo_children()
        # 找出 member_frame 與 manual_hex_grid_frame 的順序
        member_idx = [i for i, w in enumerate(children) if w is self.view.member_frame]
        hex_idx = [i for i, w in enumerate(children) if w is self.view.manual_hex_grid_frame]
        self.assertTrue(member_idx and hex_idx and member_idx[0] < hex_idx[0])

    def test_tab_has_scrollbar(self):
        # 檢查 MyStruct tab 右側有 scroll bar
        self.view.tab_control.select(self.view.tab_manual)
        # 應有一個 Scrollbar widget
        scrollbars = [w for w in self.view.tab_manual.winfo_children() if isinstance(w, tk.Scrollbar)]
        self.assertTrue(scrollbars)

    def test_manual_struct_hex_parse_real_model(self):
        # 使用真實 presenter/model 串接
        from src.model.struct_model import StructModel
        class RealPresenter:
            def __init__(self, view):
                self.view = view
                self.model = StructModel()
            def parse_manual_hex_data(self, hex_parts, struct_def, endian):
                # 將 hex_parts 組成 bytes
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
                    results.append((m['name'], value, hex(value), val_bytes.hex()))
                    offset += size
                self.view.manual_member_tree.delete(*self.view.manual_member_tree.get_children())
                for r in results:
                    self.view.manual_member_tree.insert('', 'end', values=r)
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
        # 直接用 layout offset/size 取 bytes 驗證
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
        self.assertEqual(values1[3], "7b000000", "hex raw 應該正確")
        
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
        self.assertEqual(values3[3], "0201", "hex raw 應該正確")

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

    def test_manual_struct_member_table_shows_size_column(self):
        """測試 MyStruct member 編輯表格有 size 欄位且顯示正確"""
        self.view.tab_control.select(self.view.tab_manual)
        # 設定 struct: int, char, short, bitfield
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0},
            {"name": "c", "type": "short", "bit_size": 0},
            {"name": "d", "type": "int", "bit_size": 3},
        ]
        self.view.size_var.set(12)
        self.view._render_member_table()
        # 取得 member_frame 內所有 row widget
        rows = [w for w in self.view.member_frame.winfo_children() if isinstance(w, tk.Label)]
        # 應有 size 欄位標題
        header_texts = [w.cget("text") for w in rows[:6]]
        self.assertIn("size", ''.join(header_texts).lower())
        # 應有每個欄位的 size 顯示（只讀）
        # 取得所有 size 欄位的值（假設在 column 4）
        size_labels = [w for w in self.view.member_frame.winfo_children() if hasattr(w, 'is_size_label') and w.is_size_label]
        self.assertEqual(len(size_labels), 4)
        # 驗證 int/char/short/bitfield 的 size
        size_texts = [l.cget("text") for l in size_labels]
        # int=4, char=1, short=2, bitfield(int)=4
        self.assertEqual(size_texts, ["4", "1", "2", "4"])

    def test_manual_struct_member_table_size_column_padding(self):
        """測試 struct 有 padding 時，size 欄位顯示正確"""
        self.view.tab_control.select(self.view.tab_manual)
        # 設定 struct: char, int
        self.view.members = [
            {"name": "a", "type": "char", "bit_size": 0},
            {"name": "b", "type": "int", "bit_size": 0},
        ]
        self.view.size_var.set(8)
        self.view._render_member_table()
        # 取得 size 欄位的值
        size_labels = [w for w in self.view.member_frame.winfo_children() if hasattr(w, 'is_size_label') and w.is_size_label]
        # char=1, padding=3, int=4
        self.assertEqual([l.cget("text") for l in size_labels], ["1", "4"])

    def test_manual_struct_gui_bitfield_parsing(self):
        """測試 MyStruct GUI 介面的完整 bitfield 解析流程"""
        from src.model.struct_model import StructModel
        from src.presenter.struct_presenter import StructPresenter
        
        # 建立真實的 presenter 和 model
        model = StructModel()
        presenter = StructPresenter(model, self.view)
        self.view.presenter = presenter
        
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        
        # 設定 struct: 4 bytes, 包含 bitfield 成員
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 1},  # bit 0
            {"name": "b", "type": "int", "bit_size": 3},  # bit 1-3
            {"name": "c", "type": "int", "bit_size": 5}   # bit 4-8
        ]
        self.view.size_var.set(4)  # 4 bytes total
        self.view.manual_unit_size_var.set("1 Byte")  # 1 byte 單位
        
        # 渲染成員表格和重建 hex grid
        self.view._render_member_table()
        self.view._rebuild_manual_hex_grid()
        
        # 驗證 hex grid 有正確的 4 個輸入欄位
        self.assertEqual(len(self.view.manual_hex_entries), 4, "應該有 4 個 hex 輸入欄位")
        
        # 輸入 hex data: box0=1, box1=2, box2=3, box3=4
        hex_inputs = ["1", "2", "3", "4"]
        for (entry, box_len), val in zip(self.view.manual_hex_entries, hex_inputs):
            entry.delete(0, "end")
            entry.insert(0, val.zfill(box_len))
        
        # 設定 endianness
        self.view.manual_endian_var.set("Little Endian")
        
        # 執行解析
        self.view._on_parse_manual_hex()
        
        # 驗證解析結果
        items = self.view.manual_member_tree.get_children()
        self.assertEqual(len(items), 3, "應該有 3 個解析結果")
        
        # 檢查 debug 資訊
        debug_text = self.view.manual_debug_text.get("1.0", "end")
        print(f"Debug text: {debug_text}")
        
        # 檢查實際的解析結果
        for i, item in enumerate(items):
            values = self.view.manual_member_tree.item(item, "values")
            print(f"Member {i}: {values}")
        
        # 驗證 bitfield 解析結果
        # 輸入: 0x01 0x02 0x03 0x04 (little endian)
        # 完整 32-bit 值: 0x04030201 = 67305985
        # 二進位: 00000100 00000011 00000010 00000001
        # 
        # bitfield 解析：
        # a (bit 0): 67305985 & 0x1 = 1
        # b (bit 1-3): (67305985 >> 1) & 0x7 = 0  
        # c (bit 4-8): (67305985 >> 4) & 0x1F = 0
        #
        # 驗證：67305985 >> 4 = 4206624, 4206624 & 31 = 0
        
        # 檢查第一個成員 a
        values_a = self.view.manual_member_tree.item(items[0], "values")
        self.assertEqual(values_a[0], "a", "第一個成員名稱應該是 'a'")
        print(f"Member a actual value: {values_a[1]}, expected: 1")
        self.assertEqual(values_a[1], "1", "成員 a 的值應該是 1")
        
        # 檢查第二個成員 b
        values_b = self.view.manual_member_tree.item(items[1], "values")
        self.assertEqual(values_b[0], "b", "第二個成員名稱應該是 'b'")
        print(f"Member b actual value: {values_b[1]}, expected: 0")
        self.assertEqual(values_b[1], "0", "成員 b 的值應該是 0")
        
        # 檢查第三個成員 c
        values_c = self.view.manual_member_tree.item(items[2], "values")
        self.assertEqual(values_c[0], "c", "第三個成員名稱應該是 'c'")
        print(f"Member c actual value: {values_c[1]}, expected: 0")
        self.assertEqual(values_c[1], "0", "成員 c 的值應該是 0")

    def test_manual_struct_equivalent_to_example_h(self):
        """測試 MyStruct 可以正確處理與 example.h 中 CombinedExample struct 等效的定義"""
        from src.model.struct_model import StructModel
        from src.presenter.struct_presenter import StructPresenter
        
        # 建立真實的 presenter 和 model
        model = StructModel()
        presenter = StructPresenter(model, self.view)
        self.view.presenter = presenter
        
        # 切換到 manual struct tab
        self.view.tab_control.select(self.view.tab_manual)
        
        # 設定與 example.h 中 CombinedExample 等效的 struct
        # struct CombinedExample {
        #     char      a;      // 1 byte
        #     int       b;      // 4 bytes  
        #     int       c1 : 1; // bit field (1 bit)
        #     int       c2 : 2; // bit field (2 bits)
        #     int       c3 : 5; // bit field (5 bits)
        #     char      d;      // 1 byte
        #     long long e;      // 8 bytes
        #     unsigned char f;  // 1 byte
        #     char*     g;      // 8 bytes (pointer)
        # };
        self.view.members = [
            {"name": "a", "type": "char", "bit_size": 0},           # 1 byte
            {"name": "b", "type": "int", "bit_size": 0},            # 4 bytes
            {"name": "c1", "type": "int", "bit_size": 1},           # bit field (1 bit)
            {"name": "c2", "type": "int", "bit_size": 2},           # bit field (2 bits)
            {"name": "c3", "type": "int", "bit_size": 5},           # bit field (5 bits)
            {"name": "d", "type": "char", "bit_size": 0},           # 1 byte
            {"name": "e", "type": "long long", "bit_size": 0},      # 8 bytes
            {"name": "f", "type": "unsigned char", "bit_size": 0},  # 1 byte
            {"name": "g", "type": "pointer", "bit_size": 0},        # 8 bytes (pointer)
        ]
        self.view.size_var.set(40)  # 總大小：1+3(padding)+4+4(bitfield)+1+7(padding)+8+1+7(padding)+8 = 40 bytes
        self.view.manual_unit_size_var.set("1 Byte")  # 1 byte 單位
        
        # 渲染成員表格和重建 hex grid
        self.view._render_member_table()
        self.view._rebuild_manual_hex_grid()
        
        # 驗證 hex grid 有正確的 40 個輸入欄位
        self.assertEqual(len(self.view.manual_hex_entries), 40, "應該有 40 個 hex 輸入欄位")
        
        # 輸入測試 hex data（Little Endian）
        # 模擬實際的記憶體佈局：
        # a=0x41 ('A'), padding=0x00, b=0x01020304, c1=1, c2=2, c3=3, d=0x42 ('B'), 
        # padding=0x00, e=0x0807060504030201, f=0x43 ('C'), padding=0x00, g=0x100f0e0d0c0b0a09
        # 
        # bitfield 計算：
        # c1 (bit 0): 1
        # c2 (bit 1-2): 2 (二進位: 10)
        # c3 (bit 3-7): 3 (二進位: 00011)
        # 組合：00011 10 1 = 00011101 = 0x1D = 29
        hex_inputs = [
            "41",  # a = 'A' (0x41)
            "00", "00", "00",  # padding after char
            "04", "03", "02", "01",  # b = 0x01020304 (little endian)
            "1d", "00", "00", "00",  # c1=1, c2=2, c3=3 (bitfield in int: 0x1D)
            "42",  # d = 'B' (0x42)
            "00", "00", "00",  # padding before long long (3 bytes)
            "01", "02", "03", "04", "05", "06", "07", "08",  # e = 0x0807060504030201 (little endian)
            "43",  # f = 'C' (0x43)
            "00", "00", "00", "00", "00", "00", "00",  # padding before pointer
            "09", "0a", "0b", "0c", "0d", "0e", "0f", "10",  # g = 0x100f0e0d0c0b0a09 (little endian)
        ]
        
        for (entry, box_len), val in zip(self.view.manual_hex_entries, hex_inputs):
            entry.delete(0, "end")
            entry.insert(0, val.zfill(box_len))
        
        # 設定 endianness
        self.view.manual_endian_var.set("Little Endian")
        
        # 執行解析
        self.view._on_parse_manual_hex()
        
        # 驗證解析結果
        items = self.view.manual_member_tree.get_children()
        self.assertEqual(len(items), 12, "應該有 12 個解析結果（包含 padding）")
        
        # 檢查 debug 資訊
        debug_text = self.view.manual_debug_text.get("1.0", "end")
        print(f"Debug text: {debug_text}")
        
        # 檢查實際的解析結果
        for i, item in enumerate(items):
            values = self.view.manual_member_tree.item(item, "values")
            print(f"Member {i}: {values}")
        
        # 驗證各個欄位的解析結果
        # 檢查 char a
        values_a = self.view.manual_member_tree.item(items[0], "values")
        self.assertEqual(values_a[0], "a", "欄位名稱應該是 'a'")
        self.assertEqual(values_a[1], "65", "char a 的值應該是 65 ('A')")
        
        # 檢查 padding
        values_padding1 = self.view.manual_member_tree.item(items[1], "values")
        self.assertEqual(values_padding1[0], "(padding)", "應該是 padding")
        self.assertEqual(values_padding1[1], "-", "padding 值應該是 -")
        
        # 檢查 int b
        values_b = self.view.manual_member_tree.item(items[2], "values")
        self.assertEqual(values_b[0], "b", "欄位名稱應該是 'b'")
        self.assertEqual(values_b[1], str(int("01020304", 16)), "int b 的值應該是 0x01020304")
        
        # 檢查 bitfield c1
        values_c1 = self.view.manual_member_tree.item(items[3], "values")
        self.assertEqual(values_c1[0], "c1", "欄位名稱應該是 'c1'")
        self.assertEqual(values_c1[1], "1", "bitfield c1 的值應該是 1")
        
        # 檢查 bitfield c2
        values_c2 = self.view.manual_member_tree.item(items[4], "values")
        self.assertEqual(values_c2[0], "c2", "欄位名稱應該是 'c2'")
        self.assertEqual(values_c2[1], "2", "bitfield c2 的值應該是 2")
        
        # 檢查 bitfield c3
        values_c3 = self.view.manual_member_tree.item(items[5], "values")
        self.assertEqual(values_c3[0], "c3", "欄位名稱應該是 'c3'")
        self.assertEqual(values_c3[1], "3", "bitfield c3 的值應該是 3")
        
        # 檢查 char d
        values_d = self.view.manual_member_tree.item(items[6], "values")
        self.assertEqual(values_d[0], "d", "欄位名稱應該是 'd'")
        self.assertEqual(values_d[1], "66", "char d 的值應該是 66 ('B')")
        
        # 檢查 padding
        values_padding2 = self.view.manual_member_tree.item(items[7], "values")
        self.assertEqual(values_padding2[0], "(padding)", "應該是 padding")
        self.assertEqual(values_padding2[1], "-", "padding 值應該是 -")
        
        # 檢查 long long e
        values_e = self.view.manual_member_tree.item(items[8], "values")
        self.assertEqual(values_e[0], "e", "欄位名稱應該是 'e'")
        self.assertEqual(values_e[1], str(int("0807060504030201", 16)), "long long e 的值應該是 0x0807060504030201")
        
        # 檢查 unsigned char f
        values_f = self.view.manual_member_tree.item(items[9], "values")
        self.assertEqual(values_f[0], "f", "欄位名稱應該是 'f'")
        self.assertEqual(values_f[1], "67", "unsigned char f 的值應該是 67 ('C')")
        
        # 檢查 padding
        values_padding3 = self.view.manual_member_tree.item(items[10], "values")
        self.assertEqual(values_padding3[0], "(padding)", "應該是 padding")
        self.assertEqual(values_padding3[1], "-", "padding 值應該是 -")
        
        # 檢查 pointer g
        values_g = self.view.manual_member_tree.item(items[11], "values")
        self.assertEqual(values_g[0], "g", "欄位名稱應該是 'g'")
        self.assertEqual(values_g[1], str(int("100f0e0d0c0b0a09", 16)), "pointer g 的值應該是 0x100f0e0d0c0b0a09")
        
        # 驗證 debug 資訊
        self.assertIn("Parsed 12 fields", debug_text, "debug 應該顯示解析了 12 個欄位")
        self.assertIn("Hex data:", debug_text, "debug 應該顯示 hex 資料")
        self.assertIn("Little Endian", debug_text, "debug 應該顯示 endianness")
        
        # 測試 Big Endian
        self.view.manual_endian_var.set("Big Endian")
        self.view._on_parse_manual_hex()
        
        # Big Endian 解析結果驗證（只檢查幾個關鍵欄位）
        items_big = self.view.manual_member_tree.get_children()
        values_b_big = self.view.manual_member_tree.item(items_big[2], "values")
        values_e_big = self.view.manual_member_tree.item(items_big[8], "values")
        
        # Big Endian 下，int b 應該是 0x04030201
        self.assertEqual(values_b_big[1], str(int("04030201", 16)), "Big Endian 下 int b 的值應該是 0x04030201")
        
        # Big Endian 下，long long e 應該是 0x0102030405060708
        self.assertEqual(values_e_big[1], str(int("0102030405060708", 16)), "Big Endian 下 long long e 的值應該是 0x0102030405060708")

if __name__ == "__main__":
    unittest.main()
