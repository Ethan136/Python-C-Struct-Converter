# C++ Struct Parsing Mechanism

This document explains how `struct_model.py` parses a C++ `struct` and computes its memory layout.

## Overview
- The parser is implemented in `src/model/struct_model.py`.
- Only `struct` definitions are supported; `union` parsing is not implemented.
- **Supports bitfield members (e.g., `int a : 1;`), including bitfield packing and storage unit alignment.**

## Steps
1. **Regex Extraction (Intermediate Representation)**
   - `parse_struct_definition()` extracts member types and names (including bitfields) into a temporary list, preserving declaration order. Bitfields are represented as dicts with `is_bitfield` and `bit_size`.

2. **Layout Calculation (Final Data Structure)**
   - The intermediate list is processed by `calculate_layout()`, which computes the final memory layout.
   - This final layout is stored as a **list of dictionaries**, where each dictionary represents a single member, including padding and bitfield info.

### Final Data Structure Details

Each struct member (including padding and bitfields) is stored as a dictionary. Example:
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
        "name": "flags",
        "type": "int",
        "size": 4,
        "offset": 8,
        "is_bitfield": True,
        "bit_offset": 0,
        "bit_size": 3
    }
]
```
- `is_bitfield` (bool): 是否為 bitfield 欄位
- `bit_offset` (int): 在 storage unit 內的 bit offset
- `bit_size` (int): bitfield 欄位寬度

#### Bitfield Packing/Storage Unit 規則
- 連續同型別 bitfield 會共用同一 storage unit（如 int 4 bytes 32 bits），依序分配 bit_offset。
- 若 bitfield 超過 storage unit 大小，或型別不同，則開新 storage unit。
- storage unit 會依 alignment 規則對齊。
- 普通欄位與 bitfield 欄位可混用，順序與原始 struct 宣告一致。

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

## 支援限制
- 不支援 union、enum、typedef、nested struct、#pragma pack、__attribute__ 等 C/C++ 語法。
- 只支援單一 struct 解析，不支援多 struct 同時解析。
- bitfield 只支援 int/unsigned int/char/unsigned char 等基本型別，不支援 pointer bitfield。
