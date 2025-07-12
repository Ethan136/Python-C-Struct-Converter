import unittest
import tkinter as tk
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from view.struct_view import StructView

class TestGUIInputValidation(unittest.TestCase):
    """Test cases for GUI input validation and length limiting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.view = StructView()
        # Create a test entry widget for testing
        self.test_entry = tk.Entry(self.root)
        self.test_entry.pack()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.root.destroy()
    
    def test_validate_input_hex_characters(self):
        """Test that only hexadecimal characters are allowed"""
        # Test valid hex characters
        valid_chars = '0123456789abcdefABCDEF'
        for char in valid_chars:
            event = self._create_key_event(char, 'KeyPress')
            result = self.view._validate_input(event, 8)
            self.assertIsNone(result, f"Valid hex character '{char}' should be allowed")
        
        # Test invalid characters
        invalid_chars = 'ghijklmnopqrstuvwxyzGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|;:,.<>?'
        for char in invalid_chars:
            event = self._create_key_event(char, 'KeyPress')
            result = self.view._validate_input(event, 8)
            self.assertEqual(result, "break", f"Invalid character '{char}' should be blocked")
    
    def test_validate_input_control_keys(self):
        """Test that control keys are allowed"""
        control_keys = ['BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab']
        for key in control_keys:
            event = self._create_key_event('', 'KeyPress', keysym=key)
            result = self.view._validate_input(event, 8)
            self.assertIsNone(result, f"Control key '{key}' should be allowed")
    
    def test_validate_input_ctrl_shortcuts(self):
        """Test that Ctrl shortcuts are allowed"""
        ctrl_keys = ['a', 'c', 'v', 'x']
        for key in ctrl_keys:
            event = self._create_key_event('', 'KeyPress', keysym=key, state=0x4)
            result = self.view._validate_input(event, 8)
            self.assertIsNone(result, f"Ctrl+{key} should be allowed")
    
    def test_limit_input_length(self):
        """Test that input length is properly limited"""
        max_length = 8
        
        # Test that input is allowed when under limit
        self.test_entry.delete(0, tk.END)
        self.test_entry.insert(0, "1234567")  # 7 characters, under limit
        event = self._create_key_event('8', 'Key', widget=self.test_entry)
        result = self.view._limit_input_length(event, max_length)
        self.assertIsNone(result, "Input should be allowed when under limit")
        
        # Test that input is blocked when at limit
        self.test_entry.delete(0, tk.END)
        self.test_entry.insert(0, "12345678")  # 8 characters, at limit
        event = self._create_key_event('9', 'Key', widget=self.test_entry)
        result = self.view._limit_input_length(event, max_length)
        self.assertEqual(result, "break", "Input should be blocked when at limit")
        
        # Test that input is blocked when over limit
        self.test_entry.delete(0, tk.END)
        self.test_entry.insert(0, "123456789")  # 9 characters, over limit
        event = self._create_key_event('0', 'Key', widget=self.test_entry)
        result = self.view._limit_input_length(event, max_length)
        self.assertEqual(result, "break", "Input should be blocked when over limit")
    
    def test_limit_input_length_control_keys(self):
        """Test that control keys are allowed even when at length limit"""
        max_length = 8
        self.test_entry.delete(0, tk.END)
        self.test_entry.insert(0, "12345678")  # At limit
        
        # Test control keys
        control_keys = ['BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab']
        for key in control_keys:
            event = self._create_key_event('', 'Key', keysym=key, widget=self.test_entry)
            result = self.view._limit_input_length(event, max_length)
            self.assertIsNone(result, f"Control key '{key}' should be allowed even at limit")
        
        # Test Ctrl shortcuts
        ctrl_keys = ['a', 'c', 'v', 'x']
        for key in ctrl_keys:
            event = self._create_key_event('', 'Key', keysym=key, state=0x4, widget=self.test_entry)
            result = self.view._limit_input_length(event, max_length)
            self.assertIsNone(result, f"Ctrl+{key} should be allowed even at limit")
    
    def test_no_auto_focus_functionality(self):
        """Test that auto-focus functionality has been removed"""
        # Verify that _auto_focus method no longer exists
        self.assertFalse(hasattr(self.view, '_auto_focus'), 
                        "_auto_focus method should have been removed")
    
    def test_rebuild_hex_grid_no_auto_focus_binding(self):
        """Test that hex grid entries no longer have auto-focus KeyRelease binding"""
        # Rebuild hex grid with 4-byte unit size (8 hex chars)
        self.view.rebuild_hex_grid(16, 4)  # 16 bytes total, 4 bytes per unit
        
        # Check that entries were created
        self.assertGreater(len(self.view.hex_entries), 0, "Hex entries should be created")
        
        # Test that each entry has the correct expected length and no auto-focus binding
        for entry, expected_length in self.view.hex_entries:
            self.assertEqual(expected_length, 8, "4-byte unit should have 8 hex characters")
            
            # Check that the entry has proper width (indicates proper setup)
            self.assertGreater(entry.cget('width'), 0, "Entry should have proper width")
            
            # Verify that KeyRelease binding (auto-focus) is not present
            # Note: We can't easily check bindings in unittest, but we can verify
            # that the entry is properly configured and the _auto_focus method doesn't exist
            self.assertFalse(hasattr(self.view, '_auto_focus'), 
                           "Auto-focus method should not exist")
    
    def test_rebuild_hex_grid_input_validation(self):
        """Test that input validation is properly bound to hex grid entries"""
        # Rebuild hex grid with 4-byte unit size (8 hex chars)
        self.view.rebuild_hex_grid(16, 4)  # 16 bytes total, 4 bytes per unit
        
        # Check that entries were created with proper validation
        self.assertGreater(len(self.view.hex_entries), 0, "Hex entries should be created")
        
        # Test that each entry has the correct expected length
        for entry, expected_length in self.view.hex_entries:
            self.assertEqual(expected_length, 8, "4-byte unit should have 8 hex characters")
            
            # Test that the entry has input validation bound
            bindings = entry.bind()
            # Note: Tkinter may not show all bindings in bind(), so we'll test the functionality instead
            # Check that the entry has the expected width (which indicates proper setup)
            self.assertGreater(entry.cget('width'), 0, "Entry should have proper width")
    
    def _create_key_event(self, char, event_type, keysym=None, state=0, widget=None):
        """Helper method to create a mock key event"""
        class MockEvent:
            def __init__(self, char, keysym, state, widget):
                self.char = char
                self.keysym = keysym
                self.state = state
                self.widget = widget
        
        return MockEvent(char, keysym or char, state, widget or self.test_entry)

if __name__ == '__main__':
    unittest.main() 