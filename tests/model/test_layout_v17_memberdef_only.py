import unittest
from src.model.struct_parser import parse_struct_definition_ast
from src.model.struct_model import calculate_layout


def _names(layout):
    return [x.name if hasattr(x, 'name') else x.get('name') for x in layout if (hasattr(x, 'type') and x.type != 'padding') or (isinstance(x, dict) and x.get('type') != 'padding')]


class TestLayoutV17MemberDefOnly(unittest.TestCase):
    def test_layout_expands_nd_pointer_array(self):
        src = '''
        struct S { int x; };
        struct W { struct S *nd[2][2]; };
        '''
        sdef = parse_struct_definition_ast(src)
        layout, total, align = calculate_layout(sdef.members)
        names = _names(layout)
        # pointer array 展開各元素
        self.assertIn('nd[0][0]', names)
        self.assertIn('nd[1][1]', names)

    def test_layout_referenced_struct_array_expand(self):
        src = '''
        struct Inner { int x; };
        struct W { struct Inner arr[2]; };
        '''
        sdef = parse_struct_definition_ast(src)
        layout, total, align = calculate_layout(sdef.members)
        names = _names(layout)
        self.assertIn('arr[0].x', names)
        self.assertIn('arr[1].x', names)

    def test_layout_forward_reference_expand(self):
        src = '''
        struct Outer { struct Inner a; };
        struct Inner { int x; };
        '''
        sdef = parse_struct_definition_ast(src, target_name='Outer')
        layout, total, align = calculate_layout(sdef.members)
        names = _names(layout)
        self.assertIn('a.x', names)


if __name__ == '__main__':
    unittest.main()

