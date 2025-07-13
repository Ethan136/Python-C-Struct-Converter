import unittest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.input_field_processor import InputFieldProcessor
from tests.xml_input_field_processor_loader import load_input_field_processor_tests

class TestInputFieldProcessor(unittest.TestCase):
    """Test cases for InputFieldProcessor module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = InputFieldProcessor()

    # 僅保留 process_input_field 的 hardcode 測試（如有），其餘移除
    # ...（如無則略）...

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

class TestInputFieldProcessorXMLDriven(unittest.TestCase):
    """XML 驅動的 InputFieldProcessor 測試"""
    @classmethod
    def setUpClass(cls):
        cls.processor = InputFieldProcessor()
        cls.test_data = load_input_field_processor_tests(
            os.path.join(os.path.dirname(__file__), 'data', 'test_input_field_processor_config.xml')
        )

    def test_process_input_field(self):
        for case in self.test_data['process_input_field']:
            with self.subTest(input=case['input'], byte_size=case['byte_size'], endianness=case['endianness']):
                result = self.processor.process_input_field(case['input'], case['byte_size'], case['endianness'])
                self.assertEqual(result.hex(), case['expected'].lower())

    def test_process_input_field_edge_cases(self):
        for case in self.test_data['process_input_field_edge_cases']:
            with self.subTest(input=case['input'], byte_size=case['byte_size'], endianness=case['endianness']):
                result = self.processor.process_input_field(case['input'], case['byte_size'], case['endianness'])
                self.assertEqual(result.hex(), case['expected'].lower())

if __name__ == '__main__':
    unittest.main() 