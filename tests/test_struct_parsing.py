import unittest
import tempfile
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.struct_model import parse_struct_definition, calculate_layout
from model.layout import LayoutCalculator, LayoutItem

class TestParseStructDefinition(unittest.TestCase):
    """Test cases for struct definition parsing functionality."""
    
    def test_valid_struct_definition(self):
        """Test parsing a valid struct definition."""
        content = """
        struct TestStruct {
            char a;
            int b;
            long long c;
        };
        """
        struct_name, members = parse_struct_definition(content)
        self.assertEqual(struct_name, "TestStruct")
        self.assertEqual(len(members), 3)
        self.assertEqual(members[0], ("char", "a"))
        self.assertEqual(members[1], ("int", "b"))
        self.assertEqual(members[2], ("long long", "c"))
    
    def test_struct_with_bitfields(self):
        """Test parsing struct with bit field members."""
        content = """
        struct BitFieldStruct {
            int a : 1;
            int b : 2;
            char c;
            int d : 3;
        };
        """
        struct_name, members = parse_struct_definition(content)
        self.assertEqual(struct_name, "BitFieldStruct")
        self.assertEqual(len(members), 4)
        
        # Check bitfield members
        self.assertTrue(members[0]["is_bitfield"])
        self.assertEqual(members[0]["name"], "a")
        self.assertEqual(members[0]["bit_size"], 1)
        
        self.assertTrue(members[1]["is_bitfield"])
        self.assertEqual(members[1]["name"], "b")
        self.assertEqual(members[1]["bit_size"], 2)
        
        # Check regular member
        self.assertEqual(members[2], ("char", "c"))
        
        # Check another bitfield
        self.assertTrue(members[3]["is_bitfield"])
        self.assertEqual(members[3]["name"], "d")
        self.assertEqual(members[3]["bit_size"], 3)
    
    def test_struct_with_pointer(self):
        """Test parsing struct with pointer types."""
        content = """
        struct PointerStruct {
            int* ptr;
            char* str;
        };
        """
        struct_name, members = parse_struct_definition(content)
        self.assertEqual(struct_name, "PointerStruct")
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0], ("pointer", "ptr"))
        self.assertEqual(members[1], ("pointer", "str"))
    
    def test_struct_with_unsigned_types(self):
        """Test parsing struct with unsigned types."""
        content = """
        struct UnsignedStruct {
            unsigned int a;
            unsigned long b;
        };
        """
        struct_name, members = parse_struct_definition(content)
        self.assertEqual(struct_name, "UnsignedStruct")
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0], ("unsigned int", "a"))
        self.assertEqual(members[1], ("unsigned long", "b"))
    
    def test_struct_with_whitespace(self):
        """Test parsing struct with various whitespace patterns."""
        content = """
        struct WhitespaceStruct {
            char    a;
            int     b;
            long long   c;
        };
        """
        struct_name, members = parse_struct_definition(content)
        self.assertEqual(struct_name, "WhitespaceStruct")
        self.assertEqual(len(members), 3)
        self.assertEqual(members[0], ("char", "a"))
        self.assertEqual(members[1], ("int", "b"))
        self.assertEqual(members[2], ("long long", "c"))
    
    def test_struct_with_unknown_type(self):
        """Test parsing struct with unknown type (should be ignored)."""
        content = """
        struct UnknownStruct {
            char a;
            unknown_type b;
            int c;
        };
        """
        struct_name, members = parse_struct_definition(content)
        self.assertEqual(struct_name, "UnknownStruct")
        self.assertEqual(len(members), 2)  # unknown_type should be ignored
        self.assertEqual(members[0], ("char", "a"))
        self.assertEqual(members[1], ("int", "c"))
    
    def test_invalid_struct_no_match(self):
        """Test parsing invalid struct that doesn't match pattern."""
        content = "This is not a struct definition"
        struct_name, members = parse_struct_definition(content)
        self.assertIsNone(struct_name)
        self.assertIsNone(members)


