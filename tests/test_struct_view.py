import unittest
from unittest.mock import Mock, patch
import tkinter as tk
from src.view.struct_view import StructView
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

class TestStructView(unittest.TestCase):

    def setUp(self):
        """Set up the test environment before each test."""
        # Create a root window but don't run the mainloop
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        self.mock_presenter = Mock()
        self.view = StructView()
        self.view.set_presenter(self.mock_presenter)

    def tearDown(self):
        """Clean up the test environment after each test."""
        self.root.destroy()

    def test_view_initialization(self):
        """Test that all UI components are initialized."""
        self.assertIsNotNone(self.view.file_label)
        self.assertIsNotNone(self.view.browse_button)
        self.assertIsNotNone(self.view.info_text)
        self.assertIsNotNone(self.view.unit_size_var)
        self.assertIsNotNone(self.view.endian_var)
        self.assertIsNotNone(self.view.hex_grid_frame)
        self.assertIsNotNone(self.view.debug_text)
        self.assertIsNotNone(self.view.parse_button)
        self.assertIsNotNone(self.view.result_text)

    def test_presenter_wiring(self):
        """Test that buttons and commands are correctly wired to the presenter's methods."""
        # We need a fresh view and presenter for this test
        view = StructView()
        mock_presenter = Mock()
        view.set_presenter(mock_presenter)

        # Simulate button clicks by invoking them
        view.browse_button.invoke()

        # The parse button is disabled by default, so we must enable it to test it.
        view.parse_button.config(state=tk.NORMAL)
        view.parse_button.invoke()

        # Assert that the correct presenter methods were called
        mock_presenter.browse_file.assert_called_once()
        mock_presenter.parse_hex_data.assert_called_once()

        # Test the OptionMenu dispatchers by calling them directly
        view._dispatch_on_unit_size_change("4 Bytes")
        mock_presenter.on_unit_size_change.assert_called_once_with("4 Bytes")

        view._dispatch_on_endianness_change("Big Endian")
        mock_presenter.on_endianness_change.assert_called_once_with("Big Endian")

    def test_show_file_path(self):
        """Test that the file path is displayed correctly."""
        test_path = "/path/to/some/file.h"
        self.view.show_file_path(test_path)
        self.assertEqual(self.view.file_label.cget("text"), test_path)

    @patch('tkinter.messagebox.showerror')
    def test_show_error(self, mock_showerror):
        """Test that show_error calls tkinter.messagebox.showerror."""
        error_title = "Error"
        error_message = "This is a test error."
        self.view.show_error(error_title, error_message)
        mock_showerror.assert_called_once_with(error_title, error_message)

    def test_show_struct_layout_bitfield(self):
        """Test that struct layout display includes bit field info for bitfield members."""
        struct_name = "BitFieldStruct"
        layout = [
            {"name": "a", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 0, "bit_size": 1},
            {"name": "b", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 1, "bit_size": 2},
            {"name": "c", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 3, "bit_size": 5},
        ]
        total_size = 4
        struct_align = 4
        self.view.show_struct_layout(struct_name, layout, total_size, struct_align)
        text = self.view.info_text.get("1.0", "end")
        # 應該包含 bit_offset, bit_size, is_bitfield 關鍵字或數值
        self.assertIn("bit_offset", text)
        self.assertIn("bit_size", text)
        self.assertIn("is_bitfield", text)

    def test_show_parsed_values_bitfield(self):
        """Test that parsed values display bit field info for bitfield members."""
        parsed_values = [
            {"name": "a", "value": "1", "hex_raw": "01"},
            {"name": "b", "value": "2", "hex_raw": "02"},
            {"name": "c", "value": "17", "hex_raw": "11"},
        ]
        # layout info for bitfield
        self.view.model = Mock()
        self.view.model.layout = [
            {"name": "a", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 0, "bit_size": 1},
            {"name": "b", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 1, "bit_size": 2},
            {"name": "c", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 3, "bit_size": 5},
        ]
        self.view.show_parsed_values(parsed_values, "Little Endian")
        text = self.view.result_text.get("1.0", "end")
        # 應該包含完整 bitfield 標示
        self.assertIn("[bitfield bit_offset=0 bit_size=1]", text)
        self.assertIn("[bitfield bit_offset=1 bit_size=2]", text)
        self.assertIn("[bitfield bit_offset=3 bit_size=5]", text)

    def test_show_struct_member_debug_bitfield(self):
        """Test that struct member debug info includes bit field info for bitfield members."""
        parsed_values = [
            {"name": "a", "value": "1", "hex_raw": "01"},
            {"name": "b", "value": "2", "hex_raw": "02"},
            {"name": "c", "value": "17", "hex_raw": "11"},
        ]
        layout = [
            {"name": "a", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 0, "bit_size": 1},
            {"name": "b", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 1, "bit_size": 2},
            {"name": "c", "type": "int", "size": 4, "offset": 0, "is_bitfield": True, "bit_offset": 3, "bit_size": 5},
        ]
        self.view.show_struct_member_debug(parsed_values, layout)
        text = self.view.debug_result_text.get("1.0", "end")
        # 應該包含 bit_offset, bit_size, is_bitfield
        self.assertIn("bit_offset=0", text)
        self.assertIn("bit_size=1", text)
        self.assertIn("is_bitfield=True", text)

if __name__ == '__main__':
    unittest.main()
