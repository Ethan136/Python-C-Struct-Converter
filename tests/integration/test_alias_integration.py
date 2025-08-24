import unittest
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, '..', 'src'))

from src.model.struct_model import StructModel


class TestAliasIntegration(unittest.TestCase):
    def test_load_alias_header(self):
        m = StructModel()
        header_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'examples', 'alias_integration.h')
        header_path = os.path.normpath(header_path)
        name, layout, total, align = m.load_struct_from_file(header_path)
        self.assertEqual(name, 'AliasTop')
        # smoke checks for fields from aliases
        self.assertTrue(any('in' in (i['name'] if isinstance(i, dict) else getattr(i, 'name', '')) for i in layout))
        self.assertTrue(align in (4, 8))


if __name__ == '__main__':
    unittest.main()


