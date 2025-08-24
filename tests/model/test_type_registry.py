import unittest
import os
import sys

# Ensure src on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, '..', 'src'))

from src.model.types import get_type_info, normalize_type, ALIAS_MAP, CUSTOM_TYPE_INFO


class TestTypeRegistryConfig(unittest.TestCase):
    def test_aliases_loaded(self):
        # Defaults should include U8/U16/U32/U64; and yaml file reiterates them
        self.assertEqual(normalize_type('U32'), 'unsigned int')
        self.assertEqual(normalize_type('U8'), 'unsigned char')

    def test_custom_types_loaded(self):
        # custom_types.yaml defines my_u24 size/align
        info = get_type_info('my_u24')
        self.assertEqual(info['size'], 3)
        self.assertEqual(info['align'], 1)


if __name__ == '__main__':
    unittest.main()


