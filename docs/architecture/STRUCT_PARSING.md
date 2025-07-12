# C++ Struct Parsing Mechanism

This document explains how `struct_model.py` parses a C++ `struct` and computes its memory layout.

## Overview
- The parser is implemented in `src/model/struct_model.py`.
- Only `struct` definitions are supported; `union` parsing is not implemented.

## Steps
1. **Regex Extraction (Intermediate Representation)**
   - `parse_struct_definition()` first extracts member types and names into a temporary list of tuples. For example, `struct { char s; long long val; }` becomes `[('char', 's'), ('long long', 'val')]`. This provides a simple, intermediate representation.

2. **Layout Calculation (Final Data Structure)**
   - The intermediate list is processed by `calculate_layout()`, which computes the final memory layout.
   - This final layout is stored as a **list of dictionaries**, where each dictionary represents a single member, including padding. This structure is the definitive representation of the struct's memory map.

### Final Data Structure Details

When parsing is complete, the information for each struct member (including padding) is stored in a **dictionary**. The entire struct layout is represented by a **list of these dictionaries**, which is stored in the `StructModel`'s `self.layout` attribute.

For example, `struct UserProfile { char status; long long user_id; };` is converted into:
```python
[
    {
        "name": "status",
        "type": "char",
        "size": 1,
        "offset": 0
    },
    {
        "name": "(padding)",
        "type": "padding",
        "size": 7,
        "offset": 1
    },
    {
        "name": "user_id",
        "type": "long long",
        "size": 8,
        "offset": 8
    }
]
```

#### Rationale for this Structure

- **Clarity and Readability**: Using dictionaries with keys like `"name"` and `"size"` makes the code self-documenting and easier to maintain than using tuple indices.
- **Completeness**: The structure contains all necessary information for subsequent operations: `name` (for UI display), `type` (for type-specific logic), `size` (for slicing hex data), and `offset` (for locating the member in memory).
- **Accurate Memory Representation**: Explicitly including `padding` as a distinct member type creates a precise map of the struct's memory layout, simplifying the parsing of raw hex data.
- **Extensibility**: Adding new properties to a member in the future (e.g., `is_unsigned: True`) only requires adding a new key-value pair to the dictionary, ensuring backward compatibility.

3. **Hex Data Parsing**
   - `parse_hex_data()` uses the final layout structure (`self.layout`) to interpret raw hexadecimal input.
   - It iterates through the list, using each member's `offset` and `size` to slice the byte string correctly.
   - The bytes for each member are then converted to a value using the user-specified endianness.

## Extending for `union`
The current implementation does not recognize `union` definitions. To add support, a new parsing branch would need to detect `union` keywords and adjust layout logic so that all members share offset `0` and the total size equals the largest member.

## Struct Member Value Storage in Memory

When a struct is instantiated in memory, each member's value is stored according to the computed layout, which is determined by the member's type, size, alignment, and any necessary padding for alignment.

### Storage Principles
- **Offset & Size**: Each member occupies a contiguous region of memory, starting at its computed `offset` and spanning `size` bytes, as determined by the layout calculation.
- **Padding**: If required by alignment rules, padding bytes are inserted between members. These bytes are not associated with any member and are typically set to zero or left uninitialized.
- **Order**: Members are stored in the order they are declared in the struct, with padding inserted as needed to satisfy alignment constraints.
- **Endianness**: The byte order (little-endian or big-endian) affects how multi-byte values (e.g., `int`, `long long`) are represented in memory, but does not affect the layout offsets or sizes.

### Example
Given the struct:
```c
struct Example {
    char  a;      // 1 byte
    int   b;      // 4 bytes
    short c;      // 2 bytes
};
```
On a typical 64-bit system with 4-byte alignment for `int`:
- `a` is at offset 0 (1 byte)
- 3 bytes of padding (offsets 1-3)
- `b` is at offset 4 (4 bytes)
- `c` is at offset 8 (2 bytes)
- 2 bytes of final padding (offsets 10-11) to align the struct size to a multiple of the largest alignment (4 bytes)

The memory layout (in bytes):
```
Offset:  0   1   2   3   4   5   6   7   8   9  10  11
        [a][pad][pad][pad][  b  ][  b  ][  b  ][  b  ][ c ][ c ][pad][pad]
```

### Value Storage
- Each member's value is stored in its designated region (offset, size) in the struct's memory block.
- For example, if `a = 0x12`, `b = 0x34567890`, `c = 0x9abc`, and using little-endian:
  - Memory bytes: `12 00 00 00 90 78 56 34 bc 9a 00 00`
- The value of each member can be extracted by slicing the struct's memory block at the member's offset and size, then interpreting the bytes according to the member's type and the system's endianness.

### Summary
- The struct's memory is a contiguous block, with each member occupying a specific region defined by the layout.
- Padding ensures correct alignment but does not store member values.
- The value of each member is stored as raw bytes at its offset, and can be read/written by slicing the memory block accordingly.
