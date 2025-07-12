"""
Input Field Processor Module

This module is responsible for processing user input field values in the C++ Struct Memory Parser.
It handles automatic left zero padding, endianness conversion, and raw byte data generation.
"""

class InputFieldProcessor:
    """
    Processes user input field values for struct parsing.
    
    This class provides functionality for:
    1. Automatic left zero padding
    2. Endianness conversion
    3. Raw byte data generation
    """
    
    def __init__(self):
        """Initialize the InputFieldProcessor."""
        # Supported byte sizes for individual field processing (most common cases)
        self.supported_byte_sizes = {1, 4, 8}
        # Supported endianness values
        self.supported_endianness = {'little', 'big'}
    
    def pad_hex_input(self, input_value, byte_size):
        """
        Automatically pad hex input with leading zeros.
        
        Args:
            input_value (str): User input hex string (can be empty)
            byte_size (int): Target byte size (any positive integer)
            
        Returns:
            str: Padded hex string
            
        Raises:
            ValueError: If byte_size is not positive
            
        Examples:
            >>> processor = InputFieldProcessor()
            >>> processor.pad_hex_input("12", 4)
            '00000012'
            >>> processor.pad_hex_input("123", 8)
            '0000000000000123'
            >>> processor.pad_hex_input("1", 1)
            '01'
            >>> processor.pad_hex_input("", 4)
            '00000000'
            >>> processor.pad_hex_input("1234", 16)
            '00000000000000000000000000001234'
        """
        # Validate byte size
        if byte_size <= 0:
            raise ValueError(f"Byte size must be positive, got: {byte_size}")
        
        # Handle empty input - treat as all zeros
        if not input_value:
            return "0" * (byte_size * 2)
        
        # Normalize input to lowercase
        input_value = input_value.lower()
        
        # Calculate required hex characters for the byte size
        required_chars = byte_size * 2
        
        # Pad with leading zeros if input is shorter than required
        padded_hex = input_value.zfill(required_chars)
        
        return padded_hex
    
    def convert_to_raw_bytes(self, padded_hex, byte_size, endianness):
        """
        Convert padded hex to raw byte data with endianness.
        
        Args:
            padded_hex (str): Padded hex string (must be correct length for byte_size)
            byte_size (int): Byte size (any positive integer)
            endianness (str): 'little' or 'big'
            
        Returns:
            bytes: Raw byte data
            
        Raises:
            ValueError: If endianness is not supported or hex string is invalid
            OverflowError: If hex value is too large for the byte size
            
        Examples:
            >>> processor = InputFieldProcessor()
            >>> processor.convert_to_raw_bytes("00000012", 4, 'big')
            b'\\x00\\x00\\x00\\x12'
            >>> processor.convert_to_raw_bytes("00000012", 4, 'little')
            b'\\x12\\x00\\x00\\x00'
            >>> processor.convert_to_raw_bytes("01", 1, 'big')
            b'\\x01'
        """
        # Validate endianness
        if endianness not in self.supported_endianness:
            raise ValueError(f"Unsupported endianness: {endianness}. Supported values: {self.supported_endianness}")
        
        # Validate byte size
        if byte_size <= 0:
            raise ValueError(f"Byte size must be positive, got: {byte_size}")
        
        # Validate hex string length
        expected_length = byte_size * 2
        if len(padded_hex) != expected_length:
            raise ValueError(f"Hex string length mismatch: expected {expected_length} characters, got {len(padded_hex)}")
        
        try:
            # Parse hex string to integer
            int_value = int(padded_hex, 16)
            
            # Convert to bytes with specified endianness
            raw_bytes = int_value.to_bytes(byte_size, byteorder=endianness)
            
            return raw_bytes
            
        except ValueError as e:
            # Re-raise with more descriptive message
            raise ValueError(f"Invalid hex string '{padded_hex}': {str(e)}")
        except OverflowError as e:
            # Re-raise with more descriptive message
            raise OverflowError(f"Hex value '{padded_hex}' is too large for {byte_size} bytes: {str(e)}")
    
    def process_input_field(self, input_value, byte_size, endianness):
        """
        Complete input processing pipeline.
        
        This function combines padding and conversion in a single call.
        
        Args:
            input_value (str): User input hex string (can be empty)
            byte_size (int): Target byte size (any positive integer)
            endianness (str): 'little' or 'big'
            
        Returns:
            bytes: Raw byte data ready for struct parsing
            
        Raises:
            ValueError: If parameters are invalid
            OverflowError: If hex value is too large for the byte size
            
        Examples:
            >>> processor = InputFieldProcessor()
            >>> processor.process_input_field("12", 4, 'big')
            b'\\x00\\x00\\x00\\x12'
            >>> processor.process_input_field("12", 4, 'little')
            b'\\x12\\x00\\x00\\x00'
            >>> processor.process_input_field("123", 8, 'big')
            b'\\x00\\x00\\x00\\x00\\x00\\x00\\x01#'
            >>> processor.process_input_field("", 4, 'big')
            b'\\x00\\x00\\x00\\x00'
        """
        # Step 1: Pad the input with zeros
        padded_hex = self.pad_hex_input(input_value, byte_size)
        
        # Step 2: Convert to raw bytes with endianness
        raw_bytes = self.convert_to_raw_bytes(padded_hex, byte_size, endianness)
        
        return raw_bytes
    
    def is_supported_field_size(self, byte_size):
        """
        Check if a byte size is in the commonly supported set (1, 4, 8).
        
        Args:
            byte_size (int): Byte size to check
            
        Returns:
            bool: True if byte_size is 1, 4, or 8
            
        Examples:
            >>> processor = InputFieldProcessor()
            >>> processor.is_supported_field_size(4)
            True
            >>> processor.is_supported_field_size(2)
            False
        """
        return byte_size in self.supported_byte_sizes 