class TestLayoutCalculator(unittest.TestCase):
    """Test cases for LayoutCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = LayoutCalculator()
    
    def test_simple_struct_no_padding(self):
        """Test layout calculation for struct with no padding needed."""
        members = [("char", "a"), ("char", "b"), ("char", "c")]
        layout, total_size, alignment = self.calculator.calculate(members)
        
        self.assertEqual(total_size, 3)
        self.assertEqual(alignment, 1)
        self.assertEqual(len(layout), 3)
        
        # Check each member
        self.assertEqual(layout[0]["name"], "a")
        self.assertEqual(layout[0]["offset"], 0)
        self.assertEqual(layout[0]["size"], 1)
        
        self.assertEqual(layout[1]["name"], "b")
        self.assertEqual(layout[1]["offset"], 1)
        self.assertEqual(layout[1]["size"], 1)
        
        self.assertEqual(layout[2]["name"], "c")
        self.assertEqual(layout[2]["offset"], 2)
        self.assertEqual(layout[2]["size"], 1)
    
    def test_struct_with_padding(self):
        """Test layout calculation for struct requiring padding."""
        members = [("char", "a"), ("int", "b"), ("char", "c")]
        layout, total_size, alignment = self.calculator.calculate(members)
        
        self.assertEqual(total_size, 12)  # 1 + 3(padding) + 4 + 1 + 3(padding)
        self.assertEqual(alignment, 4)
        self.assertEqual(len(layout), 5)  # 3 members + 2 padding entries
        
        # Check padding
        self.assertEqual(layout[1]["type"], "padding")
        self.assertEqual(layout[1]["size"], 3)
        self.assertEqual(layout[4]["type"], "padding")
        self.assertEqual(layout[4]["size"], 3)
    
    def test_bitfield_layout(self):
        """Test layout calculation for struct with bit fields."""
        members = [
            {"type": "int", "name": "a", "is_bitfield": True, "bit_size": 1},
            {"type": "int", "name": "b", "is_bitfield": True, "bit_size": 2},
            {"type": "char", "name": "c", "is_bitfield": False},
            {"type": "int", "name": "d", "is_bitfield": True, "bit_size": 3}
        ]
        layout, total_size, alignment = self.calculator.calculate(members)
        
        self.assertEqual(total_size, 12)  # 4 + 1 + 3(padding) + 4
        self.assertEqual(alignment, 4)
        self.assertEqual(len(layout), 5)  # 4 members + 1 padding
        
        # 只檢查 is_bitfield 存在的欄位
        bitfields = [item for item in layout if item.get("is_bitfield")]
        self.assertEqual(len(bitfields), 3)
        self.assertEqual(bitfields[0]["bit_offset"], 0)
        self.assertEqual(bitfields[0]["bit_size"], 1)
        self.assertEqual(bitfields[1]["bit_offset"], 1)
        self.assertEqual(bitfields[1]["bit_size"], 2)
        self.assertEqual(bitfields[2]["bit_offset"], 0)
        self.assertEqual(bitfields[2]["bit_size"], 3)
        # 也檢查非 bitfield 欄位
        non_bf = [item for item in layout if not item.get("is_bitfield") and item["type"] != "padding"]
        self.assertEqual(len(non_bf), 1)
        self.assertEqual(non_bf[0]["name"], "c")

class TestLayoutItemDataclass(unittest.TestCase):
    """Ensure calculate_layout returns LayoutItem objects."""

    def test_layout_item_instances(self):
        members = [("char", "a"), ("int", "b")]
        layout, _, _ = calculate_layout(members)
        self.assertTrue(all(isinstance(item, LayoutItem) for item in layout))
        self.assertEqual(layout[0].name, "a")
        b_entry = next((item for item in layout if item.name == "b"), None)
        self.assertIsNotNone(b_entry)
        self.assertEqual(b_entry.type, "int")



if __name__ == '__main__':
    unittest.main() 