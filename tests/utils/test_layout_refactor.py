import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.layout import BaseLayoutCalculator, StructLayoutCalculator, LayoutCalculator
from tests.data_driven.xml_layout_refactor_loader import load_layout_refactor_tests


class TestLayoutRefactor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_layout_refactor_config.xml')
        cls.cases = load_layout_refactor_tests(xml_path)

    def test_layout_refactor_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                if case['type'] == 'abstract':
                    with self.assertRaises(TypeError):
                        BaseLayoutCalculator()
                elif case['type'] == 'alias':
                    self.assertIs(LayoutCalculator, StructLayoutCalculator)
                elif case['type'] == 'compare':
                    members = case['members']
                    calc_alias = LayoutCalculator()
                    calc_struct = StructLayoutCalculator()
                    layout1, total1, align1 = calc_alias.calculate(members)
                    layout2, total2, align2 = calc_struct.calculate(members)
                    self.assertEqual(total1, total2)
                    self.assertEqual(align1, align2)
                    tuple1 = [(i.name, i.offset, i.size) for i in layout1]
                    tuple2 = [(i.name, i.offset, i.size) for i in layout2]
                    self.assertEqual(tuple1, tuple2)


if __name__ == '__main__':
    unittest.main()
