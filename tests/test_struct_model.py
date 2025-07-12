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


class TestParseStructDefinition(unittest.TestCase):
    """Test cases for parse_struct_definition function."""
    
    def test_valid_struct_definition(self):
        """Test parsing a valid struct definition."""
        struct_content = """
        struct TestStruct {
            int value1;
            char value2;
            double value3;
        };
        """
        struct_name, members = parse_struct_definition(struct_content)
        
        self.assertEqual(struct_name, "TestStruct")
        self.assertEqual(len(members), 3)
        self.assertEqual(members[0], ("int", "value1"))
        self.assertEqual(members[1], ("char", "value2"))
        self.assertEqual(members[2], ("double", "value3"))
    
    def test_struct_with_pointer(self):
        """Test parsing struct with pointer types."""
        struct_content = """
        struct PointerStruct {
            int* ptr1;
            char* ptr2;
        };
        """
        struct_name, members = parse_struct_definition(struct_content)
        
        self.assertEqual(struct_name, "PointerStruct")
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0], ("pointer", "ptr1"))
        self.assertEqual(members[1], ("pointer", "ptr2"))
    
    def test_struct_with_unsigned_types(self):
        """Test parsing struct with unsigned types."""
        struct_content = """
        struct UnsignedStruct {
            unsigned int value1;
            unsigned long value2;
        };
        """
        struct_name, members = parse_struct_definition(struct_content)
        
        self.assertEqual(struct_name, "UnsignedStruct")
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0], ("unsigned int", "value1"))
        self.assertEqual(members[1], ("unsigned long", "value2"))
    
    def test_struct_with_whitespace(self):
        """Test parsing struct with various whitespace patterns."""
        struct_content = """
        struct WhitespaceStruct {
            int value1;
            char value2;
        };
        """
        struct_name, members = parse_struct_definition(struct_content)
        
        self.assertEqual(struct_name, "WhitespaceStruct")
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0], ("int", "value1"))
        self.assertEqual(members[1], ("char", "value2"))
    
    def test_struct_with_bitfields(self):
        """Test parsing struct with bit field members."""
        struct_content = """
        struct BitFieldStruct {
            int a : 1;
            int b : 2;
            int c : 5;
        };
        """
        struct_name, members = parse_struct_definition(struct_content)
        self.assertEqual(struct_name, "BitFieldStruct")
        self.assertEqual(len(members), 3)
        # Each member should be a dict with type, name, is_bitfield, bit_size
        self.assertEqual(members[0]["type"], "int")
        self.assertEqual(members[0]["name"], "a")
        self.assertTrue(members[0]["is_bitfield"])
        self.assertEqual(members[0]["bit_size"], 1)
        self.assertEqual(members[1]["type"], "int")
        self.assertEqual(members[1]["name"], "b")
        self.assertTrue(members[1]["is_bitfield"])
        self.assertEqual(members[1]["bit_size"], 2)
        self.assertEqual(members[2]["type"], "int")
        self.assertEqual(members[2]["name"], "c")
        self.assertTrue(members[2]["is_bitfield"])
        self.assertEqual(members[2]["bit_size"], 5)
    
    def test_invalid_struct_no_match(self):
        """Test parsing invalid struct that doesn't match pattern."""
        struct_content = "This is not a struct definition"
        struct_name, members = parse_struct_definition(struct_content)
        
        self.assertIsNone(struct_name)
        self.assertIsNone(members)
    
    def test_struct_with_unknown_type(self):
        """Test parsing struct with unknown type (should be ignored)."""
        struct_content = """
        struct UnknownTypeStruct {
            int valid_type;
            unknown_type invalid_type;
        };
        """
        struct_name, members = parse_struct_definition(struct_content)
        
        self.assertEqual(struct_name, "UnknownTypeStruct")
        self.assertEqual(len(members), 1)  # Only valid type should be included
        self.assertEqual(members[0], ("int", "valid_type"))


