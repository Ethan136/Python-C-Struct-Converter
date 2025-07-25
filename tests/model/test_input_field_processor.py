import unittest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.input_field_processor import InputFieldProcessor
from tests.data_driven.xml_input_field_processor_loader import load_input_field_processor_tests, load_input_field_processor_error_tests

class TestInputFieldProcessor(unittest.TestCase):
    """Test cases for InputFieldProcessor module"""
    @classmethod
    def setUpClass(cls):
        # 載入異常測資
        error_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_input_field_processor_error_config.xml')
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
        for case in load_input_field_processor_tests(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_input_field_processor_config.xml')
        ):
            extra = case.get('extra_tests', {})
            for sub in extra.get('is_supported_field_size', []):
                with self.subTest(size=sub['size']):
                    result = self.processor.is_supported_field_size(sub['size'])
                    self.assertEqual(result, sub['expected'])

class TestInputFieldProcessorXMLDriven(unittest.TestCase):
    """XML 驅動的 InputFieldProcessor 測試"""
    @classmethod
    def setUpClass(cls):
        cls.processor = InputFieldProcessor()
        cls.test_data = load_input_field_processor_tests(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_input_field_processor_config.xml')
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

    def test_pad_hex_input(self):
        for case in self.test_data:
            extra = case.get('extra_tests', {})
            for subcase in extra.get('pad_hex_input', []):
                with self.subTest(input=subcase['input'], byte_size=subcase['byte_size']):
                    result = self.processor.pad_hex_input(subcase['input'], subcase['byte_size'])
                    self.assertEqual(result, subcase['expected'].lower())

    def test_convert_to_raw_bytes(self):
        for case in self.test_data:
            extra = case.get('extra_tests', {})
            for subcase in extra.get('convert_to_raw_bytes', []):
                with self.subTest(padded_hex=subcase['padded_hex'], byte_size=subcase['byte_size'], endianness=subcase['endianness']):
                    result = self.processor.convert_to_raw_bytes(subcase['padded_hex'], subcase['byte_size'], subcase['endianness'])
                    self.assertEqual(result.hex(), subcase['expected'].lower())

if __name__ == '__main__':
    unittest.main() 