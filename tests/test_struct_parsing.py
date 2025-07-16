import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.struct_model import parse_struct_definition, calculate_layout
from model.layout import LayoutCalculator, LayoutItem
from tests.xml_struct_parsing_loader import load_struct_parsing_tests


class TestStructParsingXMLDriven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = os.path.join(
            os.path.dirname(__file__), 'data', 'test_struct_parsing_config.xml'
        )
        cls.cases = load_struct_parsing_tests(config_path)

    def test_struct_parsing_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                if case.get('struct_definition') is not None:
                    struct_name, members = parse_struct_definition(case['struct_definition'])
                    if case.get('expect_none'):
                        self.assertIsNone(struct_name)
                        self.assertIsNone(members)
                    else:
                        self.assertEqual(struct_name, case.get('expected_struct_name'))
                        if 'expected_members' in case:
                            self.assertEqual(len(members), len(case['expected_members']))
                            for m, expect in zip(members, case['expected_members']):
                                if isinstance(m, tuple):
                                    self.assertEqual(m[0], expect['type'])
                                    self.assertEqual(m[1], expect['name'])
                                else:
                                    self.assertEqual(m['type'], expect['type'])
                                    self.assertEqual(m['name'], expect['name'])
                                    if expect.get('is_bitfield'):
                                        self.assertTrue(m.get('is_bitfield'))
                                        self.assertEqual(m['bit_size'], expect['bit_size'])
                if case.get('members') is not None:
                    calc = LayoutCalculator()
                    layout, total_size, alignment = calc.calculate(case['members'])
                    if 'expected_total_size' in case:
                        self.assertEqual(total_size, case['expected_total_size'])
                    if 'expected_alignment' in case:
                        self.assertEqual(alignment, case['expected_alignment'])
                    if 'expected_layout_len' in case:
                        self.assertEqual(len(layout), case['expected_layout_len'])
                    if 'expected_layout' in case:
                        for idx, expect in enumerate(case['expected_layout']):
                            item = layout[idx]
                            self.assertEqual(item['name'], expect['name'])
                            if 'type' in expect:
                                self.assertEqual(item['type'], expect['type'])
                            if 'offset' in expect:
                                self.assertEqual(item['offset'], expect['offset'])
                            if 'size' in expect:
                                self.assertEqual(item['size'], expect['size'])
                            if 'bit_offset' in expect:
                                self.assertEqual(item['bit_offset'], expect['bit_offset'])
                            if 'bit_size' in expect:
                                self.assertEqual(item['bit_size'], expect['bit_size'])
                    if case.get('check_dataclass'):
                        func_layout, _, _ = calculate_layout(case['members'])
                        self.assertTrue(all(isinstance(i, LayoutItem) for i in func_layout))


if __name__ == '__main__':
    unittest.main()