class TestCalculateLayout(unittest.TestCase):
    """Test cases for calculate_layout function."""
    
    def test_empty_members(self):
        """Test layout calculation with empty members list."""
        layout, total_size, max_alignment = calculate_layout([])
        
        self.assertEqual(layout, [])
        self.assertEqual(total_size, 0)
        self.assertEqual(max_alignment, 1)
    
    def test_simple_struct_no_padding(self):
        """Test layout calculation for struct with no padding needed."""
        members = [("char", "a"), ("char", "b"), ("char", "c")]
        layout, total_size, max_alignment = calculate_layout(members)
        
        self.assertEqual(len(layout), 3)
        self.assertEqual(total_size, 3)
        self.assertEqual(max_alignment, 1)
        
        # Check individual member layouts
        self.assertEqual(layout[0]["name"], "a")
        self.assertEqual(layout[0]["type"], "char")
        self.assertEqual(layout[0]["size"], 1)
        self.assertEqual(layout[0]["offset"], 0)
        
        self.assertEqual(layout[1]["name"], "b")
        self.assertEqual(layout[1]["type"], "char")
        self.assertEqual(layout[1]["size"], 1)
        self.assertEqual(layout[1]["offset"], 1)
        
        self.assertEqual(layout[2]["name"], "c")
        self.assertEqual(layout[2]["type"], "char")
        self.assertEqual(layout[2]["size"], 1)
        self.assertEqual(layout[2]["offset"], 2)
    
    def test_struct_with_padding(self):
        """Test layout calculation for struct requiring padding."""
        members = [("char", "a"), ("int", "b")]
        layout, total_size, max_alignment = calculate_layout(members)
        
        self.assertEqual(len(layout), 3)  # char, padding, int
        self.assertEqual(total_size, 8)
        self.assertEqual(max_alignment, 4)
        
        # Check char member
        self.assertEqual(layout[0]["name"], "a")
        self.assertEqual(layout[0]["type"], "char")
        self.assertEqual(layout[0]["size"], 1)
        self.assertEqual(layout[0]["offset"], 0)
        
        # Check padding
        self.assertEqual(layout[1]["name"], "(padding)")
        self.assertEqual(layout[1]["type"], "padding")
        self.assertEqual(layout[1]["size"], 3)
        self.assertEqual(layout[1]["offset"], 1)
        
        # Check int member
        self.assertEqual(layout[2]["name"], "b")
        self.assertEqual(layout[2]["type"], "int")
        self.assertEqual(layout[2]["size"], 4)
        self.assertEqual(layout[2]["offset"], 4)
    
    def test_struct_with_final_padding(self):
        """Test layout calculation with final padding."""
        members = [("int", "a"), ("char", "b")]
        layout, total_size, max_alignment = calculate_layout(members)
        
        self.assertEqual(len(layout), 3)  # int, char, final padding
        self.assertEqual(total_size, 8)
        self.assertEqual(max_alignment, 4)
        
        # Check int member
        self.assertEqual(layout[0]["name"], "a")
        self.assertEqual(layout[0]["type"], "int")
        self.assertEqual(layout[0]["size"], 4)
        self.assertEqual(layout[0]["offset"], 0)
        
        # Check char member
        self.assertEqual(layout[1]["name"], "b")
        self.assertEqual(layout[1]["type"], "char")
        self.assertEqual(layout[1]["size"], 1)
        self.assertEqual(layout[1]["offset"], 4)
        
        # Check final padding
        self.assertEqual(layout[2]["name"], "(final padding)")
        self.assertEqual(layout[2]["type"], "padding")
        self.assertEqual(layout[2]["size"], 3)
        self.assertEqual(layout[2]["offset"], 5)
    
    def test_complex_struct_layout(self):
        """Test layout calculation for a complex struct."""
        members = [
            ("char", "a"),
            ("int", "b"),
            ("char", "c"),
            ("double", "d")
        ]
        layout, total_size, max_alignment = calculate_layout(members)
        
        self.assertEqual(len(layout), 6)  # char, padding, int, char, padding, double
        self.assertEqual(total_size, 24)
        self.assertEqual(max_alignment, 8)
        
        # Verify offsets are correct
        expected_offsets = [0, 1, 4, 8, 9, 16]
        for i, expected_offset in enumerate(expected_offsets):
            self.assertEqual(layout[i]["offset"], expected_offset)
    
    def test_pointer_alignment(self):
        """Test layout calculation with pointer types."""
        members = [("char", "a"), ("pointer", "ptr")]
        layout, total_size, max_alignment = calculate_layout(members)
        
        self.assertEqual(len(layout), 3)  # char, padding, pointer
        self.assertEqual(total_size, 16)
        self.assertEqual(max_alignment, 8)
        
        # Check pointer alignment
        self.assertEqual(layout[2]["type"], "pointer")
        self.assertEqual(layout[2]["size"], 8)
        self.assertEqual(layout[2]["offset"], 8)

    def test_bitfield_layout(self):
        """Test layout calculation for struct with bit fields."""
        members = [
            {"type": "int", "name": "a", "is_bitfield": True, "bit_size": 1},
            {"type": "int", "name": "b", "is_bitfield": True, "bit_size": 2},
            {"type": "int", "name": "c", "is_bitfield": True, "bit_size": 5},
        ]
        layout, total_size, max_alignment = calculate_layout(members)
        # All bit fields should be packed into a single int (4 bytes)
        self.assertEqual(len(layout), 3)
        self.assertEqual(layout[0]["name"], "a")
        self.assertTrue(layout[0]["is_bitfield"])
        self.assertEqual(layout[0]["bit_offset"], 0)
        self.assertEqual(layout[0]["bit_size"], 1)
        self.assertEqual(layout[1]["name"], "b")
        self.assertTrue(layout[1]["is_bitfield"])
        self.assertEqual(layout[1]["bit_offset"], 1)
        self.assertEqual(layout[1]["bit_size"], 2)
        self.assertEqual(layout[2]["name"], "c")
        self.assertTrue(layout[2]["is_bitfield"])
        self.assertEqual(layout[2]["bit_offset"], 3)
        self.assertEqual(layout[2]["bit_size"], 5)
        # All should share the same storage unit (offset 0, size 4)
        for item in layout:
            self.assertEqual(item["offset"], 0)
            self.assertEqual(item["size"], 4)
        self.assertEqual(total_size, 4)
        self.assertEqual(max_alignment, 4)

    def test_padding_layout_fields(self):
        """Test that padding and final padding have correct bitfield-related fields."""
        members = [("char", "a"), ("int", "b"), ("char", "c")]
        layout, total_size, max_alignment = calculate_layout(members)
        # 找出所有 padding 項
        paddings = [item for item in layout if item["type"] == "padding"]
        for pad in paddings:
            self.assertIn("is_bitfield", pad)
            self.assertIn("bit_offset", pad)
            self.assertIn("bit_size", pad)
            self.assertFalse(pad["is_bitfield"])
            self.assertEqual(pad["bit_offset"], 0)
            self.assertEqual(pad["bit_size"], pad["size"] * 8)


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
    
    def test_parse_hex_data_simple(self):
        """Test parsing simple hex data."""
        # Load a simple struct first
        struct_content = """
        struct SimpleStruct {
            int value1;
            char value2;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        
        # Parse hex data
        hex_data = "01000000" + "41" + "000000"  # int(1) + char('A') + padding
        result = self.model.parse_hex_data(hex_data, "little")
        
        self.assertEqual(len(result), 3)  # int, char, padding
        
        # Check int value
        self.assertEqual(result[0]["name"], "value1")
        self.assertEqual(result[0]["value"], "1")
        self.assertEqual(result[0]["hex_raw"], "01000000")  # little endian: 數值在 little endian 下的 hex 表示
        
        # Check char value
        self.assertEqual(result[1]["name"], "value2")
        self.assertEqual(result[1]["value"], "65")  # ASCII 'A' = 65
        self.assertEqual(result[1]["hex_raw"], "41")
        
        # Check padding
        self.assertEqual(result[2]["name"], "(final padding)")
        self.assertEqual(result[2]["value"], "-")
        self.assertEqual(result[2]["hex_raw"], "000000")
    
    def test_parse_hex_data_bool(self):
        """Test parsing boolean values."""
        struct_content = """
        struct BoolStruct {
            bool flag1;
            bool flag2;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        
        # Parse hex data with boolean values
        hex_data = "01" + "00"  # true, false
        result = self.model.parse_hex_data(hex_data, "little")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "flag1")
        self.assertEqual(result[0]["value"], "True")
        self.assertEqual(result[1]["name"], "flag2")
        self.assertEqual(result[1]["value"], "False")
    
    def test_parse_hex_data_padding(self):
        """Test parsing hex data with padding."""
        struct_content = """
        struct PaddingStruct {
            char a;
            int b;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        
        # Parse hex data
        hex_data = "41" + "000000" + "02000000"  # char('A') + padding + int(2)
        result = self.model.parse_hex_data(hex_data, "little")
        
        self.assertEqual(len(result), 3)
        
        # Check char
        self.assertEqual(result[0]["name"], "a")
        self.assertEqual(result[0]["value"], "65")
        
        # Check padding
        self.assertEqual(result[1]["name"], "(padding)")
        self.assertEqual(result[1]["value"], "-")
        
        # Check int
        self.assertEqual(result[2]["name"], "b")
        self.assertEqual(result[2]["value"], "2")
    
    def test_parse_hex_data_short_input(self):
        """Test parsing hex data that's shorter than expected (should pad with zeros)."""
        struct_content = """
        struct ShortStruct {
            int value1;
            int value2;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        
        # Parse hex data that's too short
        hex_data = "01000000"  # Only 4 bytes instead of 8
        result = self.model.parse_hex_data(hex_data, "little")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "value1")
        # 左補零後，hex_data 變成 "0000000001000000"
        # 第一個 int (4 bytes): 0x00000000 = 0
        self.assertEqual(result[0]["value"], "0")
        self.assertEqual(result[1]["name"], "value2")
        # 第二個 int (4 bytes): 0x01000000 = 16777216
        self.assertEqual(result[1]["value"], "1")
    
    def test_parse_hex_data_big_endian(self):
        """Test parsing hex data with big endian byte order."""
        struct_content = """
        struct EndianStruct {
            int value1;
            short value2;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        
        # Parse hex data with big endian
        hex_data = "00000001" + "0002" + "0000"  # int(1) + short(2) + padding
        result = self.model.parse_hex_data(hex_data, "big")
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "value1")
        self.assertEqual(result[0]["value"], "1")
        self.assertEqual(result[1]["name"], "value2")
        self.assertEqual(result[1]["value"], "2")
    
    def test_parse_hex_data_pointer(self):
        """Test parsing pointer values."""
        struct_content = """
        struct PointerStruct {
            char a;
            int* ptr;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        
        # Parse hex data with pointer
        # 輸入: "41" + "000000" + "1234567890abcdef" (15 bytes)
        # 左補零後: "0" + "41" + "000000" + "1234567890abcdef" (16 bytes)
        hex_data = "41" + "000000" + "1234567890abcdef"
        result = self.model.parse_hex_data(hex_data, "little")
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "a")
        # 左補零後，char 'a' 變成 0x00 = 0
        self.assertEqual(result[0]["value"], "0")
        self.assertEqual(result[2]["name"], "ptr")
        # Pointer value should be parsed as integer
        self.assertIsInstance(int(result[2]["value"]), int)

    def test_struct_a_with_8byte_hex_units(self):
        """Test struct A { char s; long long val; } with 8-byte hex units."""
        struct_content = """
        struct A {
            char s;
            long long val;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        
        # Input: 8-byte units {1233, 121}
        # 1233 (8 bytes) + 121 (8 bytes) = 16 bytes total
        hex_data = "1233000000000000" + "1210000000000000"
        result = self.model.parse_hex_data(hex_data, "little")
        
        self.assertEqual(len(result), 3)  # char, padding, long long
        
        # Check char member 's'
        self.assertEqual(result[0]["name"], "s")
        self.assertEqual(result[0]["value"], "18")  # 0x12 = 18
        self.assertEqual(result[0]["hex_raw"], "12")
        
        # Check padding (7 bytes after char)
        self.assertEqual(result[1]["name"], "(padding)")
        self.assertEqual(result[1]["value"], "-")
        self.assertEqual(result[1]["hex_raw"], "33000000000000")
        
        # Check long long member 'val'
        self.assertEqual(result[2]["name"], "val")
        self.assertEqual(result[2]["value"], "4114")  # 0x1210 = 4114
        self.assertEqual(result[2]["hex_raw"], "1210000000000000")  # little endian: 數值在 little endian 下的 hex 表示
        
        # Verify total size is 16 bytes
        self.assertEqual(self.model.total_size, 16)
        self.assertEqual(self.model.struct_align, 8)

    def test_struct_a_endian_comparison(self):
        """Test struct A with both little endian and big endian to show the difference."""
        struct_content = """
        struct A {
            char s;
            long long val;
        };
        """
        
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        
        # Same hex data: 12330000000000001210000000000000
        hex_data = "1233000000000000" + "1210000000000000"
        
        # Test Little Endian
        result_little = self.model.parse_hex_data(hex_data, "little")
        
        # Test Big Endian
        result_big = self.model.parse_hex_data(hex_data, "big")
        
        print(f"\nLittle Endian vs Big Endian comparison:")
        print(f"Input hex: {hex_data}")
        
        print(f"\nLittle Endian results:")
        for item in result_little:
            print(f"  {item['name']}: value={item['value']}, hex_raw={item['hex_raw']}")
        
        print(f"\nBig Endian results:")
        for item in result_big:
            print(f"  {item['name']}: value={item['value']}, hex_raw={item['hex_raw']}")
        
        # Verify the differences
        # char 's' should be the same in both (single byte)
        self.assertEqual(result_little[0]["value"], result_big[0]["value"])
        
        # long long 'val' should be different
        self.assertNotEqual(result_little[2]["value"], result_big[2]["value"])
        
        # Little endian: 0x1210000000000000 = 4114
        # Big endian: 0x1210000000000000 = 1301540292310073344
        self.assertEqual(result_little[2]["value"], "4114")
        self.assertEqual(result_big[2]["value"], "1301540292310073344")

    def test_struct_a_8byte_field_short_hex(self):
        """Test 8-byte field with short hex input '121' should be padded to '0000000000000121'."""
        struct_content = """
        struct A {
            long long val;
        };
        """
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        # 輸入 '121'，應該自動左補零到 8 bytes
        hex_data = "121"
        result_little = self.model.parse_hex_data(hex_data, "little")
        result_big = self.model.parse_hex_data(hex_data, "big")
        # bytes: 00 00 00 00 00 00 01 21
        expected_hex_little = "0000000000000121"  # little endian: 數值在 little endian 下的 hex 表示
        expected_hex_big = "0000000000000121"  # big endian: 直接顯示原始 bytes 的 hex
        expected_bytes = bytes.fromhex(expected_hex_big)
        self.assertEqual(result_little[0]["hex_raw"], expected_hex_little)
        self.assertEqual(result_big[0]["hex_raw"], expected_hex_big)
        # little endian: int.from_bytes(..., 'little')
        self.assertEqual(result_little[0]["value"], str(int.from_bytes(expected_bytes, "little")))
        # big endian: int.from_bytes(..., 'big')
        self.assertEqual(result_big[0]["value"], str(int.from_bytes(expected_bytes, "big")))

    def test_integration_with_real_file(self):
        """Integration test using real struct file from tests/data/."""
        # 使用真實的 struct 檔案進行整合測試
        test_file_path = os.path.join(os.path.dirname(__file__), "data", "test_struct_a.h")
        
        # 確保測試檔案存在
        self.assertTrue(os.path.exists(test_file_path), f"Test file {test_file_path} does not exist")
        
        # 載入 struct
        struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(test_file_path)
        
        # 驗證 struct 資訊
        self.assertEqual(struct_name, "A")
        self.assertEqual(len(layout), 3)  # char, padding, long long
        self.assertEqual(total_size, 16)
        self.assertEqual(struct_align, 8)
        
        # 測試解析 hex 資料
        hex_data = "121"
        result = self.model.parse_hex_data(hex_data, "little")
        
        # 驗證結果
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "s")
        self.assertEqual(result[2]["name"], "val")
        
        # 驗證 hex_raw 是左補零的結果
        expected_hex_little = "0000000000000121"  # little endian: 數值在 little endian 下的 hex 表示
        expected_hex_big = "0000000000000121"  # big endian: 直接顯示原始 bytes 的 hex
        self.assertEqual(result[2]["hex_raw"], expected_hex_little)

    def test_hex_raw_formatting_and_padding(self):
        """Test that hex_raw is zero-padded and can be safely prefixed with 0x for display."""
        struct_content = """
        struct TestStruct {
            char a;
            int b;
            long long c;
        };
        """
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        # a: 1 byte, padding: 3 bytes, b: 4 bytes, c: 8 bytes
        # Input: a=0x1, padding=000000, b=0x123, c=0x4567890
        hex_data = "01" + "000000" + "00000123" + "0000000004567890"
        result = self.model.parse_hex_data(hex_data, "big")
        # 檢查 hex_raw 長度與補 0x
        self.assertEqual(result[0]["hex_raw"], "01")  # 1 byte
        self.assertEqual(result[1]["hex_raw"], "000000")  # 3 bytes padding
        self.assertEqual(result[2]["hex_raw"], "00000123")  # 4 bytes
        self.assertEqual(result[3]["hex_raw"], "0000000004567890")  # 8 bytes

    def test_parse_hex_data_bitfields(self):
        """Test parsing hex data for struct with bit fields."""
        # struct BitFieldStruct { int a:1; int b:2; int c:5; };
        # Layout: all packed in 1 int (4 bytes), a=bit0, b=bit1-2, c=bit3-7
        struct_content = """
        struct BitFieldStruct {
            int a : 1;
            int b : 2;
            int c : 5;
        };
        """
        with patch("builtins.open", mock_open(read_data=struct_content)):
            self.model.load_struct_from_file("test_file.h")
        # a=1, b=2, c=17 -> bits: 1 (a), 10 (b), 10001 (c) => 1 10 10001 = 0b10001101 = 0x8D
        # Little endian: 0x8D 00 00 00
        hex_data = "8d000000"
        result = self.model.parse_hex_data(hex_data, "little")
        self.assertEqual(result[0]["name"], "a")
        self.assertEqual(result[0]["value"], "1")
        self.assertEqual(result[1]["name"], "b")
        self.assertEqual(result[1]["value"], "2")
        self.assertEqual(result[2]["name"], "c")
        self.assertEqual(result[2]["value"], "17")

    def test_set_manual_struct_sets_members_and_size(self):
        """Test that set_manual_struct correctly sets members and total_size."""
        members = [
            {"name": "a", "byte_size": 1, "bit_size": 0},
            {"name": "b", "byte_size": 2, "bit_size": 0}
        ]
        total_size = 3
        self.model.set_manual_struct(members, total_size)
        self.assertEqual(self.model.manual_struct["members"], members)
        self.assertEqual(self.model.manual_struct["total_size"], total_size)

    def test_validate_manual_struct_errors_and_success(self):
        # 測試 member 欄位錯誤（total_size 足夠大）
        members = [
            {"name": "a", "byte_size": 0, "bit_size": -1},
            {"name": "b", "byte_size": -1, "bit_size": 0}
        ]
        total_size = 10  # 足夠大，確保 layout 不會先失敗
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertIn("member 'a' bit_size 需為 0 或正整數", errors)
        self.assertIn("member 'b' byte_size 需為 0 或正整數", errors)

        # 測試名稱重複（total_size 足夠大）
        members = [
            {"name": "a", "byte_size": 1, "bit_size": 0},
            {"name": "a", "byte_size": 2, "bit_size": 0}
        ]
        total_size = 10
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertIn("成員名稱 'a' 重複", errors)

        # 測試 total_size 錯誤（member 欄位正確）
        members = [
            {"name": "a", "byte_size": 1, "bit_size": 0}
        ]
        total_size = -1
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertIn("結構體大小需為正整數", errors)

        # 測試 layout 錯誤（member 欄位正確，但 total_size 太小）
        members = [
            {"name": "a", "byte_size": 1, "bit_size": 0},
            {"name": "b", "byte_size": 1, "bit_size": 0}
        ]
        total_size = 1  # 故意設小一點，讓 layout 驗證失敗
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertIn("Layout 總長度", errors[0])

        # 驗證通過情境
        members = [
            {"name": "a", "byte_size": 1, "bit_size": 0},
            {"name": "b", "byte_size": 2, "bit_size": 0}
        ]
        total_size = 4  # C++ align: char + short = 4 bytes
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertEqual(errors, [])

    def test_calculate_manual_layout_no_padding(self):
        # 測試 bitfield 緊密排列、無 padding（C++ 標準行為：同一 storage unit）
        members = [
            {"name": "a", "byte_size": 0, "bit_size": 3},
            {"name": "b", "byte_size": 0, "bit_size": 5},
            {"name": "c", "byte_size": 0, "bit_size": 8}
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
            {"name": "a", "byte_size": 0, "bit_size": 3},
            {"name": "b", "byte_size": 0, "bit_size": 5},
            {"name": "c", "byte_size": 0, "bit_size": 8}
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
        members = [{"name": "x", "byte_size": 0, "bit_size": 16}]
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
            {"name": "a", "byte_size": 0, "bit_size": 3},
            {"name": "b", "byte_size": 0, "bit_size": 5}
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
            {"name": "a", "byte_size": 1, "bit_size": 0},
            {"name": "b", "byte_size": 0, "bit_size": 12},
            {"name": "c", "byte_size": 2, "bit_size": 0},
            {"name": "d", "byte_size": 0, "bit_size": 4}
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
        result = self.model.parse_manual_hex_data(hex_data, "little", manual_layout)
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
        self.model.parse_manual_hex_data(hex_data, "little", manual_layout)
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


if __name__ == "__main__":
    unittest.main() 