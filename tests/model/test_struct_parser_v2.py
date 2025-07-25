import unittest
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, '..', 'src'))
sys.path.insert(0, project_root)

from src.model.struct_parser import (
    parse_member_line_v2,
    parse_struct_definition_v2,
    parse_struct_definition_ast,
    MemberDef,
    StructDef,
)
from src.model.layout import LayoutCalculator
from tests.data_driven.xml_struct_parser_v2_loader import load_struct_parser_v2_tests
from tests.data_driven.xml_struct_parser_v2_struct_loader import load_struct_parser_v2_struct_tests

class TestParseMemberLineV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data',
                                   'test_struct_parser_v2_config.xml')
        cls.cases = load_struct_parser_v2_tests(config_path)

    def test_member_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                m = parse_member_line_v2(case['line'])
                self.assertIsInstance(m, MemberDef)
                self.assertEqual(m.type, case['expected']['type'])
                self.assertEqual(m.name, case['expected']['name'])
                if 'is_bitfield' in case['expected']:
                    self.assertEqual(m.is_bitfield, case['expected']['is_bitfield'])
                if 'bit_size' in case['expected']:
                    self.assertEqual(m.bit_size, case['expected']['bit_size'])

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

class TestParseStructDefinitionAst(unittest.TestCase):
    def test_ast_return(self):
        content = '''
        struct Simple {
            char a;
            int b;
        };
        '''
        sdef = parse_struct_definition_ast(content)
        self.assertIsInstance(sdef, StructDef)
        self.assertEqual(sdef.name, 'Simple')
        self.assertEqual(len(sdef.members), 2)
        self.assertIsInstance(sdef.members[0], MemberDef)

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

class TestParseStructDefinitionV2XMLDriven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_parser_v2_struct_config.xml')
        cls.cases = load_struct_parser_v2_struct_tests(config_path)

    def test_struct_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                # struct_name, members
                name, members = parse_struct_definition_v2(case['struct_definition'])
                self.assertEqual(name, case['expected_struct_name'])
                self.assertEqual(len(members), len(case['expected_members']))
                for m, exp in zip(members, case['expected_members']):
                    self.assertEqual(m.type, exp['type'])
                    self.assertEqual(m.name, exp['name'])
                # AST
                sdef = parse_struct_definition_ast(case['struct_definition'])
                self.assertEqual(sdef.name, case['expected_struct_name'])
                self.assertEqual(len(sdef.members), len(case['expected_members']))
                for m, exp in zip(sdef.members, case['expected_members']):
                    self.assertEqual(m.type, exp['type'])
                    self.assertEqual(m.name, exp['name'])
                # layout
                calc = LayoutCalculator()
                layout, total, align = calc.calculate(members)
                self.assertEqual(total, case['expected_total_size'])
                self.assertEqual(align, case['expected_align'])
                self.assertEqual(len(layout), len(case['expected_layout']))
                for item, exp in zip(layout, case['expected_layout']):
                    self.assertEqual(item.name, exp['name'])
                    self.assertEqual(item.type, exp['type'])
                    self.assertEqual(item.offset, exp['offset'])
                    self.assertEqual(item.size, exp['size'])

if __name__ == '__main__':
    unittest.main()

