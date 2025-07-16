import unittest
import pytest
import os
from model.struct_parser import parse_member_line, _extract_struct_body
from tests.xml_struct_parser_utils_loader import load_struct_parser_utils_tests

class TestParseMemberLine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = os.path.join(
            os.path.dirname(__file__), 'data', 'test_struct_parser_utils_config.xml'
        )
        cls.member_cases, cls.body_cases = load_struct_parser_utils_tests(config_path)

    def test_member_cases(self):
        for case in self.member_cases:
            with self.subTest(name=case['name']):
                if case['xfail']:
                    pytest.xfail('expected failure')
                result = parse_member_line(case['line'])
                if case['return_type'] == 'tuple':
                    self.assertEqual(result, (case['expected']['type'], case['expected']['name']))
                else:
                    self.assertIsInstance(result, dict)
                    for key, val in case['expected'].items():
                        if key == 'array_dims':
                            self.assertEqual(result.get(key), val)
                        else:
                            self.assertEqual(result.get(key), val)


class TestExtractStructBody(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = os.path.join(
            os.path.dirname(__file__), 'data', 'test_struct_parser_utils_config.xml'
        )
        cls.member_cases, cls.body_cases = load_struct_parser_utils_tests(config_path)

    def test_extract_cases(self):
        for case in self.body_cases:
            with self.subTest(name=case['name']):
                name, body = _extract_struct_body(case['content'])
                self.assertEqual(name, case['expected_name'])
                for line in case['expected_contains']:
                    self.assertIn(line, body)

if __name__ == '__main__':
    unittest.main()
