import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.layout import LayoutCalculator

class TestPackAlignmentPlaceholder(unittest.TestCase):
    def test_pack_alignment_no_effect(self):
        members = [("char", "a"), ("int", "b")]
        calc_default = LayoutCalculator()
        layout_default, total_default, align_default = calc_default.calculate(members)

        calc_pack = LayoutCalculator(pack_alignment=1)
        layout_pack, total_pack, align_pack = calc_pack.calculate(members)

        self.assertEqual(layout_pack, layout_default)
        self.assertEqual(total_pack, total_default)
        self.assertEqual(align_pack, align_default)

if __name__ == '__main__':
    unittest.main()
