import unittest
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model.struct_model import StructModel

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
    
    def test_calculate_used_bits_regular_types(self):
        """測試使用空間計算 - 普通型別"""
        members = [
            {"name": "a", "type": "char", "bit_size": 0},      # 1 byte = 8 bits
            {"name": "b", "type": "int", "bit_size": 0},       # 4 bytes = 32 bits
            {"name": "c", "type": "long long", "bit_size": 0}  # 8 bytes = 64 bits
        ]
        used_bits = self.model.calculate_used_bits(members)
        self.assertEqual(used_bits, 8 + 32 + 64)  # 104 bits
    
    def test_calculate_used_bits_bitfields(self):
        """測試使用空間計算 - bitfield"""
        members = [
            {"name": "a", "type": "unsigned int", "bit_size": 4},  # 4 bits
            {"name": "b", "type": "unsigned int", "bit_size": 8},  # 8 bits
            {"name": "c", "type": "int", "bit_size": 0}            # 4 bytes = 32 bits
        ]
        used_bits = self.model.calculate_used_bits(members)
        self.assertEqual(used_bits, 4 + 8 + 32)  # 44 bits
    
    def test_calculate_used_bits_mixed_types(self):
        """測試使用空間計算 - 混合型別"""
        members = [
            {"name": "a", "type": "char", "bit_size": 0},           # 8 bits
            {"name": "b", "type": "unsigned int", "bit_size": 12},  # 12 bits
            {"name": "c", "type": "double", "bit_size": 0}          # 64 bits
        ]
        used_bits = self.model.calculate_used_bits(members)
        self.assertEqual(used_bits, 8 + 12 + 64)  # 84 bits
    
    def test_calculate_used_bits_skip_invalid_type(self):
        """測試計算時跳過無效型別"""
        members = [
            {"name": "a", "type": "int", "bit_size": 0},        # 32 bits
            {"name": "b", "type": "invalid_type", "bit_size": 0}, # 跳過
            {"name": "c", "type": "char", "bit_size": 0}        # 8 bits
        ]
        used_bits = self.model.calculate_used_bits(members)
        self.assertEqual(used_bits, 32 + 8)  # 40 bits
    
    def test_backward_compatibility_legacy_format(self):
        """測試向後相容性 - 舊格式（包含 byte_size）"""
        members = [
            {"name": "a", "byte_size": 4, "bit_size": 0},  # 舊格式
            {"name": "b", "type": "int", "bit_size": 0}    # 新格式
        ]
        result = self.model._convert_to_cpp_members(members)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "int")
        self.assertEqual(result[1]["type"], "int")
    
    def test_backward_compatibility_legacy_bitfield(self):
        """測試向後相容性 - 舊格式 bitfield"""
        members = [
            {"name": "a", "byte_size": 0, "bit_size": 4},  # 舊格式 bitfield
            {"name": "b", "type": "unsigned int", "bit_size": 8}  # 新格式 bitfield
        ]
        result = self.model._convert_to_cpp_members(members)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "unsigned int")
        self.assertTrue(result[0]["is_bitfield"])
        self.assertEqual(result[0]["bit_size"], 4)
        self.assertEqual(result[1]["type"], "unsigned int")
        self.assertTrue(result[1]["is_bitfield"])
        self.assertEqual(result[1]["bit_size"], 8)
    
    def test_backward_compatibility_legacy_byte_sizes(self):
        """測試向後相容性 - 不同 byte_size 的推斷"""
        test_cases = [
            (1, "char"),
            (2, "short"),
            (4, "int"),
            (8, "long long"),
            (16, "unsigned char")  # 其他大小推斷為 unsigned char
        ]
        
        for byte_size, expected_type in test_cases:
            with self.subTest(byte_size=byte_size):
                members = [{"name": "test", "byte_size": byte_size, "bit_size": 0}]
                result = self.model._convert_to_cpp_members(members)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["type"], expected_type)
    
    def test_validate_manual_struct_v3_format(self):
        """測試 V3 格式的驗證"""
        members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "unsigned int", "bit_size": 4}
        ]
        total_size = 8  # 4 bytes (int) + 4 bits = 4.5 bytes, 向上取整為 8 bytes
        
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertEqual(len(errors), 0)  # 應該沒有錯誤
    
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
    
    def test_export_manual_struct_to_h_v3_format(self):
        """測試 V3 格式的匯出功能"""
        members = [
            {"name": "user_id", "type": "unsigned long long", "bit_size": 0},
            {"name": "status", "type": "unsigned int", "bit_size": 4},
            {"name": "name", "type": "char", "bit_size": 0}
        ]
        total_size = 16
        
        # 設定 manual_struct
        self.model.manual_struct = {"members": members, "total_size": total_size}
        
        result = self.model.export_manual_struct_to_h("TestStruct")
        
        # 檢查匯出內容
        self.assertIn("struct TestStruct", result)
        self.assertIn("unsigned long long user_id;", result)
        self.assertIn("unsigned int status : 4;", result)
        self.assertIn("char name;", result)
        self.assertIn("// total size: 16 bytes", result)

if __name__ == "__main__":
    unittest.main() 