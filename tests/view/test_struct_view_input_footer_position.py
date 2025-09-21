import unittest

from src.view.struct_view import StructView


class TestStructViewInputFooterPosition(unittest.TestCase):
    def test_footer_helpers_exist(self):
        # v28: require helper(s) to manage footer container and toggling
        self.assertTrue(hasattr(StructView, '_create_input_footer'))
        # optional helpers to simplify toggling
        self.assertTrue(hasattr(StructView, '_show_footer_flex'))
        self.assertTrue(hasattr(StructView, '_show_footer_grid'))


if __name__ == '__main__':
    unittest.main()

import unittest

from src.presenter.struct_presenter import StructPresenter
from src.model.struct_model import StructModel
from src.view.struct_view import StructView


class DummyFrame:
    def __init__(self, parent=None, name=""):
        self.parent = parent
        self.name = name
        self.packed = False
        self.pack_calls = []
        self.forget_calls = 0
    def pack(self, *args, **kwargs):
        self.packed = True
        self.pack_calls.append((args, kwargs))
    def pack_forget(self):
        self.packed = False
        self.forget_calls += 1


class TestStructViewInputFooterPosition(unittest.TestCase):
    def setUp(self):
        # Avoid real Tk construction
        self.view = object.__new__(StructView)
        self.view.presenter = object.__new__(StructPresenter)
        # minimal presenter context + API
        self.view.presenter.context = {"extra": {"input_mode": "flex_string"}}
        def set_input_mode(mode):
            self.view.presenter.context.setdefault("extra", {})["input_mode"] = mode
            return {"mode": mode}
        self.view.presenter.set_input_mode = set_input_mode
        # Build footer and frames using dummies
        self.view.input_footer_frame = DummyFrame(parent="main", name="footer")
        self.view.hex_grid_frame = DummyFrame(parent=self.view.input_footer_frame, name="grid")
        self.view.flex_frame = DummyFrame(parent=self.view.input_footer_frame, name="flex")
        # Controls potentially touched by toggle
        self.view._unit_label = DummyFrame(parent="core", name="unit_label")
        self.view.unit_menu = DummyFrame(parent="core", name="unit_menu")
        # Parse/Export buttons should not be affected
        self.view.parse_button = DummyFrame(parent="main", name="parse_button")
        self.view.export_csv_button = DummyFrame(parent="main", name="export_button")

    def test_frames_parent_is_footer_and_toggle_visibility(self):
        # Initial: flex_string visible in footer
        # simulate initial show
        self.view.flex_frame.pack()
        self.view.hex_grid_frame.pack_forget()
        # Parents should both be footer
        self.assertIs(self.view.hex_grid_frame.parent, self.view.input_footer_frame)
        self.assertIs(self.view.flex_frame.parent, self.view.input_footer_frame)
        # Toggle to grid
        self.view._on_input_mode_change("grid")
        self.assertFalse(self.view.flex_frame.packed)
        self.assertTrue(self.view.hex_grid_frame.packed)
        # Toggle back to flex_string
        self.view._on_input_mode_change("flex_string")
        self.assertTrue(self.view.flex_frame.packed)
        self.assertFalse(self.view.hex_grid_frame.packed)

    def test_toggle_does_not_touch_parse_export(self):
        # Record initial pack counts
        before_parse_calls = len(self.view.parse_button.pack_calls)
        before_export_calls = len(self.view.export_csv_button.pack_calls)
        # Perform multiple toggles
        for m in ("grid", "flex_string", "grid", "flex_string"):
            self.view._on_input_mode_change(m)
        # Buttons should not be packed/forgotten by the toggle
        self.assertEqual(len(self.view.parse_button.pack_calls), before_parse_calls)
        self.assertEqual(len(self.view.export_csv_button.pack_calls), before_export_calls)


if __name__ == "__main__":
    unittest.main()

