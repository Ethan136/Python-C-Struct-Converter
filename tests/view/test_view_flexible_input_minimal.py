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


if __name__ == '__main__':
    unittest.main()
