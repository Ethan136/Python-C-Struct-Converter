import os
import unittest
from model.struct_model import StructModel

class TestUnionIntegration(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()
        self.file_path = os.path.join(os.path.dirname(__file__), 'data', 'union_test.h')

    def test_load_and_parse_union(self):
        name, layout, total, align = self.model.load_struct_from_file(self.file_path)
        self.assertEqual(name, 'U')
        self.assertEqual(total, 4)
        self.assertEqual(align, 4)
        self.assertEqual(len(layout), 2)
        for item in layout:
            self.assertEqual(item.offset, 0)

    def test_parse_hex_data(self):
        self.model.load_struct_from_file(self.file_path)
        hex_data = '01020304'  # first member int = 0x04030201 little-endian
        values = self.model.parse_hex_data(hex_data, 'little')
        self.assertEqual(values[0]['value'], '67305985')
        self.assertEqual(values[1]['value'], '1')

if __name__ == '__main__':
    unittest.main()
