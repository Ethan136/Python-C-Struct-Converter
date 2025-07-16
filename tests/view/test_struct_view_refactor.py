
import os
import unittest
import pytest
from unittest.mock import MagicMock, patch
from src.view.struct_view import StructView

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'), reason="No display found, skipping GUI tests"
)

class TestStructViewRefactor(unittest.TestCase):

    def setUp(self):
        # 完全 mock StructView.__init__，手動設置屬性，避免 GUI 初始化
        with patch('src.view.struct_view.StructView.__init__', lambda self: None):
            self.view = StructView()
        self.view.presenter = MagicMock()
        self.view.hex_grid_frame = MagicMock()
        self.view.hex_entries = MagicMock()
        self.view._build_hex_grid = MagicMock()
        self.view.get_selected_unit_size = MagicMock(return_value=4)
        self.view.manual_hex_grid_frame = MagicMock()
        self.view.manual_hex_entries = MagicMock()
        self.view.manual_unit_size_var = MagicMock()
        self.view.size_var = MagicMock()
        self.view.manual_unit_size_var.get = MagicMock(return_value="8 Bytes")
        self.view.size_var.get = MagicMock(return_value=32)

    @pytest.mark.timeout(10)
    def test_rebuild_hex_grid_calls_build_hex_grid(self):
        # 模擬 _build_hex_grid 方法
        self.view._build_hex_grid = MagicMock()
        
        # 模擬 get_selected_unit_size 回傳值
        self.view.get_selected_unit_size = MagicMock(return_value=4)
        
        # 呼叫 rebuild_hex_grid
        self.view.rebuild_hex_grid(16, 4)
        
        # 驗證 _build_hex_grid 是否被正確呼叫
        self.view._build_hex_grid.assert_called_once_with(
            self.view.hex_grid_frame, self.view.hex_entries, 16, 4
        )

    @pytest.mark.timeout(10)
    def test_rebuild_manual_hex_grid_calls_build_hex_grid(self):
        # 模擬 _build_hex_grid 方法
        self.view._build_hex_grid = MagicMock()
        
        # 模擬 get_selected_manual_unit_size 回傳值
        self.view.manual_unit_size_var.get = MagicMock(return_value="8 Bytes")
        self.view.size_var.get = MagicMock(return_value=32)
        
        # 呼叫 _rebuild_manual_hex_grid
        self.view._rebuild_manual_hex_grid()
        
        # 驗證 _build_hex_grid 是否被正確呼叫
        self.view._build_hex_grid.assert_called_once_with(
            self.view.manual_hex_grid_frame, self.view.manual_hex_entries, 32, 8
        )

if __name__ == '__main__':
    unittest.main()
