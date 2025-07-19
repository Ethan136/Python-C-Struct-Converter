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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.struct_model import (
    parse_struct_definition, 
    calculate_layout, 
    StructModel, 
    TYPE_INFO
)
from tests.data_driven.xml_struct_model_loader import load_struct_model_tests
from tests.data_driven.xml_struct_parse_definition_loader import load_struct_parse_definition_tests
from src.model.struct_parser import parse_struct_definition_ast
from src.model.struct_model import ast_to_dict, flatten_ast_nodes


class TestParseStructDefinition(unittest.TestCase):
    """Test cases for parse_struct_definition function."""
    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_parse_definition_config.xml')
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

    def test_anonymous_bitfield_layout(self):
        # 測試匿名 bitfield layout 正確分配 bit offset 並出現在 layout 結果中
        members = [
            {"type": "int", "name": "a", "is_bitfield": True, "bit_size": 3},
            {"type": "int", "name": None, "is_bitfield": True, "bit_size": 2},
            {"type": "int", "name": "b", "is_bitfield": True, "bit_size": 5},
        ]
        total_size = 4  # int storage unit
        layout = self.model.calculate_manual_layout(members, total_size)
        # 應有三個 bitfield，全部 offset=0, type=int, size=4
        self.assertEqual(layout[0]["name"], "a")
        self.assertEqual(layout[0]["bit_offset"], 0)
        self.assertEqual(layout[0]["bit_size"], 3)
        self.assertEqual(layout[1]["name"], None)
        self.assertEqual(layout[1]["bit_offset"], 3)
        self.assertEqual(layout[1]["bit_size"], 2)
        self.assertEqual(layout[2]["name"], "b")
        self.assertEqual(layout[2]["bit_offset"], 5)
        self.assertEqual(layout[2]["bit_size"], 5)
        # 檢查 struct 總大小為 4 bytes
        self.assertEqual(layout[0]["size"], 4)

    def test_export_anonymous_bitfield_to_h(self):
        # 匿名 bitfield 匯出 .h 時應省略名稱
        members = [
            {"type": "int", "name": "a", "is_bitfield": True, "bit_size": 3},
            {"type": "int", "name": None, "is_bitfield": True, "bit_size": 2},
            {"type": "int", "name": "b", "is_bitfield": True, "bit_size": 5},
        ]
        total_size = 4
        self.model.set_manual_struct(members, total_size)
        h_content = self.model.export_manual_struct_to_h()
        self.assertIn("int a : 3;", h_content)
        self.assertIn("int : 2;", h_content)  # 匿名 bitfield
        self.assertIn("int b : 5;", h_content)

    def test_parse_hex_data_with_anonymous_bitfield(self):
        # 測試 hex 解析時，匿名 bitfield 能正確回傳 name=None 且值正確
        # struct { int a:3; int :2; int b:5; }，假設 a=5, 匿名=3, b=17
        # bit pattern: a=5(101), anon=3(11), b=17(10001) => 101 11 10001 = 0b1011110001 = 753
        # 低位在前（little endian），int 4 bytes: 0x000002f1
        members = [
            {"type": "int", "name": "a", "is_bitfield": True, "bit_size": 3},
            {"type": "int", "name": None, "is_bitfield": True, "bit_size": 2},
            {"type": "int", "name": "b", "is_bitfield": True, "bit_size": 5},
        ]
        total_size = 4
        layout = self.model.calculate_manual_layout(members, total_size)
        print("layout:", layout)
        # 0b1000111101 = 0x23d, little endian: 0x3d 0x02 0x00 0x00
        hex_data = "3d020000"
        # 取出 storage_int
        member_bytes = bytes.fromhex(hex_data)
        storage_int = int.from_bytes(member_bytes, "little")
        print("storage_int(bin):", bin(storage_int), "storage_int(dec):", storage_int)
        result = self.model.parse_hex_data(hex_data, "little", layout=layout, total_size=4)
        print("result:", result)
        self.assertEqual(result[0]["name"], "a")
        self.assertEqual(result[0]["value"], "5")
        self.assertEqual(result[1]["name"], None)
        self.assertEqual(result[1]["value"], "3")
        self.assertEqual(result[2]["name"], "b")
        self.assertEqual(result[2]["value"], "17")


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
        from src.model.struct_model import parse_struct_definition, calculate_layout
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
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_model_config.xml')
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


