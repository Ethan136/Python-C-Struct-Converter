import os
import unittest
import pytest
import tkinter as tk

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'), reason="No display found, skipping GUI tests"
)

from src.view.struct_view import StructView


class TestStructViewInsertValuesType(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.view = StructView()

    def tearDown(self):
        self.view.destroy()
        self.root.destroy()

    def test_member_tree_insert_values_are_strings(self):
        # Minimal nodes with value/offset/size present as strings
        nodes = [{
            "id": "root",
            "label": "RootStruct",
            "type": "struct",
            "value": "",
            "offset": "",
            "size": "",
            "children": [
                {"id": "root.a", "label": "a", "type": "int", "value": "1", "offset": "0", "size": "4", "children": []}
            ],
        }]
        context = {"highlighted_nodes": []}
        # Update display to populate tree
        self.view.update_display(nodes, context)
        tree = self.view.member_tree
        # Verify values are tuple of strings
        item_id = 'root.a'
        values = tree.item(item_id, 'values')
        self.assertIsInstance(values, tuple)
        for v in values:
            self.assertIsInstance(v, str)


if __name__ == '__main__':
    unittest.main()

