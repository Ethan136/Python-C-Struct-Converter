import re
import tkinter as tk
from tkinter import filedialog
from config import get_string
from model.input_field_processor import InputFieldProcessor
import time


class HexProcessingError(Exception):
    """Custom exception for hex part processing errors."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind

class StructPresenter:
    def __init__(self, model, view=None):
        self.model = model
        self.view = view # This will be set by main.py after view is instantiated
        self.input_processor = InputFieldProcessor()
        self._layout_cache = {}  # (members_key, total_size) -> layout
        self._cache_hits = 0
        self._cache_misses = 0
        self._last_layout_time = None

    def invalidate_cache(self):
        self._layout_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def _make_cache_key(self, members, total_size):
        key = tuple(sorted((
            m.get('name', '<invalid>'),
            m.get('type', '<invalid>'),
            m.get('bit_size', 0)
        ) for m in members))
        return (key, total_size)

    def _process_hex_parts(self, hex_parts, byte_order):
        """Convert list of hex input parts to a hex string and debug lines."""
        final_hex_parts = []
        debug_bytes = []

        for raw_part, expected_chars in hex_parts:
            if not re.match(r"^[0-9a-fA-F]*$", raw_part):
                raise HexProcessingError(
                    "invalid_input",
                    f"Input '{raw_part}' contains non-hexadecimal characters."
                )

            chunk_byte_size = expected_chars // 2

            try:
                # 新版：直接用 process_input_field 產生 bytes
                bytes_for_chunk = self.input_processor.process_input_field(raw_part, chunk_byte_size, byte_order)
                int_value = int.from_bytes(bytes_for_chunk, byte_order)
            except ValueError:
                raise HexProcessingError(
                    "invalid_input",
                    f"Could not convert '{raw_part}' to a number."
                )
            except OverflowError:
                raise HexProcessingError(
                    "value_too_large",
                    f"Value 0x{raw_part} is too large for a {chunk_byte_size}-byte field."
                )

            final_hex_parts.append(bytes_for_chunk.hex())
            debug_bytes.append(bytes_for_chunk)

        debug_lines = []
        for i, chunk in enumerate(debug_bytes):
            hex_chars = [f"{b:02x}" for b in chunk]
            debug_lines.append(f"Box {i+1} ({len(chunk)} bytes): {' '.join(hex_chars)}")

        return "".join(final_hex_parts), debug_lines

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title=get_string("dialog_select_file"),
            filetypes=(("Header files", "*.h"), ("All files", "*.*" ))
        )
        if not file_path:
            return

        try:
            # 讀取原始 struct 檔案內容，傳給 debug 區
            with open(file_path, 'r') as f:
                struct_content = f.read()
            struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(file_path)
            self.view.show_file_path(file_path)
            self.view.show_struct_layout(struct_name, layout, total_size, struct_align)
            self.view.show_struct_debug(struct_content)
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

        try:
            hex_data, debug_lines = self._process_hex_parts(hex_parts_with_expected_len, byte_order_for_conversion)
        except HexProcessingError as e:
            title_map = {
                "invalid_input": get_string("dialog_invalid_input"),
                "value_too_large": get_string("dialog_value_too_large"),
                "overflow_error": get_string("dialog_overflow_error"),
                "conversion_error": get_string("dialog_conversion_error"),
            }
            self.view.show_error(title_map.get(e.kind, "Error"), str(e))
            return

        self.view.show_debug_bytes(debug_lines)

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

    def validate_manual_struct(self, struct_data):
        return self.model.validate_manual_struct(struct_data["members"], struct_data["total_size"])

    def on_manual_struct_change(self, struct_data):
        errors = self.model.validate_manual_struct(struct_data["members"], struct_data["total_size"])
        self.view.show_manual_struct_validation(errors)

    def on_export_manual_struct(self):
        struct_data = self.view.get_manual_struct_definition()
        struct_name = struct_data.get("struct_name", "MyStruct")
        h_content = self.model.export_manual_struct_to_h(struct_name)
        self.view.show_exported_struct(h_content)

    def parse_manual_hex_data(self, hex_parts, struct_def, endian):
        """解析 MyStruct tab 的 hex 資料並顯示結果"""
        try:
            unit_size = self.view.get_selected_manual_unit_size()
            byte_order = 'little' if endian == "Little Endian" else 'big'

            hex_data, debug_lines = self._process_hex_parts(hex_parts, byte_order)
            self.view.show_manual_debug_bytes(debug_lines)

            self.model.set_manual_struct(struct_def['members'], struct_def['total_size'])
            layout = self.model.calculate_manual_layout(struct_def['members'], struct_def['total_size'])

            # 解析 hex 資料，統一用 parse_hex_data
            parsed_values = self.model.parse_hex_data(hex_data, byte_order, layout=layout, total_size=struct_def['total_size'])

            # 呼叫 view 的顯示方法
            self.view.show_manual_parsed_values(parsed_values, endian)

        except HexProcessingError as e:
            title_map = {
                "invalid_input": "無效輸入",
                "value_too_large": "數值過大",
                "overflow_error": "溢位錯誤",
                "conversion_error": "轉換錯誤",
            }
            self.view.show_error(title_map.get(e.kind, "錯誤"), str(e))

        except Exception as e:
            self.view.show_error("解析錯誤", f"解析 hex 資料時發生錯誤: {e}")
            # 清空顯示
            self.view.manual_member_tree.delete(*self.view.manual_member_tree.get_children())

    def compute_member_layout(self, members, total_size):
        """計算 struct member 的 layout，回傳 layout list，含 cache 機制。"""
        cache_key = self._make_cache_key(members, total_size)
        if cache_key in self._layout_cache:
            self._cache_hits += 1
            return self._layout_cache[cache_key]
        try:
            start = time.perf_counter()
            layout = self.model.calculate_manual_layout(members, total_size)
            elapsed = time.perf_counter() - start
            self._last_layout_time = elapsed
        except Exception:
            # 不記錄 miss，不快取
            raise
        self._layout_cache[cache_key] = layout
        self._cache_misses += 1
        return layout

    def get_last_layout_time(self):
        """回傳最近一次 layout 計算（非 cache）所花秒數（float）。"""
        return self._last_layout_time

    def get_cache_stats(self):
        """回傳 (hit, miss) 統計。"""
        return self._cache_hits, self._cache_misses

    def reset_cache_stats(self):
        self._cache_hits = 0
        self._cache_misses = 0

    def calculate_remaining_space(self, members, total_size):
        """計算剩餘可用空間（bits, bytes）。"""
        used_bits = self.model.calculate_used_bits(members)
        total_bits = total_size * 8
        remaining_bits = max(0, total_bits - used_bits)
        remaining_bytes = remaining_bits // 8
        return remaining_bits, remaining_bytes