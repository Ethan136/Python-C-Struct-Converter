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
    """Process user input field values for struct parsing.

    The processor provides the following helpers:
    1. ``pad_hex_input`` - automatically left pads hex strings.
    2. ``convert_to_raw_bytes`` - converts padded hex to bytes with
       the specified endianness.
    3. ``process_input_field`` - combines the above two steps.

    It supports the common byte sizes ``1``, ``4`` and ``8`` and the
    endianness values ``"little"`` and ``"big"``.
    """
    def __init__(self):
        self.supported_byte_sizes = {1, 4, 8}
        self.supported_endianness = {'little', 'big'}

    def pad_hex_input(self, input_value, byte_size):
        """Return ``input_value`` left padded with zeros for ``byte_size``.

        Parameters
        ----------
        input_value: str
            User provided hex string. May be empty.
        byte_size: int
            Target byte size. Must be positive.

        Returns
        -------
        str
            The padded hex string in lowercase.
        """
        if byte_size <= 0:
            raise ValueError(f"Byte size must be positive, got: {byte_size}")

        if not input_value:
            return "0" * (byte_size * 2)

        input_value = input_value.lower()
        required_chars = byte_size * 2
        return input_value.zfill(required_chars)

    def convert_to_raw_bytes(self, padded_hex, byte_size, endianness):
        """Convert ``padded_hex`` to bytes using ``endianness``."""
        if endianness not in self.supported_endianness:
            raise ValueError(
                f"Unsupported endianness: {endianness}. Supported values: {self.supported_endianness}"
            )
        if byte_size <= 0:
            raise ValueError(f"Byte size must be positive, got: {byte_size}")
        expected_length = byte_size * 2
        if len(padded_hex) != expected_length:
            raise ValueError(
                f"Hex string length mismatch: expected {expected_length} characters, got {len(padded_hex)}"
            )
        try:
            int_value = int(padded_hex, 16)
            return int_value.to_bytes(byte_size, byteorder=endianness)
        except ValueError as e:
            raise ValueError(f"Invalid hex string '{padded_hex}': {e}")
        except OverflowError as e:
            raise OverflowError(
                f"Hex value '{padded_hex}' is too large for {byte_size} bytes: {e}"
            )

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
        padded = self.pad_hex_input(input_value, byte_size)
        return self.convert_to_raw_bytes(padded, byte_size, endianness)
    
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

    # New flexible input wrapper (v26)
    def process_flexible_input(self, input_str, target_len):
        """
        Delegate flexible hex string parsing to flexible_bytes_parser.
        Args:
            input_str (str): Raw user input string (e.g., "0x01, 0x0203")
            target_len (int|None): Fixed length in bytes or None for variable.
        Returns:
            ParseResult: see flexible_bytes_parser.ParseResult
        """
        from . import flexible_bytes_parser as fbp
        return fbp.parse_flexible_input(input_str, target_len)
