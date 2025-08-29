import os
import tempfile
import unittest
from src.model.struct_model import StructModel


SRC = """
struct Inner { int x; };
struct Outer { struct Inner a; };
struct Another { char y; };
"""


class TestModelV17TargetStruct(unittest.TestCase):
    def _write_temp_header(self, content):
        fd, path = tempfile.mkstemp(suffix='.h')
        os.close(fd)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_load_struct_from_file_with_target_name_outer(self):
        path = self._write_temp_header(SRC)
        try:
            model = StructModel()
            name, layout, total, align = model.load_struct_from_file(path, target_name='Outer')
            self.assertEqual(name, 'Outer')
        finally:
            os.remove(path)

    def test_load_struct_from_file_with_target_name_forward(self):
        src = """
        struct Outer { struct Inner a; };
        struct Inner { int x; };
        """
        path = self._write_temp_header(src)
        try:
            model = StructModel()
            name, layout, total, align = model.load_struct_from_file(path, target_name='Outer')
            names = [it.name if hasattr(it, 'name') else it.get('name') for it in layout]
            self.assertIn('a.x', ''.join(n for n in names if n))
        finally:
            os.remove(path)

    def test_available_top_level_types_listed(self):
        path = self._write_temp_header(SRC)
        try:
            model = StructModel()
            name, layout, total, align = model.load_struct_from_file(path, target_name='Outer')
            types = getattr(model, 'available_top_level_types', [])
            self.assertIsInstance(types, list)
            self.assertTrue(types)
            self.assertIn('Outer', types)
            self.assertIn('Inner', types)
        finally:
            os.remove(path)


if __name__ == '__main__':
    unittest.main()

