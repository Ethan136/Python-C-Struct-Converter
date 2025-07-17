
import unittest
from unittest.mock import MagicMock
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from src.presenter.struct_presenter import StructPresenter
from src.model.struct_model import StructModel

class TestPresenterRefactor(unittest.TestCase):

    def setUp(self):
        self.model = StructModel()
        self.view = MagicMock()
        self.presenter = StructPresenter(self.model, self.view)

    def test_compute_member_layout(self):
        members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0}
        ]
        layout = self.presenter.compute_member_layout(members, 8)
        # 根據 C/C++ 標準，layout 會有 a, b, padding
        self.assertEqual(len(layout), 3)
        names = [item.get("name", "") for item in layout]
        types = [item.get("type", "") for item in layout]
        self.assertIn("a", names)
        self.assertIn("b", names)
        self.assertIn("padding", types)
        # 驗證 a, b 的 size
        for item in layout:
            if item.get("name") == "a":
                self.assertEqual(item["size"], 4)
            if item.get("name") == "b":
                self.assertEqual(item["size"], 1)

    def test_calculate_remaining_space(self):
        members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0}
        ]
        remaining_bits, remaining_bytes = self.presenter.calculate_remaining_space(members, 8)
        self.assertEqual(remaining_bits, 24)
        self.assertEqual(remaining_bytes, 3)

if __name__ == '__main__':
    unittest.main()
