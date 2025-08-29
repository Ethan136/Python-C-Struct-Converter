import os
import tempfile
import time
import unittest
from src.model.struct_model import StructModel
from src.presenter.struct_presenter import StructPresenter


SRC = """
struct Inner { int x; };
struct Outer { struct Inner a; };
struct Last { char z; };
"""


class MockView:
    def __init__(self):
        self.last_nodes = None
        self.last_context = None
        self.update_display_called = False
    def update_display(self, nodes, context):
        self.last_nodes = nodes
        self.last_context = context
        self.update_display_called = True


class TestPresenterV17TargetStruct(unittest.TestCase):
    def _write_temp_header(self, content):
        fd, path = tempfile.mkstemp(suffix='.h')
        os.close(fd)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def setUp(self):
        self.model = StructModel()
        self.view = MockView()
        self.presenter = StructPresenter(self.model, self.view)
        # Make push_context synchronous for tests
        self.presenter._debounce_interval = 0
        orig_push_context = self.presenter.push_context
        def sync_push_context(*args, **kwargs):
            return orig_push_context(immediate=True)
        self.presenter.push_context = sync_push_context

    def test_set_import_target_struct_switches_root(self):
        path = self._write_temp_header(SRC)
        try:
            # initial load default (last top-level is Last)
            self.model.load_struct_from_file(path)
            # switch to Outer
            self.presenter.set_import_target_struct('Outer')
            self.assertTrue(self.view.update_display_called)
            self.assertIsInstance(self.view.last_nodes, list)
            root = self.view.last_nodes[0]
            self.assertIn('Outer', root.get('label', ''))
        finally:
            os.remove(path)

    def test_presenter_values_are_strings(self):
        path = self._write_temp_header(SRC)
        try:
            self.model.load_struct_from_file(path)
            self.presenter.set_import_target_struct('Outer')
            self.assertTrue(self.view.update_display_called)
            def walk(nodes):
                for n in nodes:
                    self.assertIsInstance(n.get('value', ''), str)
                    self.assertIsInstance(n.get('offset', ''), str)
                    self.assertIsInstance(n.get('size', ''), str)
                    walk(n.get('children', []))
            walk(self.view.last_nodes)
        finally:
            os.remove(path)


if __name__ == '__main__':
    unittest.main()

