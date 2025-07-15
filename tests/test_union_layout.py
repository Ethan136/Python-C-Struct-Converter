import unittest
from model.layout import UnionLayoutCalculator
from model.struct_model import calculate_layout

class TestUnionLayout(unittest.TestCase):
    def test_union_layout_offsets_and_size(self):
        members = [('int', 'a'), ('char', 'b')]
        layout, total, align = calculate_layout(members, calculator_cls=UnionLayoutCalculator)
        self.assertEqual(total, 4)
        self.assertEqual(align, 4)
        self.assertEqual(len(layout), 2)
        for item in layout:
            self.assertEqual(item.offset, 0)
        self.assertEqual(layout[0].size, 4)
        self.assertEqual(layout[1].size, 1)

if __name__ == '__main__':
    unittest.main()
