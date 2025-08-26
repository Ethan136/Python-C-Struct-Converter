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


class TestPointerModeSwitch(unittest.TestCase):
    def setUp(self):
        # Import here to avoid hard dependency when not needed by other tests
        from src.model.types import set_pointer_mode, reset_pointer_mode
        self._set_pointer_mode = set_pointer_mode
        self._reset_pointer_mode = reset_pointer_mode

    def tearDown(self):
        # Always reset to default 64-bit after each test
        self._reset_pointer_mode()

    def test_pointer_size_align_switch(self):
        from src.model.types import get_type_info
        self._set_pointer_mode(32)
        info32 = get_type_info('pointer')
        self.assertEqual((info32['size'], info32['align']), (4, 4))
        self._set_pointer_mode(64)
        info64 = get_type_info('pointer')
        self.assertEqual((info64['size'], info64['align']), (8, 8))

    def test_layout_changes_with_pointer_mode(self):
        # Verify a simple struct layout differs between 64-bit and 32-bit pointer modes
        from src.model.struct_model import calculate_layout
        members = [
            {"type": "char", "name": "c", "is_bitfield": False},
            {"type": "pointer", "name": "p", "is_bitfield": False},
        ]
        # Default 64-bit
        layout64, total64, align64 = calculate_layout(members)
        # char at 0, padding to 8, pointer at 8, total 16 (final padding)
        self.assertEqual(layout64[0].offset, 0)
        self.assertEqual(layout64[0].size, 1)
        # Find pointer entry
        ptr_items64 = [li for li in layout64 if getattr(li, 'name', '') == 'p']
        self.assertTrue(ptr_items64)
        self.assertEqual(ptr_items64[0].offset, 8)
        self.assertEqual(ptr_items64[0].size, 8)
        self.assertEqual(total64, 16)
        # Switch to 32-bit
        self._set_pointer_mode(32)
        layout32, total32, align32 = calculate_layout(members)
        ptr_items32 = [li for li in layout32 if getattr(li, 'name', '') == 'p']
        self.assertTrue(ptr_items32)
        self.assertEqual(layout32[0].offset, 0)
        self.assertEqual(layout32[0].size, 1)
        self.assertEqual(ptr_items32[0].offset, 4)
        self.assertEqual(ptr_items32[0].size, 4)
        self.assertEqual(total32, 8)


if __name__ == '__main__':
    unittest.main()


