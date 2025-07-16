import unittest
import tempfile
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.struct_model import StructModel
from tests.xml_struct_model_loader import load_struct_model_tests


class TestStructModel(unittest.TestCase):
    """Behaviour tests not covered by data-driven cases."""

    def setUp(self):
        self.model = StructModel()

    def test_init(self):
        self.assertIsNone(self.model.struct_name)
        self.assertEqual(self.model.members, [])
        self.assertEqual(self.model.layout, [])
        self.assertEqual(self.model.total_size, 0)
        self.assertEqual(self.model.struct_align, 1)
        self.assertIsNotNone(self.model.input_processor)

    def test_parse_hex_data_no_layout(self):
        with self.assertRaises(ValueError):
            self.model.parse_hex_data("1234", 'little')

    def test_hex_raw_formatting_and_padding(self):
        content = """
        struct HexStruct {
            char a;
            int b;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        try:
            self.model.load_struct_from_file(file_path)
            parsed_values = self.model.parse_hex_data("12", 'little')
            for item in parsed_values:
                if item["name"] != "(padding)":
                    hex_raw = item["hex_raw"]
                    self.assertEqual(len(hex_raw) % 2, 0)
                    int(hex_raw, 16)
                    layout_item = next((l for l in self.model.layout if l["name"] == item["name"]), None)
                    if layout_item:
                        expected_size = layout_item["size"] * 2
                        self.assertEqual(len(hex_raw), expected_size)
        finally:
            os.unlink(file_path)


class TestStructModelIntegrationXMLDriven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(
            os.path.dirname(__file__),
            'data',
            'test_struct_model_integration_config.xml',
        )
        cls.cases = load_struct_model_tests(config_file)

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
