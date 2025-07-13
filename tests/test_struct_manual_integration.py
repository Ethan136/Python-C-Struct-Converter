import unittest
from model.struct_model import StructModel

class TestManualStructIntegration(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()

    def test_manual_struct_full_flow(self):
        # 1. 設定手動 struct - 使用 byte_size 而不是 length
        members = [
            {"name": "a", "byte_size": 0, "bit_size": 3},
            {"name": "b", "byte_size": 0, "bit_size": 5},
            {"name": "c", "byte_size": 0, "bit_size": 8}
        ]
        total_size = 4  # C++ align 4
        self.model.set_manual_struct(members, total_size)

        # 2. 驗證
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertEqual(errors, [])

        # 3. 計算 layout
        layout = self.model.calculate_manual_layout(members, total_size)
        # 應該有 3 個 bitfield 成員，全部在 offset=0, type=unsigned int, size=4
        for i, (name, bit_offset, bit_size) in enumerate([
            ("a", 0, 3), ("b", 3, 5), ("c", 8, 8)
        ]):
            self.assertEqual(layout[i]["name"], name)
            self.assertEqual(layout[i]["type"], "unsigned int")
            self.assertEqual(layout[i]["offset"], 0)
            self.assertEqual(layout[i]["size"], 4)
            self.assertEqual(layout[i]["bit_offset"], bit_offset)
            self.assertEqual(layout[i]["bit_size"], bit_size)
        # 檢查 struct 總大小是否為 4 bytes (32 bits)
        storage_unit_size = layout[0]["size"]
        self.assertEqual(storage_unit_size, 4)

        # 4. 匯出 .h 檔
        h_content = self.model.export_manual_struct_to_h()
        self.assertIn("struct MyStruct", h_content)
        self.assertIn("unsigned int a : 3;", h_content)
        self.assertIn("unsigned int b : 5;", h_content)
        self.assertIn("unsigned int c : 8;", h_content)
        self.assertIn("// total size: 4 bytes", h_content)

if __name__ == "__main__":
    unittest.main() 