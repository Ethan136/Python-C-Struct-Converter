import unittest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.input_field_processor import InputFieldProcessor
from tests.xml_input_field_processor_loader import load_input_field_processor_tests, load_input_field_processor_error_tests

class TestInputFieldProcessor(unittest.TestCase):
    """Test cases for InputFieldProcessor module"""
    @classmethod
    def setUpClass(cls):
        # 載入異常測資
        error_file_path = os.path.join(os.path.dirname(__file__), 'data', 'test_input_field_processor_error_config.xml')
        cls.error_cases = load_input_field_processor_error_tests(error_file_path)

    def setUp(self):
        """Set up test fixtures"""
        self.processor = InputFieldProcessor()

    # 僅保留 process_input_field 的 hardcode 測試（如有），其餘移除
    # ...（如無則略）...

    # ===================== XML 驅動異常測試 =====================
    def test_xml_input_field_processor_errors(self):
        for case in self.error_cases:
            with self.subTest(name=case['name']):
                error_type = eval(case['error_type'])
                with self.assertRaises(error_type):
                    self.processor.process_input_field(case['input'], case['byte_size'], case['endianness'])

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
        for case in self.test_data:
            extra = case.get('extra_tests', {})
            for subcase in extra.get('process_input_field', []):
                with self.subTest(input=subcase['input'], byte_size=subcase['byte_size'], endianness=subcase['endianness']):
                    result = self.processor.process_input_field(subcase['input'], subcase['byte_size'], subcase['endianness'])
                    self.assertEqual(result.hex(), subcase['expected'].lower())

    def test_process_input_field_edge_cases(self):
        for case in self.test_data:
            extra = case.get('extra_tests', {})
            for subcase in extra.get('process_input_field_edge_cases', []):
                with self.subTest(input=subcase['input'], byte_size=subcase['byte_size'], endianness=subcase['endianness']):
                    result = self.processor.process_input_field(subcase['input'], subcase['byte_size'], subcase['endianness'])
                    self.assertEqual(result.hex(), subcase['expected'].lower())

if __name__ == '__main__':
    unittest.main() 