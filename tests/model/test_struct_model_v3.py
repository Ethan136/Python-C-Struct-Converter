import unittest
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.struct_model import StructModel
from tests.data_driven.xml_struct_model_v3_loader import load_struct_model_v3_tests

class TestStructModelV3(unittest.TestCase):
    """測試 V3 版本的 StructModel 新功能"""
    
    def setUp(self):
        self.model = StructModel()
    
    def test_convert_to_cpp_members_with_type(self):
        """測試新的型別轉換方法 - 支援明確型別"""
        members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "unsigned int", "bit_size": 4}
        ]
        result = self.model._convert_to_cpp_members(members)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "int")
        self.assertEqual(result[0]["name"], "a")
        self.assertFalse(result[0]["is_bitfield"])
        self.assertEqual(result[1]["type"], "unsigned int")
        self.assertEqual(result[1]["name"], "b")
        self.assertTrue(result[1]["is_bitfield"])
        self.assertEqual(result[1]["bit_size"], 4)
    
    def test_convert_to_cpp_members_skip_invalid_type(self):
        """測試跳過無效型別"""
        members = [
            {"name": "a", "type": "invalid_type", "bit_size": 0},
            {"name": "b", "type": "int", "bit_size": 0}
        ]
        result = self.model._convert_to_cpp_members(members)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "int")
        self.assertEqual(result[0]["name"], "b")
    
    def test_convert_to_cpp_members_empty_type(self):
        """測試空型別的處理"""
        members = [
            {"name": "a", "type": "", "bit_size": 0},
            {"name": "b", "type": "int", "bit_size": 0}
        ]
        result = self.model._convert_to_cpp_members(members)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "int")
        self.assertEqual(result[0]["name"], "b")
    
    def test_calculate_used_bits_skip_invalid_type(self):
        """測試計算時跳過無效型別"""
        members = [
            {"name": "a", "type": "int", "bit_size": 0},        # 32 bits
            {"name": "b", "type": "invalid_type", "bit_size": 0}, # 跳過
            {"name": "c", "type": "char", "bit_size": 0}        # 8 bits
        ]
        used_bits = self.model.calculate_used_bits(members)
        self.assertEqual(used_bits, 32 + 8)  # 40 bits
    
    # 已移除 test_backward_compatibility_legacy_format
    # 已移除 test_backward_compatibility_legacy_bitfield
    # 已移除 test_backward_compatibility_legacy_byte_sizes
    
    def test_validate_manual_struct_invalid_type(self):
        """測試無效型別的驗證"""
        members = [
            {"name": "a", "type": "invalid_type", "bit_size": 0}
        ]
        total_size = 4
        
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("不支援的型別" in error for error in errors))
    
    def test_validate_manual_struct_bitfield_type_restriction(self):
        """測試 bitfield 型別限制"""
        members = [
            {"name": "a", "type": "float", "bit_size": 4}  # float 不能用於 bitfield
        ]
        total_size = 4
        
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("bitfield 只支援" in error for error in errors))
    
    def test_validate_manual_struct_duplicate_names(self):
        """測試重複名稱驗證"""
        members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "a", "type": "char", "bit_size": 0}  # 重複名稱
        ]
        total_size = 8
        
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("重複" in error for error in errors))
    
    def test_validate_manual_struct_invalid_bit_size(self):
        """測試無效 bit_size 驗證"""
        members = [
            {"name": "a", "type": "int", "bit_size": -1}  # 負數
        ]
        total_size = 4
        
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("bit_size 需為 0 或正整數" in error for error in errors))


class TestStructModelV3XMLDriven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_model_v3_config.xml')
        cls.cases = load_struct_model_v3_tests(config_file)
        cls.model = StructModel()

    def test_struct_model_v3_cases(self):
        for case in self.cases:
            with self.subTest(name=case['name']):
                members = case['members']
                total_size = case['total_size']
                errors = self.model.validate_manual_struct(members, total_size)
                self.assertEqual(len(errors), 0)
                if case['expected_bits'] is not None:
                    used_bits = self.model.calculate_used_bits(members)
                    self.assertEqual(used_bits, case['expected_bits'])
                if case['expected_export_contains']:
                    self.model.manual_struct = {'members': members, 'total_size': total_size}
                    h = self.model.export_manual_struct_to_h('TestStruct')
                    for line in case['expected_export_contains']:
                        self.assertIn(line, h)
    
if __name__ == "__main__":
    unittest.main() 