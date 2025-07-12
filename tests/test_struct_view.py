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

if __name__ == "__main__":
    unittest.main()
