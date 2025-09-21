import unittest
from src.presenter.struct_presenter import StructPresenter
from src.model.struct_model import StructModel
from src.view.struct_view import StructView


class TestViewFlexibleInputMinimal(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()
        self.presenter = StructPresenter(self.model, None)
        # Avoid initializing a real Tk app; construct without __init__
        self.view = object.__new__(StructView)
        # Minimal fields used by methods
        self.presenter.view = self.view
        setattr(self.view, 'presenter', self.presenter)
        # Dummy flex_input_var
        class _DummyVar:
            def __init__(self): self._v = ''
            def get(self): return self._v
            def set(self, v): self._v = v
        setattr(self.view, 'flex_input_var', _DummyVar())
        # input_mode_var (for v26 binding test)
        class _DummyModeVar:
            def __init__(self, v='grid'): self._v = v
            def get(self): return self._v
            def set(self, v): self._v = v
        setattr(self.view, 'input_mode_var', _DummyModeVar('grid'))
        # dummy label to capture preview text
        class _DummyLabel:
            def __init__(self): self.last_text = None
            def config(self, **kwargs): self.last_text = kwargs.get('text')
        setattr(self.view, 'flex_preview_label', _DummyLabel())

    def test_methods_exist_and_defaults(self):
        self.assertTrue(hasattr(self.view, 'get_input_mode'))
        self.assertEqual(self.view.get_input_mode(), 'grid')
        self.assertTrue(hasattr(self.view, 'get_flexible_input_string'))
        self.assertEqual(self.view.get_flexible_input_string(), '')
        self.assertTrue(hasattr(self.view, 'show_flexible_preview'))
        self.view.show_flexible_preview('010203', 3, ['warn'], [])
        self.assertEqual(self.view._flex_preview.get('hex_bytes'), '010203')
        self.assertEqual(self.view._flex_preview.get('total_len'), 3)
        self.assertEqual(self.view._flex_preview.get('warnings'), ['warn'])
        # label updated
        self.assertIn('010203', self.view.flex_preview_label.last_text)
        self.assertIn('len=3', self.view.flex_preview_label.last_text)

    def test_get_input_mode_prefers_local_var_over_context(self):
        # presenter context says grid
        self.presenter.context.setdefault('extra', {})['input_mode'] = 'grid'
        # local UI selects flex_string
        self.view.input_mode_var.set('flex_string')
        self.assertEqual(self.view.get_input_mode(), 'flex_string')

    def test_get_input_mode_fallback_to_context(self):
        # remove local var to force fallback
        delattr(self.view, 'input_mode_var')
        self.presenter.context.setdefault('extra', {})['input_mode'] = 'flex_string'
        self.assertEqual(self.view.get_input_mode(), 'flex_string')

    def test_debug_bytes_updated_in_flex_mode(self):
        # Prepare presenter/view minimal wiring for debug bytes
        # Monkey-patch show_debug_bytes to capture lines
        captured = {}
        def _capture(lines):
            captured['lines'] = list(lines)
        setattr(self.view, 'show_debug_bytes', _capture)
        # Simulate presenter context with last_flex_hex and call view branch directly
        self.presenter.context.setdefault('extra', {})['last_flex_hex'] = '01020304'
        # Mock presenter method to return ok + warnings
        def _mock_parse():
            return {'type': 'ok', 'parsed_values': [], 'warnings': ['padded 1 byte'], 'trunc_info': []}
        self.presenter.parse_flexible_hex_input = _mock_parse
        # Force mode and trigger view parse branch
        self.view.input_mode_var.set('flex_string')
        self.view._on_parse_file()
        self.assertIn('lines', captured)
        header = captured['lines'][0]
        self.assertIn('Flex Bytes (len=4)', header)


if __name__ == '__main__':
    unittest.main()
