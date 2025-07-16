import os
import sys
import unittest

# Add src to path to import the model
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.model.layout import BaseLayoutCalculator, StructLayoutCalculator, LayoutCalculator

class TestLayoutRefactor(unittest.TestCase):
    def test_base_class_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseLayoutCalculator()

    def test_layout_alias(self):
        self.assertIs(LayoutCalculator, StructLayoutCalculator)

    def test_struct_layout_same_as_alias(self):
        members = [("char", "a"), ("int", "b")]
        calc_alias = LayoutCalculator()
        calc_struct = StructLayoutCalculator()
        layout1, total1, align1 = calc_alias.calculate(members)
        layout2, total2, align2 = calc_struct.calculate(members)
        self.assertEqual(total1, total2)
        self.assertEqual(align1, align2)
        tuple1 = [(i.name, i.offset, i.size) for i in layout1]
        tuple2 = [(i.name, i.offset, i.size) for i in layout2]
        self.assertEqual(tuple1, tuple2)

if __name__ == '__main__':
    unittest.main()
