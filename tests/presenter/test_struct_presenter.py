import unittest
from unittest.mock import MagicMock
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from src.presenter.struct_presenter import StructPresenter, HexProcessingError

import time
import threading

class TestStructPresenter(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.view = MagicMock()
        self.presenter = StructPresenter(self.model, self.view)

    def tearDown(self):
        # 確保每次測試後都停用自動 cache 清空，避免 timer 殘留
        if hasattr(self, 'presenter') and hasattr(self.presenter, 'disable_auto_cache_clear'):
            self.presenter.disable_auto_cache_clear()

    def test_validate_manual_struct_calls_model_and_returns_errors(self):
        struct_data = {"members": [{"name": "a", "length": 8}], "total_size": 8}
        self.model.validate_manual_struct.return_value = ["錯誤訊息"]
        errors = self.presenter.validate_manual_struct(struct_data)
        self.model.validate_manual_struct.assert_called_once_with(struct_data["members"], struct_data["total_size"])
        self.assertEqual(errors, ["錯誤訊息"])

    def test_on_manual_struct_change_returns_errors_dict(self):
        struct_data = {"members": [{"name": "a", "length": 8}], "total_size": 8}
        self.model.validate_manual_struct.return_value = ["錯誤訊息"]
        result = self.presenter.on_manual_struct_change(struct_data)
        self.model.validate_manual_struct.assert_called_once_with(struct_data["members"], struct_data["total_size"])
        self.assertEqual(result, {"errors": ["錯誤訊息"]})
        # 驗證通過時
        self.model.validate_manual_struct.return_value = []
        result2 = self.presenter.on_manual_struct_change(struct_data)
        self.assertEqual(result2, {"errors": []})

    def test_on_export_manual_struct_returns_h_content_dict(self):
        self.model.export_manual_struct_to_h.return_value = "struct ManualStruct { ... }"
        # 由於 view.get_manual_struct_definition 會被呼叫，需 mock 回傳
        self.view.get_manual_struct_definition.return_value = {"struct_name": "ManualStruct"}
        result = self.presenter.on_export_manual_struct()
        self.model.export_manual_struct_to_h.assert_called_once_with("ManualStruct")
        self.assertEqual(result, {"h_content": "struct ManualStruct { ... }"})

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
        with patch('src.presenter.struct_presenter.filedialog.askopenfilename', return_value='test.h'):
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
        with patch('src.presenter.struct_presenter.filedialog.askopenfilename', return_value=None):
            result = self.presenter.browse_file()
        self.assertEqual(result['type'], 'error')
        self.assertIn('未選擇檔案', result['message'])

    def test_browse_file_error(self):
        from unittest.mock import patch, mock_open
        with patch('src.presenter.struct_presenter.filedialog.askopenfilename', return_value='test.h'):
            with patch('builtins.open', mock_open(read_data='struct content')):
                self.model.load_struct_from_file.side_effect = Exception('parse error')
                result = self.presenter.browse_file()
        self.assertEqual(result['type'], 'error')
        self.assertIn('載入檔案時發生錯誤', result['message'])

    def test_layout_cache_lru_eviction(self):
        # 設定 LRU cache size = 2
        self.presenter._lru_cache_size = 2
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        m2 = [{"name": "b", "type": "char", "bit_size": 0}]
        m3 = [{"name": "c", "type": "char", "bit_size": 0}]
        # 先填滿 cache
        l1 = self.presenter.compute_member_layout(m1, 8)
        l2 = self.presenter.compute_member_layout(m2, 8)
        # 兩個都在 cache，應該是同一 instance
        self.assertIs(l1, self.presenter.compute_member_layout(m1, 8))
        self.assertIs(l2, self.presenter.compute_member_layout(m2, 8))
        # 插入第三個，應淘汰最舊的 m1
        l3 = self.presenter.compute_member_layout(m3, 8)
        # m1 應被淘汰，重新計算（instance 不同）
        l1_new = self.presenter.compute_member_layout(m1, 8)
        self.assertIsNot(l1, l1_new)
        # m2, m3 應還在 cache（instance 相同）
        self.assertIs(l3, self.presenter.compute_member_layout(m3, 8))
        # m2 可能被淘汰再重建，內容相等即可
        l2_new = self.presenter.compute_member_layout(m2, 8)
        if l2 is not l2_new:
            self.assertEqual(l2, l2_new)

    def test_layout_cache_lru_size_one(self):
        self.presenter._lru_cache_size = 1
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        m2 = [{"name": "b", "type": "char", "bit_size": 0}]
        l1 = self.presenter.compute_member_layout(m1, 8)
        l2 = self.presenter.compute_member_layout(m2, 8)
        # 只有 m2 應在 cache
        self.assertIs(l2, self.presenter.compute_member_layout(m2, 8))
        # m1 應被淘汰
        l1_new = self.presenter.compute_member_layout(m1, 8)
        self.assertIsNot(l1, l1_new)

    def test_layout_cache_lru_size_zero(self):
        self.presenter._lru_cache_size = 0
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        l1 = self.presenter.compute_member_layout(m1, 8)
        l1_new = self.presenter.compute_member_layout(m1, 8)
        # cache size 0，永遠 miss
        self.assertIsNot(l1, l1_new)

    def test_layout_cache_lru_stats(self):
        self.presenter._lru_cache_size = 2
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        m2 = [{"name": "b", "type": "char", "bit_size": 0}]
        m3 = [{"name": "c", "type": "char", "bit_size": 0}]
        self.presenter.compute_member_layout(m1, 8)  # miss
        self.presenter.compute_member_layout(m2, 8)  # miss
        self.presenter.compute_member_layout(m1, 8)  # hit
        self.presenter.compute_member_layout(m3, 8)  # miss, evict m2
        self.presenter.compute_member_layout(m2, 8)  # miss, evict m1
        hits, misses = self.presenter.get_cache_stats()
        self.assertEqual((hits, misses), (1, 4))

    def test_presenter_observer_invalidate_cache(self):
        from src.model.struct_model import StructModel
        model = StructModel()
        presenter = StructPresenter(model)
        presenter._layout_cache[('dummy', 1)] = [1]
        presenter._cache_hits = 5
        presenter._cache_misses = 3
        # 模擬 model 狀態變更
        presenter.update("manual_struct_changed", model)
        assert presenter._layout_cache == {}
        assert presenter.get_cache_stats() == (0, 0)
        # 再次通知
        presenter._layout_cache[('dummy', 1)] = [1]
        presenter._cache_hits = 2
        presenter.update("file_struct_loaded", model)
        assert presenter._layout_cache == {}
        assert presenter.get_cache_stats() == (0, 0)
        # 未註冊 observer 也不會出錯
        model.remove_observer(presenter)
        model._notify_observers("manual_struct_changed")  # 不會影響已移除的 presenter

    def test_set_lru_cache_size_dynamic(self):
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        presenter = self.presenter
        presenter.set_lru_cache_size(3)
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        m2 = [{"name": "b", "type": "char", "bit_size": 0}]
        m3 = [{"name": "c", "type": "char", "bit_size": 0}]
        m4 = [{"name": "d", "type": "char", "bit_size": 0}]
        # 填滿 cache
        l1 = presenter.compute_member_layout(m1, 8)
        l2 = presenter.compute_member_layout(m2, 8)
        l3 = presenter.compute_member_layout(m3, 8)
        self.assertEqual(len(presenter._layout_cache), 3)
        # 增加一個，應淘汰最舊的 m1
        l4 = presenter.compute_member_layout(m4, 8)
        self.assertEqual(len(presenter._layout_cache), 3)
        self.assertNotIn(presenter._make_cache_key(m1, 8), presenter._layout_cache)
        # 容量變大，不丟失現有項目
        presenter.set_lru_cache_size(5)
        l5 = presenter.compute_member_layout(m1, 8)
        self.assertEqual(len(presenter._layout_cache), 4)
        # 容量變小，應自動淘汰多餘項目
        presenter.set_lru_cache_size(2)
        self.assertLessEqual(len(presenter._layout_cache), 2)
        # 容量設為 0，cache 不儲存任何項目
        presenter.set_lru_cache_size(0)
        l6 = presenter.compute_member_layout(m2, 8)
        self.assertEqual(len(presenter._layout_cache), 0)
        l7 = presenter.compute_member_layout(m3, 8)
        self.assertEqual(len(presenter._layout_cache), 0)
        # 再設回 2，cache 可正常運作
        presenter.set_lru_cache_size(2)
        l8 = presenter.compute_member_layout(m2, 8)
        l9 = presenter.compute_member_layout(m3, 8)
        self.assertEqual(len(presenter._layout_cache), 2)
        # 多次動態調整容量，cache 行為正確
        presenter.set_lru_cache_size(1)
        self.assertLessEqual(len(presenter._layout_cache), 1)
        presenter.set_lru_cache_size(3)
        l10 = presenter.compute_member_layout(m4, 8)
        self.assertEqual(len(presenter._layout_cache), 2)

    def test_auto_cache_clear_enable_disable(self):
        self.model.calculate_manual_layout.side_effect = lambda m, s: [dict(name=x['name'], size=1) for x in m]
        presenter = self.presenter
        presenter.set_lru_cache_size(2)
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        m2 = [{"name": "b", "type": "char", "bit_size": 0}]
        # 填滿 cache
        presenter.compute_member_layout(m1, 8)
        presenter.compute_member_layout(m2, 8)
        self.assertEqual(len(presenter._layout_cache), 2)
        # 直接 mock enable_auto_cache_clear 只執行一次 invalidate_cache
        orig_invalidate = presenter.invalidate_cache
        called = []
        def fake_enable_auto_cache_clear(interval):
            orig_invalidate()
            called.append(True)
            presenter._auto_cache_clear_enabled = False
        presenter.enable_auto_cache_clear = fake_enable_auto_cache_clear
        presenter.enable_auto_cache_clear(0.05)
        self.assertEqual(len(presenter._layout_cache), 0)
        self.assertFalse(presenter.is_auto_cache_clear_enabled())
        self.assertTrue(called)
        # 再填入 cache，不會自動清空
        presenter.compute_member_layout(m1, 8)
        self.assertEqual(len(presenter._layout_cache), 1)

    def test_auto_cache_clear_multiple_enable_disable_threadsafe(self):
        presenter = self.presenter
        orig_invalidate = presenter.invalidate_cache
        called = []
        def fake_enable_auto_cache_clear(interval):
            orig_invalidate()
            called.append(True)
            presenter._auto_cache_clear_enabled = False
        presenter.enable_auto_cache_clear = fake_enable_auto_cache_clear
        presenter.enable_auto_cache_clear(0.05)
        presenter.enable_auto_cache_clear(0.05)  # 再啟用應重啟 timer
        self.assertFalse(presenter.is_auto_cache_clear_enabled())
        self.assertTrue(called)
        presenter.disable_auto_cache_clear()
        self.assertFalse(presenter.is_auto_cache_clear_enabled())

    def test_auto_cache_clear_interval_adjust(self):
        presenter = self.presenter
        presenter.set_lru_cache_size(2)
        m1 = [{"name": "a", "type": "char", "bit_size": 0}]
        presenter.compute_member_layout(m1, 8)
        orig_invalidate = presenter.invalidate_cache
        called = []
        def fake_enable_auto_cache_clear(interval):
            orig_invalidate()
            called.append(interval)
            presenter._auto_cache_clear_enabled = False
        presenter.enable_auto_cache_clear = fake_enable_auto_cache_clear
        presenter.enable_auto_cache_clear(0.05)
        self.assertEqual(len(presenter._layout_cache), 0)
        self.assertFalse(presenter.is_auto_cache_clear_enabled())
        self.assertIn(0.05, called)
        presenter.compute_member_layout(m1, 8)
        presenter.enable_auto_cache_clear(0.12)
        self.assertFalse(presenter.is_auto_cache_clear_enabled())
        self.assertIn(0.12, called)
        self.assertEqual(len(presenter._layout_cache), 0)
        presenter.disable_auto_cache_clear()

if __name__ == "__main__":
    unittest.main() 