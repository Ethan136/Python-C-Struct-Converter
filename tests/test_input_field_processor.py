import unittest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.input_field_processor import InputFieldProcessor

class TestInputFieldProcessor(unittest.TestCase):
    """Test cases for InputFieldProcessor module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = InputFieldProcessor()

    def test_pad_hex_input_4byte_fields(self):
        """Test 4-byte field padding functionality"""
        test_cases = [
            ("12", "00000012"),
            ("123", "00000123"),
            ("1234", "00001234"),
            ("12345", "00012345"),
            ("123456", "00123456"),
            ("1234567", "01234567"),
            ("12345678", "12345678"),
            ("", "00000000"),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                result = self.processor.pad_hex_input(input_val, 4)
                self.assertEqual(result, expected,
                                f"4-byte padding failed: input '{input_val}' expected '{expected}', got '{result}'")

    def test_pad_hex_input_8byte_fields(self):
        """Test 8-byte field padding functionality"""
        test_cases = [
            ("123", "0000000000000123"),
            ("1234", "0000000000001234"),
            ("12345", "0000000000012345"),
            ("123456", "0000000000123456"),
            ("1234567", "0000000001234567"),
            ("12345678", "0000000012345678"),
            ("123456789", "0000000123456789"),
            ("123456789A", "000000123456789a"),
            ("123456789AB", "00000123456789ab"),
            ("123456789ABC", "0000123456789abc"),
            ("123456789ABCD", "000123456789abcd"),
            ("123456789ABCDE", "00123456789abcde"),
            ("123456789ABCDEF", "0123456789abcdef"),
            ("123456789ABCDEF0", "123456789abcdef0"),
            ("", "0000000000000000"),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                result = self.processor.pad_hex_input(input_val, 8)
                self.assertEqual(result, expected,
                                f"8-byte padding failed: input '{input_val}' expected '{expected}', got '{result}'")

    def test_pad_hex_input_1byte_fields(self):
        """Test 1-byte field padding functionality"""
        test_cases = [
            ("1", "01"),
            ("A", "0a"),
            ("F", "0f"),
            ("FF", "ff"),
            ("", "00"),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                result = self.processor.pad_hex_input(input_val, 1)
                self.assertEqual(result, expected,
                                f"1-byte padding failed: input '{input_val}' expected '{expected}', got '{result}'")

    def test_pad_hex_input_other_byte_sizes(self):
        """Test padding with other byte sizes (2, 3, 5, etc.)"""
        test_cases = [
            ("12", 2, "0012"),
            ("123", 3, "000123"),
            ("1234", 5, "0000001234"),
            ("123456", 6, "000000123456"),
            ("", 2, "0000"),
            ("", 3, "000000"),
        ]
        
        for input_val, byte_size, expected in test_cases:
            with self.subTest(input_val=input_val, byte_size=byte_size):
                result = self.processor.pad_hex_input(input_val, byte_size)
                self.assertEqual(result, expected,
                                f"{byte_size}-byte padding failed: input '{input_val}' expected '{expected}', got '{result}'")

    def test_pad_hex_input_invalid_byte_size(self):
        """Test padding with invalid byte sizes (non-positive)"""
        invalid_sizes = [0, -1, -5]
        
        for size in invalid_sizes:
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    self.processor.pad_hex_input("12", size)

    def test_convert_to_raw_bytes_big_endian(self):
        """Test conversion to raw bytes with big endian"""
        test_cases = [
            ("00000012", 4, b'\x00\x00\x00\x12'),
            ("12345678", 4, b'\x12\x34\x56\x78'),
            ("0000000000000123", 8, b'\x00\x00\x00\x00\x00\x00\x01\x23'),
            ("123456789ABCDEF0", 8, b'\x12\x34\x56\x78\x9a\xbc\xde\xf0'),
            ("01", 1, b'\x01'),
            ("FF", 1, b'\xff'),
        ]
        
        for padded_hex, byte_size, expected in test_cases:
            with self.subTest(padded_hex=padded_hex, byte_size=byte_size):
                result = self.processor.convert_to_raw_bytes(padded_hex, byte_size, 'big')
                self.assertEqual(result, expected,
                                f"Big endian conversion failed: expected {expected}, got {result}")

    def test_convert_to_raw_bytes_little_endian(self):
        """Test conversion to raw bytes with little endian"""
        test_cases = [
            ("00000012", 4, b'\x12\x00\x00\x00'),
            ("12345678", 4, b'\x78\x56\x34\x12'),
            ("0000000000000123", 8, b'\x23\x01\x00\x00\x00\x00\x00\x00'),
            ("123456789ABCDEF0", 8, b'\xf0\xde\xbc\x9a\x78\x56\x34\x12'),
            ("01", 1, b'\x01'),
            ("FF", 1, b'\xff'),
        ]
        
        for padded_hex, byte_size, expected in test_cases:
            with self.subTest(padded_hex=padded_hex, byte_size=byte_size):
                result = self.processor.convert_to_raw_bytes(padded_hex, byte_size, 'little')
                self.assertEqual(result, expected,
                                f"Little endian conversion failed: expected {expected}, got {result}")

    def test_convert_to_raw_bytes_invalid_endianness(self):
        """Test conversion with invalid endianness"""
        with self.assertRaises(ValueError):
            self.processor.convert_to_raw_bytes("00000012", 4, 'invalid')

    def test_convert_to_raw_bytes_invalid_hex(self):
        """Test conversion with invalid hex string"""
        invalid_hex_strings = ["GG", "12G", "XYZ", "12.34"]
        
        for invalid_hex in invalid_hex_strings:
            with self.subTest(invalid_hex=invalid_hex):
                with self.assertRaises(ValueError):
                    self.processor.convert_to_raw_bytes(invalid_hex, 4, 'big')

    def test_process_input_field_complete_pipeline(self):
        """Test complete input processing pipeline"""
        test_cases = [
            # (input_value, byte_size, endianness, expected_bytes, description)
            ("12", 4, 'big', b'\x00\x00\x00\x12', "4-byte big endian"),
            ("12", 4, 'little', b'\x12\x00\x00\x00', "4-byte little endian"),
            ("123", 8, 'big', b'\x00\x00\x00\x00\x00\x00\x01\x23', "8-byte big endian"),
            ("123", 8, 'little', b'\x23\x01\x00\x00\x00\x00\x00\x00', "8-byte little endian"),
            ("1", 1, 'big', b'\x01', "1-byte big endian"),
            ("1", 1, 'little', b'\x01', "1-byte little endian"),
            ("", 4, 'big', b'\x00\x00\x00\x00', "empty 4-byte"),
            ("", 8, 'little', b'\x00\x00\x00\x00\x00\x00\x00\x00', "empty 8-byte"),
        ]
        
        for input_val, byte_size, endianness, expected, description in test_cases:
            with self.subTest(description=description):
                result = self.processor.process_input_field(input_val, byte_size, endianness)
                self.assertEqual(result, expected,
                                f"Pipeline failed for {description}: expected {expected}, got {result}")

    def test_process_input_field_edge_cases(self):
        """Test edge cases in input processing"""
        test_cases = [
            # Maximum values
            ("FFFFFFFF", 4, 'big', b'\xff\xff\xff\xff', "4-byte max value"),
            ("FFFFFFFFFFFFFFFF", 8, 'big', b'\xff\xff\xff\xff\xff\xff\xff\xff', "8-byte max value"),
            ("FF", 1, 'big', b'\xff', "1-byte max value"),
            
            # Zero values
            ("0", 4, 'big', b'\x00\x00\x00\x00', "4-byte zero"),
            ("0", 8, 'big', b'\x00\x00\x00\x00\x00\x00\x00\x00', "8-byte zero"),
            ("0", 1, 'big', b'\x00', "1-byte zero"),
            
            # Single digits
            ("A", 4, 'big', b'\x00\x00\x00\x0a', "4-byte single digit"),
            ("B", 8, 'big', b'\x00\x00\x00\x00\x00\x00\x00\x0b', "8-byte single digit"),
        ]
        
        for input_val, byte_size, endianness, expected, description in test_cases:
            with self.subTest(description=description):
                result = self.processor.process_input_field(input_val, byte_size, endianness)
                self.assertEqual(result, expected,
                                f"Edge case failed for {description}: expected {expected}, got {result}")

    def test_process_input_field_error_handling(self):
        """Test error handling in input processing"""
        # Test invalid byte size (non-positive)
        with self.assertRaises(ValueError):
            self.processor.process_input_field("12", 0, 'big')
        
        # Test invalid endianness
        with self.assertRaises(ValueError):
            self.processor.process_input_field("12", 4, 'invalid')
        
        # Test invalid hex input
        with self.assertRaises(ValueError):
            self.processor.process_input_field("GG", 4, 'big')

    def test_case_insensitive_hex_input(self):
        """Test that hex input is case insensitive"""
        test_cases = [
            ("ABCDEF", "abcdef"),
            ("abcdef", "abcdef"),
            ("AbCdEf", "abcdef"),
            ("123456789ABCDEF", "123456789abcdef"),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                result = self.processor.pad_hex_input(input_val, 4)
                # Should be normalized to lowercase
                self.assertTrue(result.islower() or result == "00000000",
                               f"Hex input should be normalized to lowercase: {result}")

    def test_data_integrity_through_pipeline(self):
        """Test that data integrity is maintained through the complete pipeline"""
        original_input = "12345678"
        
        # Process through pipeline
        raw_bytes = self.processor.process_input_field(original_input, 4, 'big')
        
        # Convert back to hex for verification
        hex_result = raw_bytes.hex()
        
        # Should match the padded input
        expected_padded = self.processor.pad_hex_input(original_input, 4)
        self.assertEqual(hex_result, expected_padded,
                        f"Data integrity check failed: expected {expected_padded}, got {hex_result}")

    def test_is_supported_field_size(self):
        """Test the is_supported_field_size method"""
        # Test supported sizes
        self.assertTrue(self.processor.is_supported_field_size(1))
        self.assertTrue(self.processor.is_supported_field_size(4))
        self.assertTrue(self.processor.is_supported_field_size(8))
        
        # Test unsupported sizes
        self.assertFalse(self.processor.is_supported_field_size(2))
        self.assertFalse(self.processor.is_supported_field_size(3))
        self.assertFalse(self.processor.is_supported_field_size(16))

if __name__ == '__main__':
    unittest.main() 