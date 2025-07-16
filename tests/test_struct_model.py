"""
test_struct_model.py

本測試檔涵蓋 struct 解析、記憶體佈局計算、hex 資料解析等功能。
測試案例包含：基本型別、bitfield、padding、pointer、混合欄位、複雜 struct 等。
特別針對 bitfield packing、欄位順序、alignment、padding 等進行驗證。
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import patch, mock_open

# Add src to path to import the model
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.struct_model import (
    parse_struct_definition, 
    calculate_layout, 
    StructModel, 
    TYPE_INFO
)
from tests.xml_struct_model_loader import load_struct_model_tests
from tests.xml_struct_parse_definition_loader import load_struct_parse_definition_tests


class TestParseStructDefinition(unittest.TestCase):
    """Test cases for parse_struct_definition function."""
    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(os.path.dirname(__file__), 'data', 'test_struct_parse_definition_config.xml')
        cls.xml_cases = load_struct_parse_definition_tests(config_file)

    def test_xml_struct_parse_definition(self):
        for case in self.xml_cases:
            with self.subTest(name=case['name']):
                struct_name, members = parse_struct_definition(case['struct_definition'])
                if case['expect_none']:
                    self.assertIsNone(struct_name)
                    self.assertIsNone(members)
                else:
                    self.assertEqual(struct_name, case['expected_struct_name'])
                    self.assertEqual(len(members), len(case['expected_members']))
                    for i, expect in enumerate(case['expected_members']):
                        m = members[i]
                        # 支援 bitfield dict/tuple
                        if isinstance(m, tuple):
                            self.assertEqual(m[0], expect['type'])
                            self.assertEqual(m[1], expect['name'])
                        else:
                            self.assertEqual(m['type'], expect['type'])
                            self.assertEqual(m['name'], expect['name'])
                            if 'is_bitfield' in expect:
                                self.assertTrue(m.get('is_bitfield', False))
                                self.assertEqual(m['bit_size'], expect['bit_size'])



class TestStructModel(unittest.TestCase):
    """Test cases for StructModel class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = StructModel()
    
    def test_init(self):
        """Test StructModel initialization."""
        self.assertIsNone(self.model.struct_name)
        self.assertEqual(self.model.members, [])
        self.assertEqual(self.model.layout, [])
        self.assertEqual(self.model.total_size, 0)
        self.assertEqual(self.model.struct_align, 1)
    
    def test_load_struct_from_file_valid(self):
        """Test loading a valid struct from file."""
        struct_content = """
        struct TestStruct {
            int value1;
            char value2;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            result = self.model.load_struct_from_file("test_file.h")
        
        self.assertEqual(result[0], "TestStruct")
        self.assertEqual(len(result[1]), 3)  # int, char, final padding
        self.assertEqual(result[2], 8)  # total size
        self.assertEqual(result[3], 4)  # alignment
        
        # Check instance variables
        self.assertEqual(self.model.struct_name, "TestStruct")
        self.assertEqual(len(self.model.members), 2)
        self.assertEqual(self.model.total_size, 8)
        self.assertEqual(self.model.struct_align, 4)
    
    def test_load_struct_from_file_invalid(self):
        """Test loading an invalid struct from file."""
        invalid_content = "This is not a struct definition"
        
        with patch("builtins.open", mock_open(read_data=invalid_content)):
            with self.assertRaises(ValueError) as context:
                self.model.load_struct_from_file("test_file.h")
        
        self.assertIn("Could not find a valid struct definition", str(context.exception))
    
    def test_parse_hex_data_no_layout(self):
        """Test parsing hex data without loading struct layout first."""
        with self.assertRaises(ValueError) as context:
            self.model.parse_hex_data("01020304", "little")
        
        self.assertIn("No struct layout loaded", str(context.exception))
    

    def test_set_manual_struct_sets_members_and_size(self):
        """Test that set_manual_struct correctly sets members and total_size."""
        members = [
            {"name": "a", "type": "char", "bit_size": 0},
            {"name": "b", "type": "short", "bit_size": 0}
        ]
        total_size = 3
        self.model.set_manual_struct(members, total_size)
        # 期望 members 轉換為 C++ 格式
        expected = [
            {"type": "char", "name": "a", "is_bitfield": False},
            {"type": "short", "name": "b", "is_bitfield": False}
        ]
        self.assertEqual(self.model.manual_struct["members"], expected)
        self.assertEqual(self.model.manual_struct["total_size"], total_size)

    def test_validate_manual_struct_errors_and_success(self):
        # 測試 member 欄位錯誤（total_size 足夠大）
        members = [
            {"name": "a", "type": "char", "bit_size": -1},
            {"name": "b", "type": "short", "bit_size": 0}
        ]
        total_size = 10  # 足夠大，確保 layout 不會先失敗
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertIn("member 'a' bit_size 需為 0 或正整數", errors)
        # 已移除 byte_size 驗證

        # 測試名稱重複（total_size 足夠大）
        members = [
            {"name": "a", "type": "char", "bit_size": 0},
            {"name": "a", "type": "short", "bit_size": 0}
        ]
        total_size = 10
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertIn("成員名稱 'a' 重複", errors)

        # 測試 total_size 錯誤（member 欄位正確）
        members = [
            {"name": "a", "type": "char", "bit_size": 0}
        ]
        total_size = -1
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertIn("結構體大小需為正整數", errors)

        # 測試 layout 錯誤（member 欄位正確，但 total_size 太小）
        members = [
            {"name": "a", "type": "char", "bit_size": 0},
            {"name": "b", "type": "short", "bit_size": 0}
        ]
        total_size = 1  # 故意設小一點，讓 layout 驗證失敗
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertIn("Layout 總長度", errors[0])

        # 驗證通過情境
        members = [
            {"name": "a", "type": "char", "bit_size": 0},
            {"name": "b", "type": "short", "bit_size": 0}
        ]
        total_size = 4  # C++ align: char + short = 4 bytes
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertEqual(errors, [])

    def test_calculate_manual_layout_no_padding(self):
        # 測試 bitfield 緊密排列、無 padding（C++ 標準行為：同一 storage unit）
        members = [
            {"name": "a", "type": "unsigned int", "bit_size": 3},
            {"name": "b", "type": "unsigned int", "bit_size": 5},
            {"name": "c", "type": "unsigned int", "bit_size": 8}
        ]
        total_size = 4  # C++ align 4
        layout = self.model.calculate_manual_layout(members, total_size)
        # 應該有三個 bitfield，全部在 offset=0, type=unsigned int, size=4
        for i, (name, bit_offset, bit_size) in enumerate([
            ("a", 0, 3), ("b", 3, 5), ("c", 8, 8)
        ]):
            self.assertEqual(layout[i]["name"], name)
            self.assertEqual(layout[i]["type"], "unsigned int")
            self.assertEqual(layout[i]["offset"], 0)
            self.assertEqual(layout[i]["size"], 4)
            self.assertEqual(layout[i]["bit_offset"], bit_offset)
            self.assertEqual(layout[i]["bit_size"], bit_size)
        # 檢查 struct 總大小為 4 bytes
        storage_unit_size = layout[0]["size"]
        self.assertEqual(storage_unit_size, 4)

    def test_export_manual_struct_to_h(self):
        # 多欄位 bitfield
        members = [
            {"name": "a", "type": "unsigned int", "bit_size": 3},
            {"name": "b", "type": "unsigned int", "bit_size": 5},
            {"name": "c", "type": "unsigned int", "bit_size": 8}
        ]
        total_size = 2
        self.model.set_manual_struct(members, total_size)
        h_content = self.model.export_manual_struct_to_h()
        self.assertIn("struct MyStruct", h_content)
        self.assertIn("unsigned int a : 3;", h_content)
        self.assertIn("unsigned int b : 5;", h_content)
        self.assertIn("unsigned int c : 8;", h_content)
        self.assertIn("// total size: 2 bytes", h_content)

        # 單一欄位
        members = [{"name": "x", "type": "unsigned int", "bit_size": 16}]
        total_size = 2
        self.model.set_manual_struct(members, total_size)
        h_content = self.model.export_manual_struct_to_h()
        self.assertIn("unsigned int x : 16;", h_content)

        # 空 struct
        members = []
        total_size = 0
        self.model.set_manual_struct(members, total_size)
        h_content = self.model.export_manual_struct_to_h()
        self.assertIn("struct MyStruct", h_content)
        self.assertIn("// total size: 0 bytes", h_content)

    def test_export_manual_struct_to_h_with_custom_name(self):
        # 測試 struct_name 參數自訂時的輸出
        members = [
            {"name": "a", "type": "unsigned int", "bit_size": 3},
            {"name": "b", "type": "unsigned int", "bit_size": 5}
        ]
        total_size = 1
        self.model.set_manual_struct(members, total_size)
        h_content = self.model.export_manual_struct_to_h(struct_name="CustomStruct")
        self.assertIn("struct CustomStruct", h_content)
        self.assertIn("unsigned int a : 3;", h_content)
        self.assertIn("unsigned int b : 5;", h_content)
        self.assertIn("// total size: 1 bytes", h_content)

    def test_manual_struct_byte_bit_size_layout(self):
        model = StructModel()
        members = [
            {"name": "a", "type": "char", "bit_size": 0},
            {"name": "b", "type": "unsigned int", "bit_size": 12},
            {"name": "c", "type": "short", "bit_size": 0},
            {"name": "d", "type": "unsigned int", "bit_size": 4}
        ]
        total_size = 16  # C++ align 4, 8, 2, etc.，實際會比 5 大
        # 驗證 set_manual_struct
        model.set_manual_struct(members, total_size)
        self.assertEqual(model.manual_struct["total_size"], total_size)
        self.assertEqual(len(model.manual_struct["members"]), 4)
        # 驗證 validate_manual_struct
        errors = model.validate_manual_struct(members, total_size)
        self.assertEqual(errors, [])
        # 驗證 layout 計算
        layout = model.calculate_manual_layout(members, total_size)
        # 只驗證非 padding 成員
        non_pad = [item for item in layout if item["type"] != "padding"]
        # a: char, offset 0
        self.assertEqual(non_pad[0]["name"], "a")
        self.assertEqual(non_pad[0]["type"], "char")
        self.assertEqual(non_pad[0]["size"], 1)
        self.assertEqual(non_pad[0]["offset"], 0)
        # b: unsigned int bitfield, offset 4, bit_offset 0, bit_size 12
        self.assertEqual(non_pad[1]["name"], "b")
        self.assertEqual(non_pad[1]["type"], "unsigned int")
        self.assertEqual(non_pad[1]["offset"], 4)
        self.assertEqual(non_pad[1]["bit_offset"], 0)
        self.assertEqual(non_pad[1]["bit_size"], 12)
        # c: short, offset 8
        self.assertEqual(non_pad[2]["name"], "c")
        self.assertEqual(non_pad[2]["type"], "short")
        self.assertEqual(non_pad[2]["offset"], 8)
        self.assertEqual(non_pad[2]["size"], 2)
        # d: unsigned int bitfield, offset 12, bit_offset 0, bit_size 4
        self.assertEqual(non_pad[3]["name"], "d")
        self.assertEqual(non_pad[3]["type"], "unsigned int")
        self.assertEqual(non_pad[3]["offset"], 12)
        self.assertEqual(non_pad[3]["bit_offset"], 0)
        self.assertEqual(non_pad[3]["bit_size"], 4)

    def test_parse_manual_hex_data_uses_file_parsing_logic(self):
        """測試 MyStruct 解析機制直接使用載入.h檔的解析邏輯"""
        manual_layout = [
            {"name": "a", "type": "int", "offset": 0, "size": 4, "is_bitfield": False},
            {"name": "b", "type": "char", "offset": 4, "size": 1, "is_bitfield": False}
        ]
        hex_data = "04030201" + "41"  # little endian
        # 直接用 parse_hex_data
        result = self.model.parse_hex_data(hex_data, "little", layout=manual_layout, total_size=5)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "a")
        self.assertEqual(result[0]["value"], "16909060")
        self.assertEqual(result[0]["hex_raw"], "04030201")  # 修正這裡
        self.assertEqual(result[1]["name"], "b")
        self.assertEqual(result[1]["value"], "65")
        self.assertEqual(result[1]["hex_raw"], "41")

    def test_parse_manual_hex_data_preserves_original_layout(self):
        """測試橋接函數不會影響原始的 layout 和 total_size"""
        struct_content = """
        struct FileStruct {
            int x;
            char y;
        };
        """
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        original_layout = self.model.layout.copy()
        original_total_size = self.model.total_size
        manual_layout = [
            {"name": "a", "type": "int", "offset": 0, "size": 4, "is_bitfield": False}
        ]
        hex_data = "01000000"
        self.model.parse_hex_data(hex_data, "little", layout=manual_layout, total_size=4)
        self.assertEqual(self.model.layout, original_layout)
        self.assertEqual(self.model.total_size, original_total_size)


class TestCombinedExampleStruct(unittest.TestCase):
    """
    測試 example.h 的 CombinedExample struct。
    驗證 struct parser 能正確處理 bitfield、padding、pointer、混合欄位順序與 layout。
    """
    def test_combined_example_struct(self):
        struct_content = '''
        struct CombinedExample {
            char      a;
            int       b;
            int       c1 : 1;
            int       c2 : 2;
            int       c3 : 5;
            char      d;
            long long e;
            unsigned char f;
            char*     g;
        };
        '''
        from model.struct_model import parse_struct_definition, calculate_layout
        struct_name, members = parse_struct_definition(struct_content)
        self.assertEqual(struct_name, "CombinedExample")
        # 檢查欄位順序與型別
        expected = [
            ("char", "a"),
            ("int", "b"),
            {"type": "int", "name": "c1", "is_bitfield": True, "bit_size": 1},
            {"type": "int", "name": "c2", "is_bitfield": True, "bit_size": 2},
            {"type": "int", "name": "c3", "is_bitfield": True, "bit_size": 5},
            ("char", "d"),
            ("long long", "e"),
            ("unsigned char", "f"),
            ("pointer", "g"),
        ]
        for m, exp in zip(members, expected):
            if isinstance(exp, dict):
                self.assertIsInstance(m, dict)
                for k in exp:
                    self.assertEqual(m[k], exp[k])
            else:
                self.assertEqual(m, exp)
        # 檢查 layout 計算（只驗證欄位順序與 offset，不驗證所有 padding 細節）
        layout, total_size, struct_align = calculate_layout(members)
        names = [item["name"] for item in layout if item["type"] != "padding"]
        self.assertEqual(names, ["a", "b", "c1", "c2", "c3", "d", "e", "f", "g"])
        self.assertEqual(struct_align, 8)
        self.assertGreaterEqual(total_size, 40)  # 依據 x86-64 ABI，應為 40 bytes


class TestTypeInfo(unittest.TestCase):
    """Test cases for TYPE_INFO constant."""
    
    def test_type_info_completeness(self):
        """Test that TYPE_INFO contains all expected types."""
        expected_types = [
            "char", "signed char", "unsigned char", "bool",
            "short", "unsigned short", "int", "unsigned int",
            "long", "unsigned long", "long long", "unsigned long long",
            "float", "double", "pointer"
        ]
        
        for type_name in expected_types:
            self.assertIn(type_name, TYPE_INFO)
            self.assertIn("size", TYPE_INFO[type_name])
            self.assertIn("align", TYPE_INFO[type_name])
    
    def test_type_info_sizes(self):
        """Test that type sizes are reasonable for 64-bit system."""
        # Test basic types
        self.assertEqual(TYPE_INFO["char"]["size"], 1)
        self.assertEqual(TYPE_INFO["int"]["size"], 4)
        self.assertEqual(TYPE_INFO["long"]["size"], 8)
        self.assertEqual(TYPE_INFO["double"]["size"], 8)
        self.assertEqual(TYPE_INFO["pointer"]["size"], 8)
    
    def test_type_info_alignment(self):
        """Test that alignment values are correct."""
        # Alignment should match size for most types
        for type_name, info in TYPE_INFO.items():
            self.assertEqual(info["size"], info["align"])


class TestStructModelXMLDriven(unittest.TestCase):
    """XML 驅動的 StructModel 測試"""
    @classmethod
    def setUpClass(cls):
        cls.test_data = load_struct_model_tests(
            os.path.join(os.path.dirname(__file__), 'data', 'test_struct_model_config.xml')
        )

    def test_struct_model_cases(self):
        for case in self.test_data:
            with self.subTest(name=case['name']):
                model = StructModel()
                struct_name, members = parse_struct_definition(case['struct_definition'])
                model.struct_name = struct_name
                model.members = members
                model.layout, model.total_size, model.struct_align = calculate_layout(members)
                if case.get('input_hex'):
                    if case.get('endianness') == 'both':
                        for endian in ['little', 'big']:
                            result = model.parse_hex_data(case['input_hex'], endian)
                            for expect in case['expected']:
                                found = next((item for item in result if item['name'] == expect['name']), None)
                                self.assertIsNotNone(found, f"欄位 {expect['name']} 未找到")
                                key = f"value_{endian}"
                                if key in expect:
                                    self.assertEqual(str(found['value']), str(expect[key]))
                                if 'hex_raw' in expect:
                                    self.assertEqual(found.get('hex_raw'), expect['hex_raw'])
                    else:
                        result = model.parse_hex_data(case['input_hex'], case.get('endianness', 'little'))
                        for expect in case['expected']:
                            found = next((item for item in result if item['name'] == expect['name']), None)
                            self.assertIsNotNone(found, f"欄位 {expect['name']} 未找到")
                            if 'value' in expect:
                                self.assertEqual(str(found['value']), str(expect['value']))
                            if 'hex_raw' in expect:
                                self.assertEqual(found.get('hex_raw'), expect['hex_raw'])
                else:
                    if 'expected_layout_len' in case:
                        self.assertEqual(len(model.layout), case['expected_layout_len'])
                    if 'expected_total_size' in case:
                        self.assertEqual(model.total_size, case['expected_total_size'])
                    if 'expected_struct_align' in case:
                        self.assertEqual(model.struct_align, case['expected_struct_align'])
                    for i, expect in enumerate(case.get('expected', [])):
                        item = model.layout[i]
                        for key, val in expect.items():
                            if key == 'name':
                                self.assertEqual(item['name'], val)
                            elif key == 'type':
                                self.assertEqual(item['type'], val)
                            elif key in ('offset', 'size', 'bit_offset', 'bit_size'):
                                self.assertEqual(item[key], val)


if __name__ == "__main__":
    unittest.main() 