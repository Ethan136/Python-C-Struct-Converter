import unittest
from unittest.mock import MagicMock
from presenter.struct_presenter import StructPresenter, HexProcessingError

class TestStructPresenter(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.view = MagicMock()
        self.presenter = StructPresenter(self.model, self.view)

    def test_validate_manual_struct_calls_model_and_returns_errors(self):
        struct_data = {"members": [{"name": "a", "length": 8}], "total_size": 8}
        self.model.validate_manual_struct.return_value = ["錯誤訊息"]
        errors = self.presenter.validate_manual_struct(struct_data)
        self.model.validate_manual_struct.assert_called_once_with(struct_data["members"], struct_data["total_size"])
        self.assertEqual(errors, ["錯誤訊息"])

    def test_on_manual_struct_change_triggers_validation_and_view(self):
        struct_data = {"members": [{"name": "a", "length": 8}], "total_size": 8}
        self.model.validate_manual_struct.return_value = ["錯誤訊息"]
        self.presenter.on_manual_struct_change(struct_data)
        self.view.show_manual_struct_validation.assert_called_once_with(["錯誤訊息"])
        # 驗證通過時
        self.model.validate_manual_struct.return_value = []
        self.presenter.on_manual_struct_change(struct_data)
        self.view.show_manual_struct_validation.assert_called_with([])

    def test_on_export_manual_struct_calls_model_and_view(self):
        self.model.export_manual_struct_to_h.return_value = "struct ManualStruct { ... }"
        self.presenter.on_export_manual_struct()
        self.model.export_manual_struct_to_h.assert_called_once()
        self.view.show_exported_struct.assert_called_once_with("struct ManualStruct { ... }")

    def test_process_hex_parts(self):
        hex_parts = [("1", 2), ("2", 2)]
        hex_data, debug_lines = self.presenter._process_hex_parts(hex_parts, "big")
        self.assertEqual(hex_data, "0102")
        self.assertEqual(debug_lines[0], "Box 1 (1 bytes): 01")
        self.assertEqual(debug_lines[1], "Box 2 (1 bytes): 02")

    def test_process_hex_parts_invalid_input(self):
        with self.assertRaises(HexProcessingError) as cm:
            self.presenter._process_hex_parts([("zz", 2)], "big")
        self.assertEqual(cm.exception.kind, "invalid_input")

    def test_layout_cache_hit_and_miss(self):
        # 模擬 model 回傳不同 layout
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        m2 = [{"name": "a", "type": "char", "bit_size": 0}, {"name": "b", "type": "int", "bit_size": 0}]
        l1 = self.presenter.compute_member_layout(m1, 8)
        l2 = self.presenter.compute_member_layout(m1, 8)
        self.assertIs(l1, l2)  # cache hit
        l3 = self.presenter.compute_member_layout(m2, 8)
        self.assertIsNot(l3, l1)  # cache miss

    def test_layout_cache_invalidation(self):
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        l1 = self.presenter.compute_member_layout(m1, 8)
        self.presenter.invalidate_cache()
        l2 = self.presenter.compute_member_layout(m1, 8)
        self.assertIsNot(l1, l2)  # cache miss after invalidation

    def test_layout_cache_performance(self):
        call_count = 0
        def fake_layout(m, s):
            nonlocal call_count
            call_count += 1
            return [dict(name=x['name'], size=1) for x in m]
        self.model.calculate_manual_layout.side_effect = fake_layout
        m = [{"name": f"f{i}", "type": "int", "bit_size": 0} for i in range(100)]
        for _ in range(20):
            self.presenter.compute_member_layout(m, 128)
        self.assertEqual(call_count, 1)  # 只計算一次

if __name__ == "__main__":
    unittest.main() 