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
    import xml.etree.ElementTree as ET
    def debug_write(msg):
        with open('/tmp/ast_xml_debug.txt', 'a') as f:
            f.write(msg + '\n')
    try:
        assert member_ast.type == member_xml.get('type')
    except AssertionError:
        debug_write(f"type mismatch: ast={member_ast.type}, xml={member_xml.get('type')}")
        debug_write(f"member_xml: {ET.tostring(member_xml, encoding='unicode')}")
        raise
    try:
        n1 = member_ast.name if member_ast.name is not None else ''
        n2 = member_xml.get('name') if member_xml.get('name') is not None else ''
        assert n1 == n2
    except AssertionError:
        debug_write(f"name mismatch: ast={member_ast.name}, xml={member_xml.get('name')}")
        debug_write(f"member_xml: {ET.tostring(member_xml, encoding='unicode')}")
        raise
    nested_xml = member_xml.find('nested_members')
    if nested_xml is not None:
        xml_members = list(nested_xml.findall('member'))
        ast_members = getattr(member_ast.nested, 'members', []) if member_ast.nested else []
        if len(xml_members) != len(ast_members):
            debug_write(f"nested count mismatch: xml={len(xml_members)}, ast={len(ast_members)}")
            debug_write(f"member_xml: {ET.tostring(member_xml, encoding='unicode')}")
            debug_write(f"xml_members: {xml_members}")
            debug_write(f"ast_members: {ast_members}")
            raise AssertionError("See /tmp/ast_xml_debug.txt for details")
        if xml_members:
            for am, xm in zip(ast_members, xml_members):
                _assert_ast_matches_xml(am, xm)
        else:
            if member_ast.nested is not None:
                if not hasattr(member_ast.nested, 'members') or len(member_ast.nested.members) != 0:
                    debug_write(f"empty nested mismatch: ast={member_ast.nested}")
                    raise AssertionError("See /tmp/ast_xml_debug.txt for details")
    else:
        if member_ast.nested is not None:
            if not hasattr(member_ast.nested, 'members') or len(member_ast.nested.members) != 0:
                debug_write(f"empty nested mismatch (no nested_xml): ast={member_ast.nested}")
                raise AssertionError("See /tmp/ast_xml_debug.txt for details")


class TestStructParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_parsing_config.xml')
        cls.cases = load_struct_parsing_tests(xml_path)

    def test_struct_parsing_cases_final(self):
        global parse_struct_definition_ast
        def dict_to_member_xml(d):
            attrs = ' '.join(f'{k}="{v}"' for k, v in d.items() if k != 'nested_members')
            xml = f'<member {attrs}'
            if 'nested_members' in d and d['nested_members']:
                xml += '>'
                xml += '<nested_members>'
                for child in d['nested_members']:
                    xml += dict_to_member_xml(child)
                xml += '</nested_members></member>'
            else:
                xml += '/>'
            return xml
        for case in self.cases:
            with self.subTest(case=case['name']):
                if case['type'] == 'parse':
                    # 巢狀 struct 案例改用 AST 驗證
                    if case['name'] == 'nested_struct_basic':
                        struct_def = case['struct_definition']
                        expected_members = case['expected_members']
                        # 解析 AST
                        sdef = parse_struct_definition_ast(struct_def)
                        # 一律轉為 XML 字串後 parse
                        if isinstance(expected_members, str):
                            xml = f'<root>{expected_members}</root>'
                        elif isinstance(expected_members, list):
                            xml = '<root>' + ''.join([dict_to_member_xml(e) for e in expected_members]) + '</root>'
                        else:
                            from xml.etree.ElementTree import tostring
                            xml = '<root>' + ''.join([ET.tostring(e, encoding='unicode') for e in expected_members]) + '</root>'
                        xml_members = list(ET.fromstring(xml).findall('member'))
                        ast_members = sdef.members
                        assert len(ast_members) == len(xml_members)
                        for am, xm in zip(ast_members, xml_members):
                            _assert_ast_matches_xml(am, xm)
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
                            n1 = m['name'] if m['name'] is not None else ''
                            n2 = exp['name'] if exp['name'] is not None else ''
                            self.assertEqual(n1, n2)
                            if exp.get('is_bitfield'):
                                self.assertTrue(m.get('is_bitfield'))
                                self.assertEqual(m['bit_size'], exp['bit_size'])
                    # 巢狀 struct AST 驗證
                    # 已移至上方 continue
                else:  # layout tests
                    # --- 新增：若 struct 內有 union，改用 AST 展平成員 ---
                    struct_def = case['struct_definition']
                    if 'union' in struct_def:
                        from src.model.struct_parser import parse_struct_definition_ast
                        def flatten_ast_members(ast, prefix=""):
                            flat = []
                            for m in ast.members:
                                if hasattr(m, 'nested') and m.nested:
                                    if m.type == 'union':
                                        for um in m.nested.members:
                                            flat.append({"type": um.type, "name": f"{m.name}.{um.name}", "is_bitfield": getattr(um, 'is_bitfield', False), "bit_size": getattr(um, 'bit_size', 0), "array_dims": getattr(um, 'array_dims', [])})
                                    elif m.type == 'struct':
                                        for sm in m.nested.members:
                                            flat.append({"type": sm.type, "name": f"{m.name}.{sm.name}", "is_bitfield": getattr(sm, 'is_bitfield', False), "bit_size": getattr(sm, 'bit_size', 0), "array_dims": getattr(sm, 'array_dims', [])})
                                else:
                                    flat.append({"type": m.type, "name": m.name, "is_bitfield": getattr(m, 'is_bitfield', False), "bit_size": getattr(m, 'bit_size', 0), "array_dims": getattr(m, 'array_dims', [])})
                            return flat
                        ast = parse_struct_definition_ast(struct_def)
                        members = flatten_ast_members(ast)
                    else:
                        _, members = parse_struct_definition(struct_def)
                    layout, total_size, align = calculate_layout(members)
                    print("[DEBUG] layout result:")
                    for item in layout:
                        print(f"  name={getattr(item, 'name', None)}, offset={getattr(item, 'offset', None)}, size={getattr(item, 'size', None)}, type={getattr(item, 'type', None)}")
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
