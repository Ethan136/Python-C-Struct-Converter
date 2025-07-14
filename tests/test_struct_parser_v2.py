import unittest
from model.struct_parser import parse_member_line_v2, parse_struct_definition_v2, MemberDef
from model.layout import LayoutCalculator

class TestParseMemberLineV2(unittest.TestCase):
    def test_regular_member(self):
        m = parse_member_line_v2('int value')
        self.assertIsInstance(m, MemberDef)
        self.assertEqual(m.type, 'int')
        self.assertEqual(m.name, 'value')
        self.assertFalse(m.is_bitfield)
        self.assertEqual(m.array_dims, [])

    def test_pointer_member(self):
        m = parse_member_line_v2('char* ptr')
        self.assertEqual(m.type, 'pointer')
        self.assertEqual(m.name, 'ptr')
        self.assertFalse(m.is_bitfield)

    def test_bitfield_member(self):
        m = parse_member_line_v2('unsigned int flag : 3')
        self.assertTrue(m.is_bitfield)
        self.assertEqual(m.type, 'unsigned int')
        self.assertEqual(m.name, 'flag')
        self.assertEqual(m.bit_size, 3)

class TestParseStructDefinitionV2(unittest.TestCase):
    def test_simple_struct(self):
        content = '''
        struct Simple {
            char a;
            int b;
        };
        '''
        name, members = parse_struct_definition_v2(content)
        self.assertEqual(name, 'Simple')
        self.assertEqual(len(members), 2)
        self.assertIsInstance(members[0], MemberDef)

class TestLayoutCalculatorWithMemberDef(unittest.TestCase):
    def test_layout_with_memberdef(self):
        members = [MemberDef('char', 'a'), MemberDef('int', 'b')]
        calc = LayoutCalculator()
        layout, total, align = calc.calculate(members)
        self.assertEqual(total, 8)
        self.assertEqual(align, 4)
        self.assertEqual(len(layout), 3)  # char, padding, int
        self.assertEqual(layout[0].name, 'a')
        self.assertEqual(layout[1].type, 'padding')
        self.assertEqual(layout[2].name, 'b')

if __name__ == '__main__':
    unittest.main()
