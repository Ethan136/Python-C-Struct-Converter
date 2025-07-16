import unittest
from src.model.struct_model import calculate_layout
from src.model.layout import BaseLayoutCalculator, LayoutItem
from src.model.struct_parser import parse_c_definition

class DummyCalculator(BaseLayoutCalculator):
    def calculate(self, members):
        self.layout = [LayoutItem(name='dummy', type='char', size=1, offset=0, is_bitfield=False, bit_offset=0, bit_size=8)]
        return self.layout, 1, 1

class TestCalculateLayoutCustom(unittest.TestCase):
    def test_custom_calculator_parameter(self):
        layout, total, align = calculate_layout([('char', 'a')], calculator_cls=DummyCalculator)
        self.assertEqual(total, 1)
        self.assertEqual(align, 1)
        self.assertEqual(layout[0].name, 'dummy')

class TestParseCDefinition(unittest.TestCase):
    def test_parse_struct_returns_kind(self):
        content = """
        struct A {
            int x;
        };
        """
        kind, name, members = parse_c_definition(content)
        self.assertEqual(kind, 'struct')
        self.assertEqual(name, 'A')
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0], ('int', 'x'))

if __name__ == '__main__':
    unittest.main()
