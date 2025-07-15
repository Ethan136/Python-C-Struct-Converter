import unittest
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.layout import UnionLayoutCalculator
from model.struct_model import calculate_layout
from model.struct_parser import parse_c_definition_ast

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

    def test_union_with_nested_struct(self):
        content = """
        union U {
            struct S {
                int a;
                char b;
            } s;
            int x;
        };
        """
        udef = parse_c_definition_ast(content)
        layout, total, align = calculate_layout(udef.members, kind='union')
        names = [item.name for item in layout]
        self.assertIn('s.a', names)
        self.assertIn('s.b', names)
        self.assertIn('x', names)
        self.assertEqual(total, 8)
        self.assertEqual(align, 4)

    def test_union_with_nested_struct_array(self):
        content = """
        union U {
            struct S {
                int a;
                char b;
            } s[2];
            int x;
        };
        """
        udef = parse_c_definition_ast(content)
        layout, total, align = calculate_layout(udef.members, kind='union')
        names = [item.name for item in layout]
        self.assertIn('s[0].a', names)
        self.assertIn('s[1].b', names)
        self.assertIn('x', names)
        self.assertEqual(total, 8)
        self.assertEqual(align, 4)

if __name__ == '__main__':
    unittest.main()
