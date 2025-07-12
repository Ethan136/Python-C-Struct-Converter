import unittest
import tkinter as tk
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.view.struct_view import StructView
from src.presenter.struct_presenter import StructPresenter
from src.model.struct_model import StructModel

class TestStructViewPadding(unittest.TestCase):
    """測試 GUI 的 struct layout 標準顯示（只顯示下方 Treeview）"""
    
    def setUp(self):
        self.root = tk.Tk()
        self.model = StructModel()
        self.view = StructView()
        self.presenter = StructPresenter(self.model, self.view)
        self.view.presenter = self.presenter
        # 切換到手動設定 tab
        self.view.tab_control.select(self.view.tab_manual)
    
    def tearDown(self):
        self.root.destroy()
    
    def test_only_standard_treeview_layout_in_manual_tab(self):
        """手動設定 tab 只顯示下方標準 struct layout (ttk.Treeview)"""
        # 設定 struct
        self.view.size_var.set(8)
        self.view.members = [
            {"name": "a", "byte_size": 1, "bit_size": 0},
            {"name": "b", "byte_size": 4, "bit_size": 0},
        ]
        self.view._on_manual_struct_change()
        # 應該有 manual_layout_tree 屬性
        self.assertTrue(hasattr(self.view, "manual_layout_tree"), "應有 manual_layout_tree")
        # manual_layout_tree 應該是 ttk.Treeview
        from tkinter import ttk
        self.assertIsInstance(self.view.manual_layout_tree, ttk.Treeview)
        # 應該沒有上方自訂 layout frame
        found_custom_layout = False
        for child in self.view.member_frame.winfo_children():
            if isinstance(child, tk.LabelFrame) and "Memory Layout" in child.cget("text"):
                found_custom_layout = True
        self.assertFalse(found_custom_layout, "不應該有自訂 memory layout 框架")
        # Treeview 內容應該正確顯示 struct layout
        items = self.view.manual_layout_tree.get_children()
        self.assertGreaterEqual(len(items), 2, "Treeview 應該有 struct 成員顯示")
        # 檢查第一個欄位名稱
        first_item = self.view.manual_layout_tree.item(items[0])
        self.assertIn("a", first_item["values"])  # 應有 a 欄位

if __name__ == "__main__":
    unittest.main() 