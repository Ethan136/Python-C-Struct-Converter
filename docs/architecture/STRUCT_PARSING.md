# C++ Struct Parsing Mechanism

This document explains how `struct_model.py` parses a C++ `struct` and computes its memory layout.

## Overview
- The parser is implemented in `src/model/struct_model.py`.
- Only `struct` definitions are supported; `union` parsing is not implemented.
- **Supports bitfield members (e.g., `int a : 1;`), including bitfield packing and storage unit alignment.**
- **Supports manual struct definition with byte/bit size validation and export functionality.**
- **Implements comprehensive validation logic with TDD testing approach.**

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

## Manual Struct Definition System

### Overview
The system supports manual struct definition through GUI interface, allowing users to create structs without external header files.

> **Note:** Manual struct mode now fully supports C++-style alignment and padding. All members are automatically aligned and padded as in C++.

### Manual Layout Calculation
- **Function**: `calculate_manual_layout(members, total_size)`
- **Purpose**: Calculate layout for manually defined structs using C++ standard alignment and padding rules
- **Features**:
  - Bit-level size tracking
  - Automatic end padding insertion
  - **Automatic alignment and padding for all members, matching C++ compiler behavior**
  - Validation against total struct size
  - Future-ready for pragma pack/align mechanisms
- **Implementation Note**: `calculate_manual_layout` now directly calls `calculate_layout` after converting members to C++ types, so the resulting layout is identical to what a C++ compiler would produce.

### Manual Struct Validation
- **Function**: `validate_manual_struct(members, total_size)`
- **Purpose**: Comprehensive validation of manual struct definitions
- **Validation Rules**:
  - Member name uniqueness
  - Positive integer size validation
  - Total size consistency verification
  - Real-time validation feedback

### Struct Export Functionality
- **Function**: `export_manual_struct_to_h()`
- **Purpose**: Export manually defined structs to C header files
- **Features**:
  - Generates valid C struct declarations
  - Proper bitfield syntax formatting
  - Type compatibility handling

## Validation Logic

### Struct Definition Validation
- **Function**: `validate_struct_definition()`
- **Purpose**: Enhanced validation logic for struct definitions
- **Validation Areas**:
  - Member field type validation
  - Positive integer size validation
  - Total size consistency checking
  - Bitfield-specific validation rules

### Layout Validation
- **Function**: `validate_layout()`
- **Purpose**: Layout consistency validation
- **Validation Rules**:
  - Sum of bit sizes equals struct total size
  - Proper offset calculation verification
  - Padding entry validation

### Byte/Bit Size Merging
- **Function**: `_merge_byte_and_bit_size()`
- **Purpose**: Compatibility layer for legacy data formats
- **Features**:
  - Converts length to bit_size when needed
  - Maintains backward compatibility
  - Supports both old and new data formats

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

## Hex String 補零方向與記憶體對應說明

### 為什麼 struct input 是「左補零」？

- 使用者輸入的 hex string（如 "121"）是「高位在左、低位在右」的**人類可讀十六進位字串**。
- 當 hex string 長度不足 struct 大小時，**系統會自動左補零**（高位補零），確保 bytes 長度正確。
- 這樣 "121" → "0000000000000121"（8 bytes），對應 bytes [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x21]。

### 與 C/C++ 記憶體的對應

- 在 C/C++ 中，struct 記憶體是「固定長度」的 bytes array，不足時高位補零。
- 例如：
  ```c
  struct A { long long val; };
  struct A a = { .val = 0x121 };
  // 記憶體內容（big endian）：00 00 00 00 00 00 01 21
  // 記憶體內容（little endian）：21 01 00 00 00 00 00 00
  ```
- Python 解析 bytes → 數值時，會根據 endianness（big/little）正確解讀高低位。

### 圖解

| hex string                | bytes array (index)         | int.from_bytes(..., "big") | int.from_bytes(..., "little") |
|---------------------------|-----------------------------|----------------------------|-------------------------------|
| "0000000000000121"        | [0x00, ..., 0x01, 0x21]     | 289                        | 2378182078228332544           |
| "2101000000000000"        | [0x21, 0x01, 0x00, ...]     | 2378182078228332544        | 289                           |

### 結論

- **左補零**是為了讓 hex string 的「高位」對應到 bytes array 的高 index（big endian）或低 index（little endian）。
- Python 會根據 endianness 正確解讀 bytes array，不會搞錯高低位。
- 這種設計與 C/C++ 記憶體 dump、hexdump 工具完全一致。

## Testing and TDD Approach

### Test-Driven Development
The struct parsing system follows TDD principles with comprehensive test coverage:

- **Unit Tests**: All core functionality is unit tested
- **Integration Tests**: End-to-end testing of struct parsing and data conversion
- **GUI Tests**: Tkinter interface testing with proper skip handling
- **Validation Tests**: Comprehensive validation logic testing

### Test Coverage Areas
- **Bitfield Functionality**: Parsing, layout, data extraction
- **Manual Struct Definition**: Creation, validation, export
- **Validation Logic**: Error handling and edge cases
- **Memory Layout**: Padding, alignment, bitfield packing
- **Data Processing**: Hex conversion, endianness, bitfield extraction

### Testing Infrastructure
- **Cross-Platform Test Runner**: `run_all_tests.py` separates GUI and non-GUI tests
- **XML Configuration Tests**: Automated testing using XML configuration files
- **TDD Workflow**: Test-first development approach for all new features

## 支援限制
- 不支援 union、enum、typedef、nested struct、#pragma pack、__attribute__ 等 C/C++ 語法。
- 只支援單一 struct 解析，不支援多 struct 同時解析。
- bitfield 只支援 int/unsigned int/char/unsigned char 等基本型別，不支援 pointer bitfield。
- 手動 struct 定義目前不支援 padding，所有成員緊密排列。
> **Note:** Manual struct mode does not support padding or advanced C features (e.g., union, nested struct, #pragma pack). All members are tightly packed.

## Future Enhancements

### Planned Features
- **Pragma Pack Support**: Bit-level padding foundation ready for alignment mechanisms
- **Advanced Alignment**: Framework in place for custom alignment rules
- **Extended Type Support**: Architecture supports additional C types
- **Union Support**: Framework ready for union parsing implementation

### Maintenance Notes
- **Backward Compatibility**: Maintained for existing functionality
- **Documentation**: All changes documented and tested
- **Code Quality**: TDD approach ensures robust implementation
