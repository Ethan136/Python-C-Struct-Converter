import unittest
from model.struct_model import calculate_layout
from model.layout import UnionLayoutCalculator

class TestUnionLayoutCustom(unittest.TestCase):
    def test_custom_calculator_parameter(self):
        layout, total, align = calculate_layout([('int','a'), ('char','b')], calculator_cls=UnionLayoutCalculator)
        self.assertEqual(total, 4)
        self.assertEqual(align, 4)
        self.assertEqual(len(layout), 2)
        for item in layout:
            self.assertEqual(item.offset, 0)

if __name__ == '__main__':
    unittest.main()
