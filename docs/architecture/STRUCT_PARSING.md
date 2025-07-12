# C++ Struct Parsing Mechanism

This document explains how `struct_model.py` parses a C++ `struct` and computes its memory layout.

## Overview
- The parser is implemented in `src/model/struct_model.py`.
- Only `struct` definitions are supported; `union` parsing is not implemented.

## Steps
1. **Regex Extraction**
   - `parse_struct_definition()` searches for a `struct` declaration using:
     ```python
     struct_match = re.search(r"struct\s+(\w+)\s*\{([^}]+)\};", file_content, re.DOTALL)
     ```
   - Member declarations are captured with:
     ```python
     member_matches = re.findall(r"\s*([\w\s\*]+?)\s+([\w\[\]]+);", struct_content)
     ```
   - Types containing `*` are treated as pointers; otherwise they must exist in the `TYPE_INFO` table.
2. **Layout Calculation**
   - `calculate_layout()` iterates over the member list to compute offsets and padding.
   - Built‑in type size and alignment are defined in `TYPE_INFO`:
     ```python
     TYPE_INFO = {
         "char": {"size": 1, "align": 1},
         ...
         "pointer": {"size": 8, "align": 8}
     }
     ```
   - For each member:
     - Padding is inserted so the offset respects the member's alignment.
     - The member entry is added with its calculated offset and size.
   - After processing all members, final padding aligns the whole struct to its maximum alignment.
3. **Hex Data Parsing**
   - `parse_hex_data()` reads raw hexadecimal input, pads it to the struct's total size, and converts slices according to the layout.
   - Each member's bytes are converted using `int.from_bytes` with the user‑specified endianness.
   - Padding regions are reported with `"-"` for the value field.

## Extending for `union`
The current implementation does not recognize `union` definitions. To add support, a new parsing branch would need to detect `union` keywords and adjust layout logic so that all members share offset `0` and the total size equals the largest member.
