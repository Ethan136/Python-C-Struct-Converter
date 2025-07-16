import unittest
import os
from src.model.struct_model import StructModel
from tests.data_driven.xml_manual_struct_loader import load_manual_struct_tests

class TestManualStructIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'manual_struct_test_config.xml')
        cls.xml_cases = load_manual_struct_tests(config_file)

    def setUp(self):
        self.model = StructModel()

    def test_manual_struct_cases(self):
        for case in self.xml_cases:
            with self.subTest(name=case['name']):
                members = case['members']
                total_size = case['total_size']
                # 設定 struct
                self.model.set_manual_struct(members, total_size)
                # 設定 struct_name
                if case.get('struct_name'):
                    self.model.struct_name = case['struct_name']
                # 驗證錯誤
                errors = self.model.validate_manual_struct(members, total_size)
                if case['expected_errors']:
                    for key in case['expected_errors']:
                        self.assertTrue(any(key in err for err in errors), f"'{key}' not found in errors: {errors}")
                else:
                    self.assertEqual(errors, case['expected_errors'])
                # 匯出 .h 檔內容
                h_content = self.model.export_manual_struct_to_h(case.get('struct_name'))
                for line in case.get('expected_export_contains', []):
                    self.assertIn(line, h_content)

if __name__ == "__main__":
    unittest.main() 