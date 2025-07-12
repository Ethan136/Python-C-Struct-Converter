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

if __name__ == "__main__":
    unittest.main()