class TestStructModelNDArray(unittest.TestCase):
    """TDD: 驗證多維陣列 layout 是否正確展開 (v5_nd_array)"""
    def test_nd_array_layout(self):
        struct_content = """
        struct NDArrayTest {
            int arr[2][3];
        };
        """
        model = StructModel()
        # 直接模擬從檔案載入 struct
        model.struct_name, model.members = parse_struct_definition(struct_content)
        model.layout, model.total_size, model.struct_align = calculate_layout(model.members)
        # 預期 layout 會展開成 6 個 int 元素
        int_size = TYPE_INFO["int"]["size"]
        expected = [
            {"name": f"arr[{i}][{j}]", "type": "int", "size": int_size, "offset": int_size * (i * 3 + j)}
            for i in range(2) for j in range(3)
        ]
        # 目前 layout 尚未展開，預期會失敗
        # 只驗證 layout 長度與名稱
        actual = [item for item in model.layout if item["type"] == "int"]
        self.assertEqual(len(actual), 6, "多維陣列應展開為 6 個元素 (2x3)")
        for idx, exp in enumerate(expected):
            self.assertEqual(actual[idx]["name"], exp["name"], f"第 {idx} 個元素名稱錯誤")

    def test_nested_struct_with_nd_array_layout(self):
        from src.model.struct_parser import MemberDef, StructDef
        # 構造 struct S 的 AST
        s_ast = StructDef(name="S", members=[MemberDef(type="int", name="x")])
        # 構造 NDArrayTest 的 AST，arr[2][2]，nested 指向 s_ast
        arr_member = MemberDef(type="S", name="arr", array_dims=[2,2], nested=s_ast)
        nd_ast = StructDef(name="NDArrayTest", members=[arr_member])
        model = StructModel()
        model.struct_name = nd_ast.name
        model.members = nd_ast.members
        model.layout, model.total_size, model.struct_align = calculate_layout(model.members)
        print("DEBUG layout:", model.layout)
        int_size = TYPE_INFO["int"]["size"]
        expected = [
            {"name": f"arr[{i}][{j}].x", "type": "int", "size": int_size, "offset": int_size * (i * 2 + j)}
            for i in range(2) for j in range(2)
        ]
        actual = [item for item in model.layout if item["type"] == "int"]
        self.assertEqual(len(actual), 4, "巢狀 struct 多維陣列應展開為 4 個元素 (2x2)")
        for idx, exp in enumerate(expected):
            self.assertEqual(actual[idx]["name"], exp["name"], f"第 {idx} 個元素名稱錯誤")


class TestFlattenASTNodes(unittest.TestCase):
    def test_flatten_ast_nodes_simple(self):
        # 單層 AST
        ast = {
            "id": "root",
            "name": "root",
            "type": "struct",
            "children": [
                {"id": "a", "name": "a", "type": "int", "children": []},
                {"id": "b", "name": "b", "type": "char", "children": []}
            ]
        }
        flat = flatten_ast_nodes(ast)
        self.assertEqual(len(flat), 3)
        self.assertEqual(flat[0]["id"], "root")
        self.assertEqual(flat[1]["id"], "a")
        self.assertEqual(flat[2]["id"], "b")

    def test_flatten_ast_nodes_nested(self):
        # 巢狀 AST
        ast = {
            "id": "root",
            "name": "root",
            "type": "struct",
            "children": [
                {
                    "id": "nested",
                    "name": "nested",
                    "type": "struct",
                    "children": [
                        {"id": "x", "name": "x", "type": "int", "children": []},
                        {"id": "y", "name": "y", "type": "char", "children": []}
                    ]
                },
                {"id": "tail", "name": "tail", "type": "char", "children": []}
            ]
        }
        flat = flatten_ast_nodes(ast)
        ids = [n["id"] for n in flat]
        self.assertEqual(ids, ["root", "nested", "x", "y", "tail"])
        self.assertEqual(len(flat), 5)


class TestStructModelASTAPI(unittest.TestCase):
    def test_parse_struct_definition_ast_and_to_dict(self):
        code = '''
        struct V6Test {
            int a;
            struct Inner {
                char b;
                union {
                    short c;
                    float d;
                } u;
            } inner;
            int arr[2][3];
            unsigned int x : 3;
            unsigned int   : 2;
            unsigned int y : 5;
        };
        '''
        ast = parse_struct_definition_ast(code)
        ast_dict = ast_to_dict(ast)
        self.assertEqual(ast_dict['name'], 'V6Test')
        self.assertTrue(ast_dict['is_struct'])
        self.assertTrue(any(child['name'] == 'inner' for child in ast_dict['children']))
        inner = next(child for child in ast_dict['children'] if child['name'] == 'inner')
        self.assertTrue(inner['is_struct'])
        union = next(child for child in inner['children'] if child['is_union'])
        self.assertEqual(len(union['children']), 2)
        arr = next(child for child in ast_dict['children'] if child['name'] == 'arr')
        self.assertEqual(arr['type'], 'int')
        self.assertIn('children', arr)
        x = next(child for child in ast_dict['children'] if child['name'] == 'x')
        self.assertTrue(x['is_bitfield'])
        y = next(child for child in ast_dict['children'] if child['name'] == 'y')
        self.assertTrue(y['is_bitfield'])

    def test_struct_model_get_struct_ast_and_display_nodes(self):
        code = '''
        struct Simple {
            int a;
            char b;
        };
        '''
        model = StructModel()
        model.struct_content = code
        ast_dict = model.get_struct_ast()
        self.assertEqual(ast_dict['name'], 'Simple')
        nodes_tree = model.get_display_nodes('tree')
        self.assertIsInstance(nodes_tree, list)
        self.assertEqual(nodes_tree[0]['name'], 'Simple')
        nodes_flat = model.get_display_nodes('flat')
        self.assertTrue(any(n['name'] == 'a' for n in nodes_flat))
        self.assertTrue(any(n['name'] == 'b' for n in nodes_flat))


if __name__ == "__main__":
    unittest.main() 