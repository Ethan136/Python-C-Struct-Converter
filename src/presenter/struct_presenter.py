import re
from tkinter import filedialog
from config import get_string

class StructPresenter:
    def __init__(self, model, view=None):
        self.model = model
        self.view = view # This will be set by main.py after view is instantiated

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
        debug_bytes_per_box = []  # 新增：收集每個 box 的 bytes
        for raw_part, expected_chars_in_box in hex_parts_with_expected_len:
            # Validate input is hex
            if not re.match(r"^[0-9a-fA-F]*$", raw_part):
                self.view.show_error(get_string("dialog_invalid_input"),
                                   f"Input '{raw_part}' contains non-hexadecimal characters.")
                return
            
            # Convert raw_part to integer value
            try:
                # Handle empty string as 0
                int_value = int(raw_part, 16) if raw_part else 0
            except ValueError:
                self.view.show_error(get_string("dialog_invalid_input"),
                                   f"Could not convert '{raw_part}' to a number.")
                return

            # Determine the byte size of the current input chunk (e.g., 1, 4, or 8 bytes)
            chunk_byte_size = expected_chars_in_box // 2

            # Convert integer value to bytes using the selected endianness
            try:
                # Ensure the value fits within the chunk_byte_size
                # Max value for N bytes is (2**(N*8)) - 1
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
        # 依照 unit size 決定每行顯示幾個 byte
        unit_size = self.view.get_selected_unit_size()
        debug_lines = []
        current_line = []
        for i, chunk_bytes in enumerate(debug_bytes_per_box):
            # 逐 byte 轉成 2位小寫 hex
            for b in chunk_bytes:
                current_line.append(f"{b:02x}")
                if len(current_line) == unit_size:
                    debug_lines.append(" ".join(current_line))
                    current_line = []
        if current_line:
            debug_lines.append(" ".join(current_line))
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
        except Exception as e:
            self.view.show_error(get_string("dialog_parsing_error"),
                               f"An error occurred during parsing: {e}")