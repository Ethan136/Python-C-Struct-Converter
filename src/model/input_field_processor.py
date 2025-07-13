"""
Input Field Processor Module

This module is responsible for processing user input field values in the C++ Struct Memory Parser.
It handles automatic left zero padding, endianness conversion, and raw byte data generation.
"""

class InputFieldProcessor:
    """
    Processes user input field values for struct parsing.
    
    以『數值語意』為核心：
    1. 將 input_value 當作 hex 數值解析
    2. 用 to_bytes(byte_size, endianness) 產生 bytes
    3. 回傳 bytes
    """
    def __init__(self):
        self.supported_byte_sizes = {1, 4, 8}
        self.supported_endianness = {'little', 'big'}

    def process_input_field(self, input_value, byte_size, endianness):
        """
        將 input_value 當作 hex 數值，依據 byte_size 與 endianness 產生 bytes。
        Args:
            input_value (str): User input hex string (可為空)
            byte_size (int): 欄位 bytes 數
            endianness (str): 'little' 或 'big'
        Returns:
            bytes: struct 欄位的原始 bytes
        """
        if byte_size <= 0:
            raise ValueError(f"Byte size must be positive, got: {byte_size}")
        if endianness not in self.supported_endianness:
            raise ValueError(f"Unsupported endianness: {endianness}")
        value = int(input_value, 16) if input_value else 0
        try:
            return value.to_bytes(byte_size, endianness)
        except OverflowError as e:
            raise OverflowError(f"Value {value} too large for {byte_size} bytes: {e}")
    
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