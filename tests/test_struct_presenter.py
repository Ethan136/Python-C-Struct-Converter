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

if __name__ == "__main__":
    unittest.main() 