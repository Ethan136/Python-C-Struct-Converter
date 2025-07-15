import unittest
import tempfile
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model.struct_model import StructModel

class TestStructModel(unittest.TestCase):
    """Test cases for StructModel integration functionality."""
    
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
        self.assertIsNotNone(self.model.input_processor)
    
    def test_load_struct_from_file_valid(self):
        """Test loading a valid struct from file."""
        # Create temporary file with valid struct
        content = """
        struct TestStruct {
            char a;
            int b;
            long long c;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        
        try:
            struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(file_path)
            
            self.assertEqual(struct_name, "TestStruct")
            self.assertEqual(total_size, 16)  # 1 + 3(padding) + 4 + 8
            self.assertEqual(struct_align, 8)
            self.assertEqual(len(layout), 4)  # 3 members + 1 padding
            
            # Check that model state is updated
            self.assertEqual(self.model.struct_name, "TestStruct")
            self.assertEqual(self.model.total_size, 16)
            self.assertEqual(self.model.struct_align, 8)
            
        finally:
            os.unlink(file_path)
    
    def test_load_struct_from_file_invalid(self):
        """Test loading an invalid struct from file."""
        # Create temporary file with invalid content
        content = "This is not a struct definition"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        
        try:
            with self.assertRaises(ValueError):
                self.model.load_struct_from_file(file_path)
        finally:
            os.unlink(file_path)
    
    def test_parse_hex_data_simple(self):
        """Test parsing simple hex data."""
        # Load a simple struct first
        content = """
        struct SimpleStruct {
            char a;
            int b;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        
        try:
            self.model.load_struct_from_file(file_path)
            
            # Parse hex data: 1 byte for char, 3 bytes padding, 4 bytes for int
            hex_data = "12" + "00"*3 + "01000000"  # a=0x12, b=1
            parsed_values = self.model.parse_hex_data(hex_data, 'little')
            
            self.assertEqual(len(parsed_values), 3)  # 2 members + 1 padding
            
            # Check char member
            self.assertEqual(parsed_values[0]["name"], "a")
            self.assertEqual(parsed_values[0]["value"], "18")  # 0x12 = 18
            self.assertEqual(parsed_values[0]["hex_raw"], "12")
            
            # Check padding
            self.assertEqual(parsed_values[1]["name"], "(padding)")
            self.assertEqual(parsed_values[1]["value"], "-")
            
            # Check int member
            self.assertEqual(parsed_values[2]["name"], "b")
            self.assertEqual(parsed_values[2]["value"], "1")
            
        finally:
            os.unlink(file_path)
    
    def test_parse_hex_data_big_endian(self):
        """Test parsing hex data with big endian byte order."""
        # Load a struct with multiple fields
        content = """
        struct EndianStruct {
            char a;
            int b;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        
        try:
            self.model.load_struct_from_file(file_path)
            
            # Parse hex data with big endian
            hex_data = "12345678"  # 4 bytes for int
            parsed_values = self.model.parse_hex_data(hex_data, 'big')
            
            # Check int member (big endian)
            int_member = next(item for item in parsed_values if item["name"] == "b")
            self.assertEqual(int_member["value"], "305419896")  # 0x12345678
            
        finally:
            os.unlink(file_path)
    
    def test_parse_hex_data_bitfields(self):
        """Test parsing hex data for struct with bit fields."""
        # Load a struct with bit fields
        content = """
        struct BitFieldStruct {
            int a : 1;
            int b : 2;
            char c;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        try:
            self.model.load_struct_from_file(file_path)
            # 動態取得 layout offset/size
            layout = self.model.layout
            # 找出 bitfield storage unit offset/size
            a_layout = next(item for item in layout if item["name"] == "a")
            c_layout = next(item for item in layout if item["name"] == "c")
            total_size = self.model.total_size
            # 準備全 0
            hex_bytes = bytearray(total_size)
            # bitfield storage unit: 設定 offset 處 0x07
            hex_bytes[a_layout["offset"]:a_layout["offset"]+a_layout["size"]] = bytes([0x07] + [0x00]*(a_layout["size"]-1))
            # char c: 設定 offset 處 0xff
            hex_bytes[c_layout["offset"]] = 0xff
            hex_data = hex_bytes.hex()
            parsed_values = self.model.parse_hex_data(hex_data, 'little')
            a_member = next(item for item in parsed_values if item["name"] == "a")
            b_member = next(item for item in parsed_values if item["name"] == "b")
            c_member = next(item for item in parsed_values if item["name"] == "c")
            self.assertEqual(a_member["value"], "1")
            self.assertEqual(b_member["value"], "3")
            self.assertEqual(c_member["value"], "255")
        finally:
            os.unlink(file_path)
    
    def test_parse_hex_data_bool(self):
        """Test parsing boolean values."""
        # Load a struct with bool field
        content = """
        struct BoolStruct {
            bool flag;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        
        try:
            self.model.load_struct_from_file(file_path)
            
            # Parse hex data
            parsed_values = self.model.parse_hex_data("01", 'little')
            self.assertEqual(parsed_values[0]["value"], "True")
            
            parsed_values = self.model.parse_hex_data("00", 'little')
            self.assertEqual(parsed_values[0]["value"], "False")
            
        finally:
            os.unlink(file_path)
    
    def test_parse_hex_data_pointer(self):
        """Test parsing pointer values."""
        # Load a struct with pointer field
        content = """
        struct PointerStruct {
            int* ptr;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        
        try:
            self.model.load_struct_from_file(file_path)
            
            # Parse hex data
            hex_data = "123456789ABCDEF0"  # 8 bytes for pointer
            parsed_values = self.model.parse_hex_data(hex_data, 'little')
            
            self.assertEqual(parsed_values[0]["name"], "ptr")
            # Pointer value should be parsed as integer
            self.assertIsInstance(int(parsed_values[0]["value"]), int)
            
        finally:
            os.unlink(file_path)

    def test_parse_hex_data_nested(self):
        """Test parsing hex data for nested structs."""
        content = '''
        struct Outer {
            int a;
            struct Inner {
                char b;
                int c;
            } inner;
        };
        '''
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        try:
            self.model.load_struct_from_file(file_path)
            hex_data = '010000004100000002000000'
            result = self.model.parse_hex_data(hex_data, 'little')
            names = [item['name'] for item in result]
            self.assertEqual(names, ['a', 'inner.b', '(padding)', 'inner.c'])
            values = [item['value'] for item in result if item['name'] != '(padding)']
            self.assertEqual(values, ['1', '65', '2'])
        finally:
            os.unlink(file_path)

    def test_parse_hex_data_nested_array(self):
        """Test parsing hex data for nested struct arrays."""
        content = '''
        struct Outer {
            int a;
            struct Inner {
                char b;
                int c;
            } inner_arr[2];
        };
        '''
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        try:
            self.model.load_struct_from_file(file_path)
            hex_data = '0100000041000000020000004200000003000000'
            result = self.model.parse_hex_data(hex_data, 'little')
            names = [item['name'] for item in result]
            self.assertEqual(
                names,
                [
                    'a',
                    'inner_arr[0].b',
                    '(padding)',
                    'inner_arr[0].c',
                    'inner_arr[1].b',
                    '(padding)',
                    'inner_arr[1].c',
                ],
            )
            values = [item['value'] for item in result if item['name'] != '(padding)']
            self.assertEqual(values, ['1', '65', '2', '66', '3'])
        finally:
            os.unlink(file_path)
    
    def test_parse_hex_data_padding(self):
        """Test parsing hex data with padding."""
        # Load a struct with padding
        content = """
        struct PaddingStruct {
            char a;
            int b;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        
        try:
            self.model.load_struct_from_file(file_path)
            
            # Parse hex data
            hex_data = "12345678"  # 4 bytes
            parsed_values = self.model.parse_hex_data(hex_data, 'little')
            
            # Should have padding entry
            padding_entries = [item for item in parsed_values if item["name"] == "(padding)"]
            self.assertGreater(len(padding_entries), 0)
            
            for padding in padding_entries:
                self.assertEqual(padding["value"], "-")
                self.assertIsInstance(padding["hex_raw"], str)
            
        finally:
            os.unlink(file_path)
    
    def test_parse_hex_data_short_input(self):
        """Test parsing hex data that's shorter than expected (should pad with zeros)."""
        # Load a struct
        content = """
        struct ShortStruct {
            int a;
            long long b;
        };
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.h') as f:
            f.write(content)
            file_path = f.name
        try:
            self.model.load_struct_from_file(file_path)
            layout = self.model.layout
            a_layout = next(item for item in layout if item["name"] == "a")
            b_layout = next(item for item in layout if item["name"] == "b")
            total_size = self.model.total_size
            hex_bytes = bytearray(total_size)
            # int a: 設定 offset 處 0x12
            hex_bytes[a_layout["offset"]] = 0x12
            # long long b: 設定 offset 處 0x34
            hex_bytes[b_layout["offset"]] = 0x34
            hex_data = hex_bytes.hex()
            parsed_values = self.model.parse_hex_data(hex_data, 'little')
            int_member = next(item for item in parsed_values if item["name"] == "a")
            self.assertEqual(int_member["value"], str(0x12))
        finally:
            os.unlink(file_path)
    
    def test_parse_hex_data_no_layout(self):
        """Test parsing hex data without loading struct layout first."""
        with self.assertRaises(ValueError):
            self.model.parse_hex_data("1234", 'little')
    
    def test_hex_raw_formatting_and_padding(self):
        """Test that hex_raw is zero-padded and can be safely prefixed with 0x for display."""
        # Load a simple struct
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
            
            # Parse hex data
            hex_data = "12"
            parsed_values = self.model.parse_hex_data(hex_data, 'little')
            
            # Check hex_raw formatting
            for item in parsed_values:
                if item["name"] != "(padding)":
                    hex_raw = item["hex_raw"]
                    # Should be even length (each byte = 2 hex chars)
                    self.assertEqual(len(hex_raw) % 2, 0)
                    # Should be valid hex
                    int(hex_raw, 16)  # Should not raise ValueError
                    # Should be zero-padded to correct size
                    # Find the corresponding layout item to get size
                    layout_item = next((layout_item for layout_item in self.model.layout if layout_item["name"] == item["name"]), None)
                    if layout_item:
                        expected_size = layout_item["size"] * 2
                        self.assertEqual(len(hex_raw), expected_size)
            
        finally:
            os.unlink(file_path)


if __name__ == '__main__':
    unittest.main() 