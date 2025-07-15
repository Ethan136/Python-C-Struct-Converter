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
            return {'type': 'error', 'message': '未選擇檔案'}

        try:
            with open(file_path, 'r') as f:
                struct_content = f.read()
            struct_name, layout, total_size, struct_align = self.model.load_struct_from_file(file_path)
            return {
                'type': 'ok',
                'file_path': file_path,
                'struct_name': struct_name,
                'layout': layout,
                'total_size': total_size,
                'struct_align': struct_align,
                'struct_content': struct_content
            }
        except Exception as e:
            return {'type': 'error', 'message': f"載入檔案時發生錯誤: {e}"}

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
            return {'type': 'error', 'message': '尚未載入 struct 定義檔案'}

        hex_parts_with_expected_len = self.view.get_hex_input_parts()

        byte_order_str = self.view.get_selected_endianness()
        byte_order_for_conversion = 'little' if byte_order_str == "Little Endian" else 'big'

        try:
            hex_data, debug_lines = self._process_hex_parts(hex_parts_with_expected_len, byte_order_for_conversion)
        except HexProcessingError as e:
            title_map = {
                "invalid_input": "無效輸入",
                "value_too_large": "數值過大",
                "overflow_error": "溢位錯誤",
                "conversion_error": "轉換錯誤",
            }
            return {'type': 'error', 'message': f"{title_map.get(e.kind, '錯誤')}: {str(e)}"}

        if len(hex_data) > self.model.total_size * 2:
            return {'type': 'error', 'message': f"輸入資料長度 ({len(hex_data)}) 超過預期總大小 ({self.model.total_size * 2})"}

        try:
            parsed_values = self.model.parse_hex_data(hex_data, byte_order_for_conversion)
            return {'type': 'ok', 'debug_lines': debug_lines, 'parsed_values': parsed_values}
        except Exception as e:
            return {'type': 'error', 'message': f"解析 hex 資料時發生錯誤: {e}"}

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
        """解析 MyStruct tab 的 hex 資料，回傳 dict 結果，不操作 view"""
        try:
            unit_size = struct_def.get('unit_size')
            byte_order = 'little' if endian == "Little Endian" else 'big'

            hex_data, debug_lines = self._process_hex_parts(hex_parts, byte_order)

            self.model.set_manual_struct(struct_def['members'], struct_def['total_size'])
            layout = self.model.calculate_manual_layout(struct_def['members'], struct_def['total_size'])

            parsed_values = self.model.parse_hex_data(hex_data, byte_order, layout=layout, total_size=struct_def['total_size'])

            return {'type': 'ok', 'debug_lines': debug_lines, 'parsed_values': parsed_values}
        except HexProcessingError as e:
            title_map = {
                "invalid_input": "無效輸入",
                "value_too_large": "數值過大",
                "overflow_error": "溢位錯誤",
                "conversion_error": "轉換錯誤",
            }
            return {'type': 'error', 'message': f"{title_map.get(e.kind, '錯誤')}: {str(e)}"}
        except Exception as e:
            return {'type': 'error', 'message': f"解析 hex 資料時發生錯誤: {e}"}

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