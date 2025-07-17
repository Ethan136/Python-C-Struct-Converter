import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.struct_model import parse_struct_definition, calculate_layout
from src.model.layout import LayoutItem
from tests.data_driven.xml_struct_parsing_loader import load_struct_parsing_tests

import xml.etree.ElementTree as ET
from src.model.struct_parser import parse_struct_definition_ast


def _assert_ast_matches_xml(member_ast, member_xml):
    # member_ast: MemberDef
    # member_xml: ElementTree.Element <member>
    assert member_ast.type == member_xml.get('type')
    assert member_ast.name == member_xml.get('name')
    nested_xml = member_xml.find('nested_members')
    if nested_xml is not None:
        assert member_ast.nested is not None
        ast_members = member_ast.nested.members
        xml_members = list(nested_xml.findall('member'))
        assert len(ast_members) == len(xml_members)
        for am, xm in zip(ast_members, xml_members):
            _assert_ast_matches_xml(am, xm)
    else:
        assert member_ast.nested is None


class TestStructParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_parsing_config.xml')
        cls.cases = load_struct_parsing_tests(xml_path)

    def test_struct_parsing_cases(self):
        for case in self.cases:
            with self.subTest(case=case['name']):
                if case['type'] == 'parse':
                    # 巢狀 struct case 改用 AST 驗證
                    if case['name'] == 'nested_struct_basic':
                        from src.model.struct_parser import parse_struct_definition_ast
                        sdef = parse_struct_definition_ast(case['struct_definition'])
                        ast_members = sdef.members
                        expected_members = case['expected_members']
                        # 遞迴比對 AST
                        for am, em in zip(ast_members, expected_members):
                            self.assertEqual(am.type, em['type'])
                            self.assertEqual(am.name, em['name'])
                            if am.type == 'struct' and 'nested_members' in em:
                                self.assertIsNotNone(am.nested)
                                for am2, em2 in zip(am.nested.members, em['nested_members']):
                                    self.assertEqual(am2.type, em2['type'])
                                    self.assertEqual(am2.name, em2['name'])
                        continue
                    struct_name, members = parse_struct_definition(case['struct_definition'])
                    if case.get('expect_none'):
                        self.assertIsNone(struct_name)
                        self.assertIsNone(members)
                        continue
                    self.assertEqual(struct_name, case['expected_struct_name'])
                    self.assertEqual(len(members), len(case['expected_members']))
                    for m, exp in zip(members, case['expected_members']):
                        if isinstance(m, tuple):
                            try:
                                self.assertEqual(m, (exp['type'], exp['name']))
                            except AssertionError:
                                print(f"\n[DEBUG] Case: {case['name']}")
                                print(f"Struct definition:\n{case['struct_definition']}")
                                print(f"Parsed members: {members}")
                                print(f"Expected members: {case['expected_members']}")
                                raise
                        else:
                            self.assertEqual(m['type'], exp['type'])
                            self.assertEqual(m['name'], exp['name'])
                            if exp.get('is_bitfield'):
                                self.assertTrue(m.get('is_bitfield'))
                                self.assertEqual(m['bit_size'], exp['bit_size'])
                else:  # layout tests
                    _, members = parse_struct_definition(case['struct_definition'])
                    layout, total_size, align = calculate_layout(members)
                    self.assertEqual(total_size, case['expected_total_size'])
                    self.assertEqual(align, case['expected_alignment'])
                    self.assertEqual(len(layout), len(case['expected_layout']))
                    for item, exp in zip(layout, case['expected_layout']):
                        if exp.get('type') == 'padding':
                            self.assertEqual(item['type'], 'padding')
                            self.assertEqual(item['size'], exp['size'])
                        else:
                            # LayoutItem object expected
                            self.assertIsInstance(item, LayoutItem)
                            self.assertEqual(item.name, exp['name'])
                            self.assertEqual(item.offset, exp['offset'])
                            self.assertEqual(item.size, exp['size'])
                            if 'bit_offset' in exp:
                                self.assertEqual(item.bit_offset, exp['bit_offset'])
                            if 'bit_size' in exp:
                                self.assertEqual(item.bit_size, exp['bit_size'])
                    if case['name'] == 'layout_item_dataclass':
                        self.assertTrue(all(isinstance(i, LayoutItem) for i in layout))


def test_struct_ast_nested_from_xml():
    xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_parsing_config.xml')
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for case in root.findall('test_case'):
        if case.get('name') == 'nested_struct_basic':
            struct_def = case.find('struct_definition').text
            expected_members = case.find('expected_members')
            sdef = parse_struct_definition_ast(struct_def)
            ast_members = sdef.members
            xml_members = list(expected_members.findall('member'))
            assert len(ast_members) == len(xml_members)
            for am, xm in zip(ast_members, xml_members):
                _assert_ast_matches_xml(am, xm)


if __name__ == '__main__':
    unittest.main()
