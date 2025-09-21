import unittest
from unittest.mock import MagicMock
import time

from src.model.struct_model import StructModel
from src.presenter.struct_presenter import StructPresenter


class MockFlexView:
    def __init__(self, s: str, endian: str = "Little Endian"):
        self._s = s
        self._endian = endian
        self.last_nodes = None
        self.last_context = None
        self.update_display_called = False
    def get_flexible_input_string(self):
        return self._s
    def get_selected_endianness(self):
        return self._endian
    def update_display(self, nodes, context):
        self.last_nodes = nodes
        self.last_context = context
        self.update_display_called = True
    def on_values_refreshed(self):
        pass


class TestPresenterFlexibleInput(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()
        # Minimal layout for 3 bytes at offset 0
        self.model.layout = [{
            'name': 'x', 'type': 'char', 'offset': 0, 'size': 3,
            'is_bitfield': False
        }]
        self.model.total_size = 3
        self.view = MockFlexView("0x01,0x0302")
        self.presenter = StructPresenter(self.model, self.view)
        # Make push_context synchronous
        self.presenter._debounce_interval = 0
        orig_push_context = self.presenter.push_context
        def sync_push_context(*args, **kwargs):
            return orig_push_context(immediate=True)
        self.presenter.push_context = sync_push_context

    def test_set_input_mode_updates_context(self):
        out = self.presenter.set_input_mode("flex_string")
        self.assertEqual(out.get("mode"), "flex_string")
        self.assertTrue(self.view.update_display_called)
        self.assertEqual(self.view.last_context.get("extra", {}).get("input_mode"), "flex_string")

    def test_parse_flexible_hex_input_success(self):
        res = self.presenter.parse_flexible_hex_input()
        self.assertEqual(res.get('type'), 'ok')
        parsed = res.get('parsed_values')
        self.assertIsInstance(parsed, list)
        self.assertEqual(parsed[0]['hex_raw'], '010203')

    def test_parse_flexible_hex_input_invalid(self):
        self.presenter.view = MockFlexView("0x, 01")
        res = self.presenter.parse_flexible_hex_input()
        self.assertEqual(res.get('type'), 'error')
        self.assertIn('Invalid', res.get('message'))


if __name__ == '__main__':
    unittest.main()

