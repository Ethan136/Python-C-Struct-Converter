"""
Input Field Processor Module

This module is responsible for processing user input field values in the C++ Struct Memory Parser.
It handles automatic left zero padding, endianness conversion, and raw byte data generation.

Example Usage:
    processor = InputFieldProcessor()
    # 將 '12' 補零為 4 bytes 並轉換為 little endian bytes
    bytes_data = processor.process_input_field('12', 4, 'little')
    # bytes_data == b'\x12\x00\x00\x00'
"""

class InputFieldProcessor:
    """
    Processes user input field values for struct parsing.
    
    支援機制：
    1. 自動左補零（如 4 bytes 欄位 '12' -> '00000012'）
    2. 依據 byte_size 及 endianness 產生原始 bytes
    3. 支援 1/4/8 bytes 欄位，big/little endian
    4. 空字串自動視為 0
    5. 超過欄位大小會拋出 OverflowError

    Methods:
        process_input_field(input_value, byte_size, endianness):
            將 input_value（hex 字串）補零並轉換為 bytes
        is_supported_field_size(byte_size):
            檢查是否為支援的欄位大小（1, 4, 8）
    """
    def __init__(self):
        self.supported_byte_sizes = {1, 4, 8}
        self.supported_endianness = {'little', 'big'}

    def process_input_field(self, input_value, byte_size, endianness):
        """
        將 input_value 當作 hex 數值，依據 byte_size 與 endianness 產生 bytes。
        Args:
            input_value (str): 使用者輸入的 hex 字串（可為空）
            byte_size (int): 欄位 bytes 數（1, 4, 8）
            endianness (str): 'little' 或 'big'
        Returns:
            bytes: struct 欄位的原始 bytes
        Raises:
            ValueError: byte_size 或 endianness 不合法
            OverflowError: 數值超過欄位可容納範圍
        Example:
            >>> processor = InputFieldProcessor()
            >>> processor.process_input_field('12', 4, 'little')
            b'\x12\x00\x00\x00'
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
        檢查 byte_size 是否為支援的欄位大小（1, 4, 8）。
        Args:
            byte_size (int): 欲檢查的 bytes 數
        Returns:
            bool: True 表示支援
        Example:
            >>> processor = InputFieldProcessor()
            >>> processor.is_supported_field_size(4)
            True
            >>> processor.is_supported_field_size(2)
            False
        """
        return byte_size in self.supported_byte_sizes 