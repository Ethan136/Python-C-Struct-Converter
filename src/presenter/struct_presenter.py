import re
from tkinter import filedialog
from config import get_string
from model.input_field_processor import InputFieldProcessor

class StructPresenter:
    def __init__(self, model, view=None):
        self.model = model
        self.view = view # This will be set by main.py after view is instantiated
        self.input_processor = InputFieldProcessor()

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title=get_string("dialog_select_file"),
            filetypes=(("Header files", "*.h"), ("All files", "*.*" ))
        )
        if not file_path:
            return

        try:
            struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(file_path)
            self.view.show_file_path(file_path)
            self.view.show_struct_layout(struct_name, layout, total_size, struct_align)
            self.view.enable_parse_button()
            self.view.clear_results()
            
            # Rebuild hex grid based on new struct size
            unit_size = self.view.get_selected_unit_size()
            self.view.rebuild_hex_grid(total_size, unit_size)

        except Exception as e:
            self.view.show_error(get_string("dialog_file_error"), f"An error occurred: {e}")
            self.view.disable_parse_button()
            self.view.clear_results()
            self.view.rebuild_hex_grid(0, 1) # Clear hex grid

    def on_unit_size_change(self, *args):
        # This method is called when the unit size dropdown changes
        if self.model.total_size > 0: # Only rebuild if a struct is loaded
            unit_size = self.view.get_selected_unit_size()
            self.view.rebuild_hex_grid(self.model.total_size, unit_size)

    def on_endianness_change(self, *args):
        # This method is called when the endianness dropdown changes
        # Trigger re-parsing with the new endianness
        self.parse_hex_data()

    def parse_hex_data(self):
        if not self.model.layout:
            self.view.show_warning(get_string("dialog_no_struct"),
                                   "Please load a struct definition file first.")
            return

        hex_parts_with_expected_len = self.view.get_hex_input_parts()
        
        # Determine the selected endianness for converting input values to bytes
        byte_order_str = self.view.get_selected_endianness()
        byte_order_for_conversion = 'little' if byte_order_str == "Little Endian" else 'big'

        final_memory_hex_parts = []
        debug_bytes_per_box = []  # 收集每個 box 的 bytes
        for raw_part, expected_chars_in_box in hex_parts_with_expected_len:
            # Validate input is hex
            if not re.match(r"^[0-9a-fA-F]*$", raw_part):
                self.view.show_error(get_string("dialog_invalid_input"),
                                   f"Input '{raw_part}' contains non-hexadecimal characters.")
                return
            
            # Determine the byte size of the current input chunk (e.g., 1, 4, or 8 bytes)
            chunk_byte_size = expected_chars_in_box // 2

            # 使用 InputFieldProcessor 進行左補0
            try:
                padded_hex = self.input_processor.pad_hex_input(raw_part, chunk_byte_size)
                int_value = int(padded_hex, 16) if padded_hex else 0
            except ValueError:
                self.view.show_error(get_string("dialog_invalid_input"),
                                   f"Could not convert '{raw_part}' to a number.")
                return

            # Convert integer value to bytes using the selected endianness
            try:
                max_val = (2**(chunk_byte_size * 8)) - 1
                if int_value > max_val:
                    self.view.show_error(get_string("dialog_value_too_large"),
                                       f"Value 0x{raw_part} is too large for a {chunk_byte_size}-byte field.")
                    return

                bytes_for_chunk = int_value.to_bytes(chunk_byte_size, byteorder=byte_order_for_conversion)
                final_memory_hex_parts.append(bytes_for_chunk.hex())
                debug_bytes_per_box.append(bytes_for_chunk)
            except OverflowError:
                self.view.show_error(get_string("dialog_overflow_error"),
                                   f"Value 0x{raw_part} is too large for a {chunk_byte_size}-byte field.")
                return
            except Exception as e:
                self.view.show_error(get_string("dialog_conversion_error"),
                                   f"Error converting value 0x{raw_part} to bytes: {e}")
                return

        # --- 新增：格式化 debug bytes 並顯示 ---
        # 根據每個 input 欄位的實際 byte 數來顯示
        debug_lines = []
        for i, chunk_bytes in enumerate(debug_bytes_per_box):
            # 將這個 chunk 的所有 bytes 轉成 hex 字串
            hex_chars = []
            for b in chunk_bytes:
                hex_chars.append(f"{b:02x}")
            debug_lines.append(f"Box {i+1} ({len(chunk_bytes)} bytes): {' '.join(hex_chars)}")
        self.view.show_debug_bytes(debug_lines)
        # --- end debug ---

        # Join all converted hex parts to form the complete hex_data string representing raw memory
        hex_data = "".join(final_memory_hex_parts)

        # The model's parse_hex_data will then use bytes.fromhex(hex_data) to get raw memory bytes.
        # The model's int.from_bytes will then interpret these raw memory bytes using the selected byte_order.
        # This ensures consistency: input value -> memory bytes (based on selected endian) -> parsed value (based on selected endian)

        # The model will handle padding if hex_data is shorter than total_size * 2
        # We only check if it's too long here
        if len(hex_data) > self.model.total_size * 2:
            self.view.show_error(get_string("dialog_invalid_length"),
                               f"Input data ({len(hex_data)} chars) is longer than the expected total size ({self.model.total_size * 2} chars).")
            return

        try:
            # Pass the selected byte_order_for_conversion to the model for final interpretation
            parsed_values = self.model.parse_hex_data(hex_data, byte_order_for_conversion)
            self.view.show_parsed_values(parsed_values, byte_order_str)
            
            # Show struct member debug information
            self.view.show_struct_member_debug(parsed_values, self.model.layout)
        except Exception as e:
            self.view.show_error(get_string("dialog_parsing_error"),
                               f"An error occurred during parsing: {e}")