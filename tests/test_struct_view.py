import os
import unittest
import tkinter as tk
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'), reason="No display found, skipping GUI tests"
)

from src.view.struct_view import StructView

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

    def test_add_and_delete_bitfield(self):
        self.view._add_bitfield()
        self.assertEqual(len(self.view.bitfields), 1)
        self.view.bitfields[0]["name_var"].set("foo")
        self.view.bitfields[0]["length_var"].set(7)
        self.assertEqual(self.view.bitfields[0]["name"], "foo")
        self.assertEqual(self.view.bitfields[0]["length"], 7)
        self.view._delete_bitfield(0)
        self.assertEqual(len(self.view.bitfields), 0)

    def test_get_manual_struct_definition(self):
        self.view.size_var.set(24)
        self.view.bitfields.append({"name": "a", "length": 8})
        self.view.bitfields.append({"name": "b", "length": 16})
        struct_data = self.view.get_manual_struct_definition()
        self.assertEqual(struct_data["total_size"], 24)
        self.assertEqual(struct_data["members"], [{"name": "a", "length": 8}, {"name": "b", "length": 16}])

    def test_show_manual_struct_validation(self):
        self.view.show_manual_struct_validation(["錯誤1", "錯誤2"])
        self.assertIn("錯誤1", self.view.validation_label.cget("text"))
        self.view.show_manual_struct_validation([])
        self.assertIn("設定正確", self.view.validation_label.cget("text"))

    def test_export_button_triggers_presenter(self):
        self.view.on_export_manual_struct()
        self.assertTrue(self.presenter.export_called)

    def test_move_bitfield_up(self):
        # 新增三個 bitfield
        self.view.bitfields = [
            {"name": "a", "length": 8},
            {"name": "b", "length": 8},
            {"name": "c", "length": 8},
        ]
        self.view._render_bitfield_table()
        # 對 b 執行上移
        self.view._move_bitfield_up(1)
        names = [bf["name"] for bf in self.view.bitfields]
        self.assertEqual(names, ["b", "a", "c"])

    def test_move_bitfield_down(self):
        self.view.bitfields = [
            {"name": "a", "length": 8},
            {"name": "b", "length": 8},
            {"name": "c", "length": 8},
        ]
        self.view._render_bitfield_table()
        # 對 b 執行下移
        self.view._move_bitfield_down(1)
        names = [bf["name"] for bf in self.view.bitfields]
        self.assertEqual(names, ["a", "c", "b"])

    def test_move_bitfield_up_at_top_noop(self):
        self.view.bitfields = [
            {"name": "a", "length": 8},
            {"name": "b", "length": 8},
        ]
        self.view._render_bitfield_table()
        # 對第一個執行上移，應無變化
        self.view._move_bitfield_up(0)
        names = [bf["name"] for bf in self.view.bitfields]
        self.assertEqual(names, ["a", "b"])

    def test_move_bitfield_down_at_bottom_noop(self):
        self.view.bitfields = [
            {"name": "a", "length": 8},
            {"name": "b", "length": 8},
        ]
        self.view._render_bitfield_table()
        # 對最後一個執行下移，應無變化
        self.view._move_bitfield_down(1)
        names = [bf["name"] for bf in self.view.bitfields]
        self.assertEqual(names, ["a", "b"])

    def test_struct_name_input_and_export(self):
        # 設定 struct 名稱
        self.view.struct_name_var.set("MyStruct")
        self.view.bitfields = [
            {"name": "a", "length": 8},
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
        self.view.bitfields = [
            {"name": "a", "length": 8},
        ]
        self.view.size_var.set(8)
        self.view.on_export_manual_struct()
        self.assertEqual(self.presenter.last_struct_data.get('struct_name'), "MyStruct")

    def test_copy_bitfield_creates_duplicate(self):
        self.view.bitfields = [
            {"name": "a", "length": 8},
            {"name": "b", "length": 16},
        ]
        self.view._render_bitfield_table()
        # 複製第一個欄位
        self.view._copy_bitfield(0)
        self.assertEqual(len(self.view.bitfields), 3)
        self.assertEqual(self.view.bitfields[0]["name"], "a")
        self.assertEqual(self.view.bitfields[1]["name"], "a_copy")
        self.assertEqual(self.view.bitfields[1]["length"], 8)
        self.assertEqual(self.view.bitfields[2]["name"], "b")

    def test_copy_bitfield_auto_rename(self):
        self.view.bitfields = [
            {"name": "a", "length": 8},
            {"name": "a_copy", "length": 8},
        ]
        self.view._render_bitfield_table()
        # 複製第一個欄位
        self.view._copy_bitfield(0)
        self.assertEqual(self.view.bitfields[1]["name"], "a_copy2")

    def test_duplicate_name_highlight_and_error(self):
        self.view.bitfields = [
            {"name": "a", "length": 8},
            {"name": "a", "length": 16},
        ]
        self.view._render_bitfield_table()
        self.view.show_manual_struct_validation(["成員名稱 'a' 重複"])
        # 應有高亮（紅底）與錯誤訊息
        for idx, bf in enumerate(self.view.bitfields):
            entry = self.view.bitfield_frame.grid_slaves(row=idx+1, column=1)[0]
            self.assertEqual(entry.cget("bg"), "#ffcccc")
        # 應有錯誤訊息顯示
        self.assertIn("重複", self.view.validation_label.cget("text"))

    def test_invalid_length_highlight_and_error(self):
        self.view.bitfields = [
            {"name": "a", "length": 0},
            {"name": "b", "length": -1},
        ]
        self.view._render_bitfield_table()
        self.view.show_manual_struct_validation(["bitfield 'a' 長度需為正整數", "bitfield 'b' 長度需為正整數"])
        # 應有高亮（紅底）
        for idx, bf in enumerate(self.view.bitfields):
            entry = self.view.bitfield_frame.grid_slaves(row=idx+1, column=2)[0]
            self.assertEqual(entry.cget("bg"), "#ffcccc")
        # 應有錯誤訊息顯示
        self.assertIn("長度需為正整數", self.view.validation_label.cget("text"))

    def test_error_highlight_clears_on_fix(self):
        self.view.bitfields = [
            {"name": "a", "length": 8},
            {"name": "a", "length": 16},
        ]
        self.view._render_bitfield_table()
        self.view.show_manual_struct_validation(["成員名稱 'a' 重複"])
        # 修正名稱
        self.view.bitfields[1]["name"] = "b"
        self.view._render_bitfield_table()
        self.view.show_manual_struct_validation([])
        # 應無高亮
        for idx, bf in enumerate(self.view.bitfields):
            entry = self.view.bitfield_frame.grid_slaves(row=idx+1, column=1)[0]
            self.assertNotEqual(entry.cget("bg"), "#ffcccc")
        # 應無錯誤訊息
        self.assertIn("設定正確", self.view.validation_label.cget("text"))

    def test_hex_grid_last_entry_dynamic_length(self):
        # struct 9 byte, unit_size 4
        total_size = 9
        unit_size = 4
        self.view.rebuild_hex_grid(total_size, unit_size)
        # 應有 3 格
        self.assertEqual(len(self.view.hex_entries), 3)
        # 前兩格應該是 8 hex 字元，最後一格應該是 2 hex 字元
        self.assertEqual(self.view.hex_entries[0][1], 8)
        self.assertEqual(self.view.hex_entries[1][1], 8)
        self.assertEqual(self.view.hex_entries[2][1], 2)

    def test_show_manual_struct_validation_remaining_bits(self):
        # Case 1: 剛好填滿
        self.view.size_var.set(2)  # 2 bytes = 16 bits
        self.view.members = [
            {"name": "a", "byte_size": 1, "bit_size": 0},  # 8 bits
            {"name": "b", "byte_size": 0, "bit_size": 8}, # 8 bits
        ]
        self.view.show_manual_struct_validation([])
        label = self.view.validation_label.cget("text")
        self.assertIn("剩餘可用空間：0 bits（0 bytes）", label)

        # Case 2: 有剩餘空間
        self.view.size_var.set(2)  # 2 bytes = 16 bits
        self.view.members = [
            {"name": "a", "byte_size": 1, "bit_size": 0},  # 8 bits
        ]
        self.view.show_manual_struct_validation([])
        label = self.view.validation_label.cget("text")
        self.assertIn("剩餘可用空間：8 bits（1 bytes）", label)

        # Case 3: 空 struct
        self.view.size_var.set(2)
        self.view.members = []
        self.view.show_manual_struct_validation([])
        label = self.view.validation_label.cget("text")
        self.assertIn("剩餘可用空間：16 bits（2 bytes）", label)

if __name__ == "__main__":
    unittest.main()
