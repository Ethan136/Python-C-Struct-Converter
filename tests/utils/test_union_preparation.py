import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.struct_model import calculate_layout
from src.model.layout import BaseLayoutCalculator, LayoutItem
from src.model.struct_parser import parse_c_definition
from tests.data_driven.xml_union_preparation_loader import load_union_preparation_tests


class DummyCalculator(BaseLayoutCalculator):
    def calculate(self, members):
        self.layout = [LayoutItem(name='dummy', type='char', size=1, offset=0, is_bitfield=False, bit_offset=0, bit_size=8)]
        return self.layout, 1, 1


class TestUnionPreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_union_preparation_config.xml')
        cls.cases = load_union_preparation_tests(xml_path)

    def test_union_preparation_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                if case['type'] == 'custom':
                    layout, total, align = calculate_layout([('char', 'a')], calculator_cls=DummyCalculator)
                    self.assertEqual(total, case['expected_total'])
                    self.assertEqual(align, case['expected_align'])
                    self.assertEqual(layout[0].name, case['expected_name'])
                elif case['type'] == 'parse_definition':
                    kind, name, members = parse_c_definition(case['struct_definition'])
                    self.assertEqual(kind, 'struct')
                    self.assertEqual(name, 'A')
                    self.assertEqual(len(members), 1)
                    self.assertEqual(members[0], ('int', 'x'))


if __name__ == '__main__':
    unittest.main()
