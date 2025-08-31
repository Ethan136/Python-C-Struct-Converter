"""Shared column definitions for unified GUI and CSV export (V24)."""

# Keep the exact order in sync with GUI unified table
UNIFIED_LAYOUT_VALUE_COLUMNS = [
    "name",
    "type",
    "offset",
    "size",
    "bit_offset",
    "bit_size",
    "is_bitfield",
    "value",
    "hex_value",
    "hex_raw",
]

def get_unified_layout_value_columns():
    return list(UNIFIED_LAYOUT_VALUE_COLUMNS)

