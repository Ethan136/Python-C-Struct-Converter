import unittest
import sys
import os
import xml.etree.ElementTree as ET

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.model.struct_model import StructModel
from src.model.input_field_processor import InputFieldProcessor
from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

class TestStructParsingCore(unittest.TestCase):
    """Test cases for core struct parsing functionality without GUI"""
    @classmethod
    def setUpClass(cls):
        cls.model = StructModel()
        cls.input_processor = InputFieldProcessor()
        cls.test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        cls.config_file = os.path.join(cls.test_data_dir, 'struct_parsing_test_config.xml')
        cls.loader = BaseXMLTestLoader(cls.config_file)
        cls.cases = cls.loader.cases

    def _process_input_data(self, input_data, endianness, layout, total_size):
        """Process input data using InputFieldProcessor and struct layout"""
        struct_bytes = bytearray(total_size)
        input_idx = 0
        for item in layout:
            if item['type'] == 'padding':
                continue
            input_item = input_data[input_idx]
            value = input_item['value']
            unit_size = input_item['unit_size']
            raw_bytes = self.input_processor.process_input_field(value, unit_size, endianness)
            struct_bytes[item['offset']:item['offset']+item['size']] = raw_bytes
            input_idx += 1
        return struct_bytes.hex()

    def test_struct_parsing_cases(self):
        for case in self.cases:
            struct_file = case.get('struct_file')
            if not struct_file:
                continue
            struct_file_path = os.path.join(self.test_data_dir, struct_file)
            struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(struct_file_path)
            self.assertIsNotNone(struct_name, f"Failed to load struct definition for {case['name']}")
            input_data = case.get('input_data', [])
            expected_results = case.get('expected_results', {})
            for endianness in ['little', 'big']:
                if endianness not in expected_results:
                    continue
                with self.subTest(case=case['name'], endianness=endianness):
                    hex_data = self._process_input_data(input_data, endianness, layout, total_size)
                    parsed_values = self.model.parse_hex_data(hex_data, endianness)
                    expected = expected_results[endianness]
                    for member_name, expected_data in expected.items():
                        parsed_member = next((item for item in parsed_values if item['name'] == member_name), None)
                        self.assertIsNotNone(parsed_member, f"Member '{member_name}' not found in parsed results")
                        expected_value = expected_data['expected_value']
                        actual_value = parsed_member['value']
                        self.assertEqual(actual_value, expected_value,
                                         f"Value mismatch for {member_name} in {endianness} endian: "
                                         f"expected {expected_value}, got {actual_value}")
                        expected_hex = expected_data['expected_hex']
                        actual_hex = parsed_member['hex_raw']
                        self.assertEqual(actual_hex, expected_hex,
                                         f"Hex mismatch for {member_name} in {endianness} endian: "
                                         f"expected {expected_hex}, got {actual_hex}")

if __name__ == '__main__':
    unittest.main() 