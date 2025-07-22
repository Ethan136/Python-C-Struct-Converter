import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.layout import LayoutCalculator
from tests.data_driven.xml_pack_alignment_loader import load_pack_alignment_tests


class TestPackAlignmentPlaceholder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_pack_alignment_placeholder_config.xml')
        cls.cases = load_pack_alignment_tests(xml_path)

    def test_pack_alignment_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                if case.get('type') == 'nested':
                    offsets, total = self._calc_nested_case(case)
                else:
                    calc = LayoutCalculator(pack_alignment=case.get('pack', 4))
                    layout, total, _ = calc.calculate(case['members'])
                    offsets = {item.name: item.offset for item in layout if item.name in case['expected_offsets']}

                for name, offset in case['expected_offsets'].items():
                    self.assertEqual(offsets[name], offset)
                if case.get('expected_total_size') is not None:
                    self.assertEqual(total, case['expected_total_size'])

    def _calc_nested_case(self, case):
        pack = case.get('pack', 4)
        members = case['members']
        inner_member = next(m for m in members if m['name'] == 'b')
        inner_calc = LayoutCalculator(pack_alignment=pack)
        _, inner_size, inner_align = inner_calc.calculate(inner_member['nested']['members'])

        def eff(al):
            return min(al, pack) if pack else al

        offsets = {}
        offset = 0
        max_align = 1

        # char a
        align_a = eff(1)
        offsets['a'] = offset
        offset += 1
        max_align = max(max_align, align_a)

        # struct b
        align_b = eff(inner_align)
        offset = (offset + align_b - 1) // align_b * align_b
        offsets['b'] = offset
        offset += inner_size
        max_align = max(max_align, align_b)

        # short c
        align_c = eff(2)
        offset = (offset + align_c - 1) // align_c * align_c
        offsets['c'] = offset
        offset += 2
        max_align = max(max_align, align_c)

        final_align = eff(max_align)
        total = (offset + final_align - 1) // final_align * final_align
        return offsets, total


if __name__ == '__main__':
    unittest.main()
