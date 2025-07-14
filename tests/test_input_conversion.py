import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import tempfile
from model.input_field_processor import InputFieldProcessor
from model.struct_model import StructModel
from tests.xml_input_conversion_loader import load_input_conversion_tests, load_input_conversion_error_tests

class TestInputConversion(unittest.TestCase):
    """Test cases for input conversion mechanism"""
    
    @classmethod
    def setUpClass(cls):
        # 載入 XML 驅動測資
        config_file_path = os.path.join(os.path.dirname(__file__), 'data', 'test_input_conversion_config.xml')
        cls.xml_cases = load_input_conversion_tests(config_file_path)
        # 載入異常測資
        error_file_path = os.path.join(os.path.dirname(__file__), 'data', 'test_input_conversion_error_config.xml')
        cls.error_cases = load_input_conversion_error_tests(error_file_path)

    def setUp(self):
        self.model = StructModel()
        # 建立測試 struct
        self.test_struct_content = """
struct TestStruct {
    char a;
    int b;
    long long c;
    char d;
    int e;
    char f;
};
"""
        self.tmp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.h')
        self.tmp_file.write(self.test_struct_content)
        self.tmp_file.close()
        self.struct_name, self.layout, self.total_size, self.struct_align = \
            self.model.load_struct_from_file(self.tmp_file.name)

    def tearDown(self):
        if os.path.exists(self.tmp_file.name):
            os.unlink(self.tmp_file.name)

    def convert_input_to_bytes(self, input_val, byte_size, byte_order='big'):
        int_value = int(input_val, 16) if input_val else 0
        bytes_result = int_value.to_bytes(byte_size, byteorder=byte_order)
        hex_result = bytes_result.hex()
        return int_value, bytes_result, hex_result

    # ===================== XML 驅動測試 =====================
    def test_xml_input_conversion(self):
        for case in self.xml_cases:
            unit_size = case['unit_size']
            input_values = case['input_values']
            expected_results = case['expected_results']
            name = case['name']
            with self.subTest(name=name):
                for idx, (input_val, expect) in enumerate(zip(input_values, expected_results)):
                    # big endian
                    _, _, hex_big = self.convert_input_to_bytes(input_val, unit_size, 'big')
                    self.assertEqual(hex_big, expect['big_endian'],
                        f"[big] {name} idx={idx} input={input_val} expect={expect['big_endian']} got={hex_big}")
                    # little endian
                    _, _, hex_little = self.convert_input_to_bytes(input_val, unit_size, 'little')
                    self.assertEqual(hex_little, expect['little_endian'],
                        f"[little] {name} idx={idx} input={input_val} expect={expect['little_endian']} got={hex_little}")

    # ===================== XML 驅動異常測試 =====================
    def test_xml_input_conversion_errors(self):
        for case in self.error_cases:
            with self.subTest(name=case['name']):
                error_type = eval(case['error_type'])
                with self.assertRaises(error_type):
                    self.convert_input_to_bytes(case['input'], case['byte_size'], 'big')

    # ===================== 保留/整合原有 hardcode 測試 =====================
    def test_model_parsing_integration(self):
        hex_data = "12"  # 1-byte value
        byte_order = 'big'
        parsed_values = self.model.parse_hex_data(hex_data, byte_order)
        self.assertGreater(len(parsed_values), 0, "Model should parse at least one value")
        for item in parsed_values:
            self.assertIn('name', item)
            self.assertIn('value', item)
            self.assertIn('hex_raw', item)
            if item['value'] != "-":
                self.assertIsInstance(item['value'], str)
                self.assertIsInstance(item['hex_raw'], str)
                self.assertEqual(len(item['hex_raw']) % 2, 0)
                break

    def test_endianness_consistency(self):
        input_val = "12345678"
        byte_size = 4
        int_value_big, bytes_big, hex_big = self.convert_input_to_bytes(input_val, byte_size, 'big')
        int_value_little, bytes_little, hex_little = self.convert_input_to_bytes(input_val, byte_size, 'little')
        self.assertNotEqual(hex_big, hex_little)
        self.assertEqual(int_value_big, int_value_little)

if __name__ == "__main__":
    unittest.main() 