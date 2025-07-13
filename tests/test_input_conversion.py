import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import tempfile
import pytest
from model.input_field_processor import InputFieldProcessor
from model.struct_model import StructModel
from tests.test_config_parser import TestConfigParser

class TestInputConversion(unittest.TestCase):
    """Test cases for input conversion mechanism"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = StructModel()
        
        # Create a test struct for comprehensive testing
        self.test_struct_content = """
struct TestStruct {
    char a;           // 1 byte
    int b;            // 4 bytes  
    long long c;      // 8 bytes
    char d;           // 1 byte
    int e;            // 4 bytes
    char f;           // 1 byte
};
"""
        
        # Create temporary file for testing
        self.tmp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.h')
        self.tmp_file.write(self.test_struct_content)
        self.tmp_file.close()
        
        # Load the struct
        self.struct_name, self.layout, self.total_size, self.struct_align = \
            self.model.load_struct_from_file(self.tmp_file.name)
        
        # Load test configurations
        config_file_path = os.path.join(os.path.dirname(__file__), 'data', 'test_input_conversion_config.xml')
        if os.path.exists(config_file_path):
            self.config_parser = TestConfigParser(config_file_path)
            self.test_configs = self.config_parser.parse()
        else:
            self.test_configs = {}

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.tmp_file.name):
            os.unlink(self.tmp_file.name)

    def convert_input_to_bytes(self, input_val, byte_size, byte_order='big'):
        """
        Simulates the exact conversion logic from struct_presenter.py
        """
        # Step 1: Convert input to integer (handles empty as 0)
        int_value = int(input_val, 16) if input_val else 0
        
        # Step 2: Convert to bytes with specified endianness
        bytes_result = int_value.to_bytes(byte_size, byteorder=byte_order)
        hex_result = bytes_result.hex()
        
        return int_value, bytes_result, hex_result

    def test_4byte_field_expansion(self):
        """Test 4-byte field expansion requirement"""
        # Requirement: 4-byte field input 12 -> expand to 00000012
        input_val = "12"
        byte_size = 4
        expected_big = "00000012"
        expected_little = "12000000"
        
        # Test big endian
        int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, byte_size, 'big')
        self.assertEqual(hex_result, expected_big, 
                        f"4-byte field expansion failed: expected {expected_big}, got {hex_result}")
        
        # Test little endian
        int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, byte_size, 'little')
        self.assertEqual(hex_result_le, expected_little,
                        f"4-byte field little endian failed: expected {expected_little}, got {hex_result_le}")

    def test_8byte_field_expansion(self):
        """Test 8-byte field expansion requirement"""
        # Requirement: 8-byte field input 123 -> expand to 0000000000000123
        input_val = "123"
        byte_size = 8
        expected_big = "0000000000000123"
        expected_little = "2301000000000000"
        
        # Test big endian
        int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, byte_size, 'big')
        self.assertEqual(hex_result, expected_big,
                        f"8-byte field expansion failed: expected {expected_big}, got {hex_result}")
        
        # Test little endian
        int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, byte_size, 'little')
        self.assertEqual(hex_result_le, expected_little,
                        f"8-byte field little endian failed: expected {expected_little}, got {hex_result_le}")

    def test_1byte_field_expansion(self):
        """Test 1-byte field expansion requirement"""
        # Requirement: 1-byte field input 1 -> expand to 01
        input_val = "1"
        byte_size = 1
        expected = "01"  # Same for both endianness
        
        # Test big endian
        int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, byte_size, 'big')
        self.assertEqual(hex_result, expected,
                        f"1-byte field expansion failed: expected {expected}, got {hex_result}")
        
        # Test little endian
        int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, byte_size, 'little')
        self.assertEqual(hex_result_le, expected,
                        f"1-byte field little endian failed: expected {expected}, got {hex_result_le}")

    def test_empty_field_handling(self):
        """Test empty field handling requirement"""
        # Requirement: Empty 1/4/8 byte fields -> all zeros
        test_cases = [
            ("", 1, "00"),                    # 1-byte empty
            ("", 4, "00000000"),              # 4-byte empty
            ("", 8, "0000000000000000"),      # 8-byte empty
        ]
        
        for input_val, byte_size, expected in test_cases:
            with self.subTest(input_val=input_val, byte_size=byte_size):
                int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, byte_size, 'big')
                self.assertEqual(hex_result, expected,
                                f"Empty field handling failed for {byte_size}-byte: expected {expected}, got {hex_result}")

    def test_various_input_scenarios(self):
        """Test various input scenarios"""
        test_cases = [
            # (input_value, byte_size, expected_big, expected_little, description)
            ("ABCDEF01", 4, "abcdef01", "01efcdab", "4-byte field with full value"),
            ("123456789ABCDEF0", 8, "123456789abcdef0", "f0debc9a78563412", "8-byte field with full value"),
            ("FF", 1, "ff", "ff", "1-byte field with full value"),
            ("A", 1, "0a", "0a", "1-byte field with single hex digit"),
            ("ABC", 4, "00000abc", "bc0a0000", "4-byte field with 3 hex digits"),
            ("123456", 8, "0000000000123456", "5634120000000000", "8-byte field with 6 hex digits"),
        ]
        
        for input_val, byte_size, expected_big, expected_little, description in test_cases:
            with self.subTest(description=description):
                # Test big endian
                int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, byte_size, 'big')
                self.assertEqual(hex_result, expected_big,
                                f"Big endian failed for {description}: expected {expected_big}, got {hex_result}")
                
                # Test little endian
                int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, byte_size, 'little')
                self.assertEqual(hex_result_le, expected_little,
                                f"Little endian failed for {description}: expected {expected_little}, got {hex_result_le}")

    def test_value_range_validation(self):
        """Test value range validation"""
        # Test that values too large for their byte size are handled correctly
        test_cases = [
            ("100000000", 4),  # Too large for 4 bytes
            ("10000000000000000", 8),  # Too large for 8 bytes
        ]
        
        for input_val, byte_size in test_cases:
            with self.subTest(input_val=input_val, byte_size=byte_size):
                # This should raise an OverflowError
                with self.assertRaises(OverflowError):
                    self.convert_input_to_bytes(input_val, byte_size, 'big')

    def test_invalid_hex_input(self):
        """Test invalid hex input handling"""
        # Test that non-hex characters are handled correctly
        invalid_inputs = ["GG", "12G", "XYZ", "12.34"]
        
        for input_val in invalid_inputs:
            with self.subTest(input_val=input_val):
                # This should raise a ValueError
                with self.assertRaises(ValueError):
                    self.convert_input_to_bytes(input_val, 4, 'big')

    def test_model_parsing_integration(self):
        """Test integration with model parsing"""
        # Test that the model correctly parses the converted data
        hex_data = "12"  # 1-byte value
        byte_order = 'big'
        
        # The model should pad this to the total size and parse correctly
        parsed_values = self.model.parse_hex_data(hex_data, byte_order)
        
        # Should have parsed values
        self.assertGreater(len(parsed_values), 0, "Model should parse at least one value")
        
        # Check that parsed values have the expected structure
        for item in parsed_values:
            self.assertIn('name', item, "Parsed item should have a name")
            self.assertIn('value', item, "Parsed item should have a value")
            self.assertIn('hex_raw', item, "Parsed item should have hex_raw")
            
            # Skip padding entries (they have value "-")
            if item['value'] != "-":
                # Check that the value is a valid string representation
                self.assertIsInstance(item['value'], str, "Value should be a string")
                # Check that hex_raw is a valid hex string
                self.assertIsInstance(item['hex_raw'], str, "hex_raw should be a string")
                # hex_raw should have even length (each byte = 2 hex chars)
                self.assertEqual(len(item['hex_raw']) % 2, 0, "hex_raw should have even length")
                break

    def test_endianness_consistency(self):
        """Test that endianness is applied consistently"""
        input_val = "12345678"
        byte_size = 4
        
        # Big endian: 12345678 -> 12345678
        int_value_big, bytes_big, hex_big = self.convert_input_to_bytes(input_val, byte_size, 'big')
        
        # Little endian: 12345678 -> 78563412
        int_value_little, bytes_little, hex_little = self.convert_input_to_bytes(input_val, byte_size, 'little')
        
        # Values should be different for multi-byte fields
        self.assertNotEqual(hex_big, hex_little, 
                           "Big and little endian should produce different results for multi-byte values")
        
        # But the integer value should be the same
        self.assertEqual(int_value_big, int_value_little,
                        "Integer value should be the same regardless of endianness")

    # =========================================================================
    # 已搬移至 XML 驅動測試的 input/output 驗證，請見 test_xml_all_configs 等
    # =========================================================================

    def test_xml_config_loading(self):
        """Test that XML configuration files can be loaded correctly"""
        if not self.test_configs:
            self.skipTest("No XML configuration file found")
        
        # Check that we have test configurations
        self.assertGreater(len(self.test_configs), 0, "Should have at least one test configuration")
        
        # Check that all configurations are valid
        errors = self.config_parser.validate_config()
        self.assertEqual(len(errors), 0, f"Configuration validation failed: {errors}")

    def test_xml_4byte_config(self):
        """Test 4-byte configuration from XML"""
        if '4byte_test' not in self.test_configs:
            self.skipTest("4byte_test configuration not found in XML")
        
        config = self.test_configs['4byte_test']
        
        # Verify configuration
        self.assertEqual(config.unit_size, 4, "Unit size should be 4")
        self.assertEqual(len(config.input_values), 5, "Should have 5 input values")
        
        # Test each input value
        input_values = config.get_input_values_list()
        expected_results = config.get_expected_results_list()
        
        for i, (input_val, expected_result) in enumerate(zip(input_values, expected_results)):
            with self.subTest(index=i, input=input_val):
                # Test big endian
                int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, config.unit_size, 'big')
                self.assertEqual(hex_result, expected_result['big_endian'],
                                f"Big endian failed for index {i}: expected {expected_result['big_endian']}, got {hex_result}")
                
                # Test little endian
                int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, config.unit_size, 'little')
                self.assertEqual(hex_result_le, expected_result['little_endian'],
                                f"Little endian failed for index {i}: expected {expected_result['little_endian']}, got {hex_result_le}")

    def test_xml_8byte_config(self):
        """Test 8-byte configuration from XML"""
        if '8byte_test' not in self.test_configs:
            self.skipTest("8byte_test configuration not found in XML")
        
        config = self.test_configs['8byte_test']
        
        # Verify configuration
        self.assertEqual(config.unit_size, 8, "Unit size should be 8")
        self.assertEqual(len(config.input_values), 3, "Should have 3 input values")
        
        # Test each input value
        input_values = config.get_input_values_list()
        expected_results = config.get_expected_results_list()
        
        for i, (input_val, expected_result) in enumerate(zip(input_values, expected_results)):
            with self.subTest(index=i, input=input_val):
                # Test big endian
                int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, config.unit_size, 'big')
                self.assertEqual(hex_result, expected_result['big_endian'],
                                f"Big endian failed for index {i}: expected {expected_result['big_endian']}, got {hex_result}")
                
                # Test little endian
                int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, config.unit_size, 'little')
                self.assertEqual(hex_result_le, expected_result['little_endian'],
                                f"Little endian failed for index {i}: expected {expected_result['little_endian']}, got {hex_result_le}")

    def test_xml_1byte_config(self):
        """Test 1-byte configuration from XML"""
        if '1byte_test' not in self.test_configs:
            self.skipTest("1byte_test configuration not found in XML")
        
        config = self.test_configs['1byte_test']
        
        # Verify configuration
        self.assertEqual(config.unit_size, 1, "Unit size should be 1")
        self.assertEqual(len(config.input_values), 4, "Should have 4 input values")
        
        # Test each input value
        input_values = config.get_input_values_list()
        expected_results = config.get_expected_results_list()
        
        for i, (input_val, expected_result) in enumerate(zip(input_values, expected_results)):
            with self.subTest(index=i, input=input_val):
                # Test big endian
                int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, config.unit_size, 'big')
                self.assertEqual(hex_result, expected_result['big_endian'],
                                f"Big endian failed for index {i}: expected {expected_result['big_endian']}, got {hex_result}")
                
                # Test little endian
                int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, config.unit_size, 'little')
                self.assertEqual(hex_result_le, expected_result['little_endian'],
                                f"Little endian failed for index {i}: expected {expected_result['little_endian']}, got {hex_result_le}")

    def test_xml_mixed_config(self):
        """Test mixed configuration from XML (including empty values)"""
        if 'mixed_test' not in self.test_configs:
            self.skipTest("mixed_test configuration not found in XML")
        
        config = self.test_configs['mixed_test']
        
        # Verify configuration
        self.assertEqual(config.unit_size, 4, "Unit size should be 4")
        self.assertEqual(len(config.input_values), 4, "Should have 4 input values")
        
        # Test each input value
        input_values = config.get_input_values_list()
        expected_results = config.get_expected_results_list()
        
        for i, (input_val, expected_result) in enumerate(zip(input_values, expected_results)):
            with self.subTest(index=i, input=input_val):
                # Test big endian
                int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, config.unit_size, 'big')
                self.assertEqual(hex_result, expected_result['big_endian'],
                                f"Big endian failed for index {i}: expected {expected_result['big_endian']}, got {hex_result}")
                
                # Test little endian
                int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, config.unit_size, 'little')
                self.assertEqual(hex_result_le, expected_result['little_endian'],
                                f"Little endian failed for index {i}: expected {expected_result['little_endian']}, got {hex_result_le}")

    def test_xml_edge_cases_config(self):
        """Test edge cases configuration from XML"""
        if 'edge_cases_test' not in self.test_configs:
            self.skipTest("edge_cases_test configuration not found in XML")
        
        config = self.test_configs['edge_cases_test']
        
        # Verify configuration
        self.assertEqual(config.unit_size, 4, "Unit size should be 4")
        self.assertEqual(len(config.input_values), 3, "Should have 3 input values")
        
        # Test each input value
        input_values = config.get_input_values_list()
        expected_results = config.get_expected_results_list()
        
        for i, (input_val, expected_result) in enumerate(zip(input_values, expected_results)):
            with self.subTest(index=i, input=input_val):
                # Test big endian
                int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, config.unit_size, 'big')
                self.assertEqual(hex_result, expected_result['big_endian'],
                                f"Big endian failed for index {i}: expected {expected_result['big_endian']}, got {hex_result}")
                
                # Test little endian
                int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, config.unit_size, 'little')
                self.assertEqual(hex_result_le, expected_result['little_endian'],
                                f"Little endian failed for index {i}: expected {expected_result['little_endian']}, got {hex_result_le}")

    def test_xml_all_configs(self):
        """Test all configurations from XML file"""
        if not self.test_configs:
            self.skipTest("No XML configuration file found")
        
        # Test all configurations
        for config_name, config in self.test_configs.items():
            with self.subTest(config_name=config_name):
                input_values = config.get_input_values_list()
                expected_results = config.get_expected_results_list()
                
                for i, (input_val, expected_result) in enumerate(zip(input_values, expected_results)):
                    with self.subTest(index=i, input=input_val):
                        # Test big endian
                        int_value, bytes_result, hex_result = self.convert_input_to_bytes(input_val, config.unit_size, 'big')
                        self.assertEqual(hex_result, expected_result['big_endian'],
                                        f"Big endian failed for {config_name}[{i}]: expected {expected_result['big_endian']}, got {hex_result}")
                        
                        # Test little endian
                        int_value_le, bytes_result_le, hex_result_le = self.convert_input_to_bytes(input_val, config.unit_size, 'little')
                        self.assertEqual(hex_result_le, expected_result['little_endian'],
                                        f"Little endian failed for {config_name}[{i}]: expected {expected_result['little_endian']}, got {hex_result_le}")

def test_convert_to_raw_bytes_valid():
    processor = InputFieldProcessor()
    # big endian
    assert processor.process_input_field("00000012", 4, 'big') == b'\x00\x00\x00\x12'
    # little endian
    assert processor.process_input_field("00000012", 4, 'little') == b'\x12\x00\x00\x00'

def test_convert_to_raw_bytes_invalid_endianness():
    processor = InputFieldProcessor()
    with pytest.raises(ValueError):
        processor.process_input_field("00000012", 4, 'middle')

def test_convert_to_raw_bytes_invalid_hex():
    processor = InputFieldProcessor()
    with pytest.raises(ValueError):
        processor.process_input_field("zzzzzzzz", 4, 'big')

def test_convert_to_raw_bytes_length_mismatch():
    processor = InputFieldProcessor()
    # 7 bytes = 14 hex digits, 15 hex digits為長度錯誤，這裡會因 int() 失敗或 overflow
    with pytest.raises(Exception):
        processor.process_input_field("100000000000000", 7, 'big')

def test_convert_to_raw_bytes_max_value():
    processor = InputFieldProcessor()
    # 7 bytes = 14 hex digits, 最大值 0xfffffffffffffff，不會 overflow
    processor.process_input_field("ffffffffffffff", 7, 'big')  # 不應該丟出異常

def test_is_supported_field_size():
    processor = InputFieldProcessor()
    assert processor.is_supported_field_size(1)
    assert processor.is_supported_field_size(4)
    assert processor.is_supported_field_size(8)
    assert not processor.is_supported_field_size(2)
    assert not processor.is_supported_field_size(16)

if __name__ == '__main__':
    unittest.main() 