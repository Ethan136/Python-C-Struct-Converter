import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.struct_model import parse_struct_definition, calculate_layout
from src.model.layout import LayoutItem
from tests.data_driven.xml_struct_parsing_loader import load_struct_parsing_tests


class TestStructParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_parsing_config.xml')
        cls.cases = load_struct_parsing_tests(xml_path)

    def test_struct_parsing_cases(self):
        for case in self.cases:
            with self.subTest(case=case['name']):
                if case['type'] == 'parse':
                    struct_name, members = parse_struct_definition(case['struct_definition'])
                    if case.get('expect_none'):
                        self.assertIsNone(struct_name)
                        self.assertIsNone(members)
                        continue
                    self.assertEqual(struct_name, case['expected_struct_name'])
                    self.assertEqual(len(members), len(case['expected_members']))
                    for m, exp in zip(members, case['expected_members']):
                        if isinstance(m, tuple):
                            self.assertEqual(m, (exp['type'], exp['name']))
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


if __name__ == '__main__':
    unittest.main()
