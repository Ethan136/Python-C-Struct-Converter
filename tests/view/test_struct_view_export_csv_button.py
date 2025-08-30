import os
import tempfile
import unittest
import pytest
try:
    import tkinter as tk
except Exception:
    tk = None

pytestmark = pytest.mark.skipif(
    (not os.environ.get('DISPLAY')) or (tk is None), reason="No display/tkinter, skipping GUI tests"
)

from src.model.struct_model import StructModel
from src.presenter.struct_presenter import StructPresenter
from src.view.struct_view import StructView


SRC = """
struct A { int x; int y; };
struct B { char c; };
"""


class TestStructViewExportCSV(unittest.TestCase):
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

    def test_export_csv_button_and_flow(self):
        path = self._write_temp_header(SRC)
        out_fd, out_path = tempfile.mkstemp(suffix='.csv')
        os.close(out_fd)
        try:
            # Load model and wire presenter/view
            model = StructModel()
            model.load_struct_from_file(path)
            view = StructView()
            presenter = StructPresenter(model, view)
            view.presenter = presenter

            # Enable export button by showing layout
            view.show_struct_layout(model.struct_name, model.layout, model.total_size, model.struct_align)
            btn_state = getattr(view, 'export_csv_button', None)['state']
            self.assertEqual(btn_state, 'normal')

            # Monkeypatch filedialog and messagebox to avoid UI
            from src.view import struct_view as sv
            sv.filedialog.asksaveasfilename = lambda **kwargs: out_path
            try:
                sv.messagebox.showwarning = lambda *a, **k: None
                sv.messagebox.showerror = lambda *a, **k: None
            except Exception:
                pass

            # Trigger export
            view._on_export_csv()

            # Verify file created and non-empty
            self.assertTrue(os.path.exists(out_path))
            self.assertGreater(os.path.getsize(out_path), 0)
        finally:
            os.remove(path)
            try:
                os.remove(out_path)
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()

