import unittest
from src.model.struct_model import StructModel

class TestManualStructIntegration(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()

    def test_manual_struct_full_flow(self):
        # 1. 設定手動 struct
        members = [
            {"name": "a", "length": 3},
            {"name": "b", "length": 5},
            {"name": "c", "length": 8}
        ]
        total_size = 16
        self.model.set_manual_struct(members, total_size)

        # 2. 驗證
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertEqual(errors, [])

        # 3. 計算 layout
        layout = self.model.calculate_manual_layout(members, total_size)
        self.assertEqual(len(layout), 3)
        self.assertEqual(layout[0]["name"], "a")
        self.assertEqual(layout[1]["name"], "b")
        self.assertEqual(layout[2]["name"], "c")
        self.assertEqual(layout[0]["bit_offset"], 0)
        self.assertEqual(layout[1]["bit_offset"], 3)
        self.assertEqual(layout[2]["bit_offset"], 8)
        self.assertEqual(layout[2]["bit_size"], 8)
        for item in layout:
            self.assertEqual(item["offset"], 0)
            self.assertEqual(item["size"], 2)  # 16 bits = 2 bytes

        # 4. 匯出 .h 檔
        h_content = self.model.export_manual_struct_to_h()
        self.assertIn("struct MyStruct", h_content)
        self.assertIn("unsigned int a : 3;", h_content)
        self.assertIn("unsigned int b : 5;", h_content)
        self.assertIn("unsigned int c : 8;", h_content)
        self.assertIn("// total size: 16 bits", h_content)

if __name__ == "__main__":
    unittest.main() 