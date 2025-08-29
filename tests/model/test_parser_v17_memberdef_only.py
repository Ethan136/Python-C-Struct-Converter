import unittest
from src.model.struct_parser import parse_member_line_v2, parse_struct_definition_ast, MemberDef


class TestParserV17MemberDefOnly(unittest.TestCase):
    def test_scalar_pointer_array_returns_memberdef(self):
        m1 = parse_member_line_v2('int a')
        self.assertIsInstance(m1, MemberDef)
        self.assertEqual(m1.type, 'int')
        self.assertEqual(m1.name, 'a')

        m2 = parse_member_line_v2('int *p')
        self.assertIsInstance(m2, MemberDef)
        self.assertEqual(m2.type, 'pointer')
        self.assertEqual(m2.name, 'p')

        m3 = parse_member_line_v2('int *arr[2]')
        self.assertIsInstance(m3, MemberDef)
        self.assertEqual(m3.type, 'pointer')
        self.assertEqual(m3.name, 'arr')
        self.assertEqual(m3.array_dims, [2])

    def test_nd_pointer_array_memberdef_dims_preserved(self):
        m = parse_member_line_v2('int *nd[2][2]')
        self.assertIsInstance(m, MemberDef)
        self.assertEqual(m.type, 'pointer')
        self.assertEqual(m.name, 'nd')
        self.assertEqual(m.array_dims, [2, 2])

    def test_referenced_struct_union_memberdef(self):
        src = '''
        struct Inner { int x; char y; };
        union U { int a; char b; };
        struct Outer { struct Inner i; union U u; };
        '''
        sdef = parse_struct_definition_ast(src)
        self.assertIsNotNone(sdef)
        self.assertTrue(all(isinstance(m, MemberDef) for m in sdef.members))


if __name__ == '__main__':
    unittest.main()

