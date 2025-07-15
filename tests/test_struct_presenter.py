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

    def test_layout_cache_stats(self):
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        m2 = [{"name": "a", "type": "char", "bit_size": 0}, {"name": "b", "type": "int", "bit_size": 0}]
        # First call: miss
        self.presenter.compute_member_layout(m1, 8)
        hits, misses = self.presenter.get_cache_stats()
        self.assertEqual((hits, misses), (0, 1))
        # Second call: hit
        self.presenter.compute_member_layout(m1, 8)
        hits, misses = self.presenter.get_cache_stats()
        self.assertEqual((hits, misses), (1, 1))
        # Third call: new key, miss
        self.presenter.compute_member_layout(m2, 8)
        hits, misses = self.presenter.get_cache_stats()
        self.assertEqual((hits, misses), (1, 2))
        # Invalidate cache resets stats
        self.presenter.invalidate_cache()
        hits, misses = self.presenter.get_cache_stats()
        self.assertEqual((hits, misses), (0, 0))
        # Test reset_cache_stats
        self.presenter.compute_member_layout(m1, 8)
        self.presenter.compute_member_layout(m1, 8)
        self.presenter.reset_cache_stats()
        hits, misses = self.presenter.get_cache_stats()
        self.assertEqual((hits, misses), (0, 0))

    def test_layout_cache_edge_cases(self):
        # Empty members
        self.model.calculate_manual_layout.side_effect = lambda m, s: []
        l1 = self.presenter.compute_member_layout([], 0)
        self.assertEqual(l1, [])
        hits, misses = self.presenter.get_cache_stats()
        self.assertEqual((hits, misses), (0, 1))
        # Call again (should hit cache)
        l2 = self.presenter.compute_member_layout([], 0)
        self.assertIs(l1, l2)
        hits, misses = self.presenter.get_cache_stats()
        self.assertEqual((hits, misses), (1, 1))
        # Very large struct
        big_members = [{"name": f"f{i}", "type": "int", "bit_size": 0} for i in range(1000)]
        self.model.calculate_manual_layout.side_effect = lambda m, s: m
        l3 = self.presenter.compute_member_layout(big_members, 4000)
        self.assertEqual(len(l3), 1000)
        # Invalid member format (should not cache if exception)
        def raise_error(m, s):
            raise ValueError("bad format")
        self.model.calculate_manual_layout.side_effect = raise_error
        with self.assertRaises(ValueError):
            self.presenter.compute_member_layout([{"bad": "field"}], 8)
        # Cache stats should not increment hit/miss for failed call
        hits2, misses2 = self.presenter.get_cache_stats()
        self.assertEqual((hits2, misses2), (1, 2))

    def test_layout_performance_hook(self):
        import time as _time
        self.model.calculate_manual_layout.side_effect = lambda m, s: _time.sleep(0.01) or [dict(name=x['name'], size=1) for x in m]
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        # Before any calculation
        self.assertIsNone(self.presenter.get_last_layout_time())
        # First call: miss, should record time
        self.presenter.compute_member_layout(m1, 8)
        t1 = self.presenter.get_last_layout_time()
        self.assertIsInstance(t1, float)
        self.assertGreater(t1, 0)
        # Second call: hit, time should not change
        self.presenter.compute_member_layout(m1, 8)
        t2 = self.presenter.get_last_layout_time()
        self.assertEqual(t1, t2)
        # New key: miss, time should update
        m2 = [{"name": "b", "type": "char", "bit_size": 0}]
        self.presenter.compute_member_layout(m2, 8)
        t3 = self.presenter.get_last_layout_time()
        self.assertIsInstance(t3, float)
        self.assertGreater(t3, 0)
        self.assertNotEqual(t1, t3)

    def test_parse_manual_hex_data_success(self):
        # Arrange
        hex_parts = [("01", 2), ("02", 2)]
        struct_def = {"members": [{"name": "a", "type": "char", "bit_size": 0}], "total_size": 2, "unit_size": 1}
        self.model.set_manual_struct.return_value = None
        self.model.calculate_manual_layout.return_value = [{"name": "a", "type": "char", "size": 1}]
        self.model.parse_hex_data.return_value = [
            {"name": "a", "value": 1, "hex_value": "0x1", "hex_raw": "01"}
        ]
        # Act
        result = self.presenter.parse_manual_hex_data(hex_parts, struct_def, "Little Endian")
        # Assert
        self.assertEqual(result["type"], "ok")
        self.assertIn("debug_lines", result)
        self.assertIn("parsed_values", result)
        self.assertEqual(result["parsed_values"][0]["name"], "a")
        self.assertEqual(result["parsed_values"][0]["value"], 1)

    def test_parse_manual_hex_data_hex_error(self):
        # Arrange
        hex_parts = [("zz", 2)]
        struct_def = {"members": [{"name": "a", "type": "char", "bit_size": 0}], "total_size": 2, "unit_size": 1}
        # Act
        result = self.presenter.parse_manual_hex_data(hex_parts, struct_def, "Little Endian")
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("無效輸入", result["message"])

    def test_parse_manual_hex_data_model_error(self):
        # Arrange
        hex_parts = [("01", 2)]
        struct_def = {"members": [{"name": "a", "type": "char", "bit_size": 0}], "total_size": 2, "unit_size": 1}
        self.model.set_manual_struct.side_effect = Exception("model error")
        # Act
        result = self.presenter.parse_manual_hex_data(hex_parts, struct_def, "Little Endian")
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("解析 hex 資料時發生錯誤", result["message"])

    def test_parse_hex_data_success(self):
        # Arrange
        self.model.layout = True
        self.model.total_size = 2
        self.model.parse_hex_data.return_value = [
            {"name": "a", "value": 1, "hex_value": "0x1", "hex_raw": "01"}
        ]
        self.view.get_hex_input_parts.return_value = [("01", 2)]
        self.view.get_selected_endianness.return_value = "Little Endian"
        # Act
        result = self.presenter.parse_hex_data()
        # Assert
        self.assertEqual(result["type"], "ok")
        self.assertIn("debug_lines", result)
        self.assertIn("parsed_values", result)
        self.assertEqual(result["parsed_values"][0]["name"], "a")
        self.assertEqual(result["parsed_values"][0]["value"], 1)

    def test_parse_hex_data_no_struct(self):
        # Arrange
        self.model.layout = False
        # Act
        result = self.presenter.parse_hex_data()
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("尚未載入 struct", result["message"])

    def test_parse_hex_data_hex_error(self):
        # Arrange
        self.model.layout = True
        self.model.total_size = 2
        self.view.get_hex_input_parts.return_value = [("zz", 2)]
        self.view.get_selected_endianness.return_value = "Little Endian"
        # Act
        result = self.presenter.parse_hex_data()
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("無效輸入", result["message"])

    def test_parse_hex_data_length_error(self):
        # Arrange
        self.model.layout = True
        self.model.total_size = 1
        self.view.get_hex_input_parts.return_value = [("0102", 4)]  # 4 chars > 2
        self.view.get_selected_endianness.return_value = "Little Endian"
        # Act
        result = self.presenter.parse_hex_data()
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("超過預期總大小", result["message"])

    def test_parse_hex_data_model_error(self):
        # Arrange
        self.model.layout = True
        self.model.total_size = 2
        self.model.parse_hex_data.side_effect = Exception("model error")
        self.view.get_hex_input_parts.return_value = [("01", 2)]
        self.view.get_selected_endianness.return_value = "Little Endian"
        # Act
        result = self.presenter.parse_hex_data()
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("解析 hex 資料時發生錯誤", result["message"])

    def test_browse_file_success(self):
        from unittest.mock import patch, mock_open
        # Arrange
        with patch('presenter.struct_presenter.filedialog.askopenfilename', return_value='test.h'):
            with patch('builtins.open', mock_open(read_data='struct content')):
                self.model.load_struct_from_file.return_value = ('MyStruct', [{'name': 'a'}], 8, 4)
                # Act
                result = self.presenter.browse_file()
        # Assert
        self.assertEqual(result['type'], 'ok')
        self.assertEqual(result['file_path'], 'test.h')
        self.assertEqual(result['struct_name'], 'MyStruct')
        self.assertEqual(result['layout'], [{'name': 'a'}])
        self.assertEqual(result['total_size'], 8)
        self.assertEqual(result['struct_align'], 4)
        self.assertEqual(result['struct_content'], 'struct content')

    def test_browse_file_cancel(self):
        from unittest.mock import patch
        with patch('presenter.struct_presenter.filedialog.askopenfilename', return_value=None):
            result = self.presenter.browse_file()
        self.assertEqual(result['type'], 'error')
        self.assertIn('未選擇檔案', result['message'])

    def test_browse_file_error(self):
        from unittest.mock import patch, mock_open
        with patch('presenter.struct_presenter.filedialog.askopenfilename', return_value='test.h'):
            with patch('builtins.open', mock_open(read_data='struct content')):
                self.model.load_struct_from_file.side_effect = Exception('parse error')
                result = self.presenter.browse_file()
        self.assertEqual(result['type'], 'error')
        self.assertIn('載入檔案時發生錯誤', result['message'])

if __name__ == "__main__":
    unittest.main() 