import unittest
import tempfile
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.struct_model import StructModel
from tests.data_driven.xml_struct_model_loader import load_struct_model_tests


class TestStructModel(unittest.TestCase):
    """Behaviour tests loaded from XML."""

    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'test_struct_model_integration_config.xml',
        )
        cls.cases = [c for c in load_struct_model_tests(config_file) if c.get('type') in ('init', 'no_layout', 'hex_raw_formatting')]

    def test_behavior_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                if case['type'] == 'init':
                    model = StructModel()
                    self.assertIsNone(model.struct_name)
                    self.assertEqual(model.members, [])
                    self.assertEqual(model.layout, [])
                    self.assertEqual(model.total_size, 0)
                    self.assertEqual(model.struct_align, 1)
                    self.assertIsNotNone(model.input_processor)
                elif case['type'] == 'no_layout':
                    model = StructModel()
                    with self.assertRaises(eval(case['expected_exception'])):
                        model.parse_hex_data(case['input_hex'], case.get('endianness', 'little'))
                elif case['type'] == 'hex_raw_formatting':
                    model = StructModel()
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
                        f.write(case['struct_definition'])
                        file_path = f.name
                    try:
                        model.load_struct_from_file(file_path)
                        parsed_values = model.parse_hex_data(case['input_hex'], case.get('endianness', 'little'))
                        for item in parsed_values:
                            if item['name'] != '(padding)':
                                hex_raw = item['hex_raw']
                                self.assertEqual(len(hex_raw) % 2, 0)
                                layout_item = next((l for l in model.layout if l['name'] == item['name']), None)
                                if layout_item:
                                    expected_size = layout_item['size'] * 2
                                    self.assertEqual(len(hex_raw), expected_size)
                    finally:
                        os.unlink(file_path)


class TestStructModelIntegrationXMLDriven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'test_struct_model_integration_config.xml',
        )
        cls.cases = [c for c in load_struct_model_tests(config_file) if not c.get('type')]

    def test_integration_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                model = StructModel()
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
                    f.write(case['struct_definition'])
                    file_path = f.name
                try:
                    if 'expected_exception' in case:
                        with self.assertRaises(eval(case['expected_exception'])):
                            model.load_struct_from_file(file_path)
                        continue
                    struct_name, layout, total_size, struct_align = model.load_struct_from_file(file_path)
                    if 'expected_total_size' in case:
                        self.assertEqual(total_size, case['expected_total_size'])
                    if 'expected_struct_align' in case:
                        self.assertEqual(struct_align, case['expected_struct_align'])
                    if 'expected_layout_len' in case:
                        self.assertEqual(len(layout), case['expected_layout_len'])

                    if case.get('input_hex'):
                        endian = case.get('endianness', 'little')
                        result = model.parse_hex_data(case['input_hex'], endian)
                        for expect in case['expected']:
                            found = next((item for item in result if item['name'] == expect['name']), None)
                            self.assertIsNotNone(found, f"Field {expect['name']} not found")
                            if 'value' in expect:
                                self.assertEqual(str(found['value']), str(expect['value']))
                            if 'hex_raw' in expect:
                                self.assertEqual(found['hex_raw'], expect['hex_raw'])
                finally:
                    os.unlink(file_path)


if __name__ == '__main__':
    unittest.main()
