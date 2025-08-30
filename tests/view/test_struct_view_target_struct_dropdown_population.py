import os
import tempfile
import unittest
import pytest
import tkinter as tk

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'), reason="No display found, skipping GUI tests"
)

from src.model.struct_model import StructModel
from src.presenter.struct_presenter import StructPresenter
from src.view.struct_view import StructView


SRC = """
struct Inner { int x; };
struct Outer { struct Inner a; };
struct Another { char y; };
"""


class TestStructViewTargetStructDropdown(unittest.TestCase):
    def _write_temp_header(self, content):
        fd, path = tempfile.mkstemp(suffix='.h')
        os.close(fd)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_dropdown_population_and_sync(self):
        path = self._write_temp_header(SRC)
        try:
            model = StructModel()
            # Initial load (default last top-level)
            model.load_struct_from_file(path)
            view = StructView()
            presenter = StructPresenter(model, view)
            view.presenter = presenter
            # Trigger update so dropdown gets populated from context.extra
            nodes = presenter.get_display_nodes('tree')
            view.update_display(nodes, presenter.context)
            # Read dropdown values
            combo = getattr(view, 'target_struct_combo', None)
            assert combo is not None
            try:
                values = tuple(combo['values'])
            except Exception:
                # Fallback for Entry replacement
                values = tuple()
            # Should contain known types collected by model
            self.assertIn('Outer', values)
            self.assertIn('Inner', values)
            # Now switch to Outer via presenter and ensure the UI var syncs
            presenter.set_import_target_struct('Outer')
            self.root.update()
            current = view.target_struct_var.get()
            self.assertEqual(current, 'Outer')
        finally:
            os.remove(path)


if __name__ == '__main__':
    unittest.main()

