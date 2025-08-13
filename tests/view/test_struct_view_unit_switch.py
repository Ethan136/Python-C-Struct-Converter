import os
import unittest
import pytest
from unittest.mock import MagicMock, patch
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.view.struct_view import StructView
from src.presenter.struct_presenter import StructPresenter


class TestStructViewUnitSwitch(unittest.TestCase):
    @pytest.mark.timeout(10)
    def test_unit_switch_uses_presenter_model_total_size(self):
        # Patch StructView.__init__ to avoid GUI initialization
        with patch('src.view.struct_view.StructView.__init__', lambda self: None):
            view = StructView()
        # Prepare view methods
        view.get_selected_unit_size = MagicMock(return_value=4)
        view.rebuild_hex_grid = MagicMock()
        # Real presenter with mocked model
        model = MagicMock()
        model.total_size = 16
        presenter = StructPresenter(model=model, view=view)
        presenter.view = view
        view.presenter = presenter
        # Trigger unit size change
        view._on_unit_size_change()
        # Should rebuild with model.total_size and selected unit size
        view.rebuild_hex_grid.assert_called_once_with(16, 4)

    @pytest.mark.timeout(10)
    def test_unit_switch_fallback_to_view_current_file_total_size(self):
        # Patch StructView.__init__ to avoid GUI initialization
        with patch('src.view.struct_view.StructView.__init__', lambda self: None):
            view = StructView()
        # Prepare view state and methods
        view.current_file_total_size = 24
        view.rebuild_hex_grid = MagicMock()
        # Mock presenter that returns unit_size but lacks usable model.total_size
        presenter = MagicMock()
        presenter.on_unit_size_change.return_value = {"unit_size": 4}
        presenter.model = MagicMock()
        # Ensure presenter.model doesn't provide total_size
        delattr(presenter.model, 'total_size')
        view.presenter = presenter
        # Trigger unit size change
        view._on_unit_size_change()
        # Should fallback to view.current_file_total_size
        view.rebuild_hex_grid.assert_called_once_with(24, 4)


if __name__ == '__main__':
    unittest.main()