# C/C++ Struct Parsing & Layout (Up-to-date)

This document describes how the current code parses C/C++ `struct`/`union`, computes memory layout, and parses hex data.

## Overview
- Parsing is provided by `src/model/struct_parser.py` and orchestrated by `src/model/struct_model.py`.
- Layout is computed by `src/model/layout.py` using `StructLayoutCalculator` and `UnionLayoutCalculator`.
- **Supports struct and union, nested structs/unions, arrays, and bitfields (including anonymous bitfields).**
- **Supports base types: char/signed char/unsigned char/bool/short/unsigned short/int/unsigned int/long/unsigned long/long long/unsigned long long/float/double/pointer.**
- **Manual struct definitions use the same layout engine and validation.**
- Follows TDD with extensive unit/integration tests.

## Parsing → Layout pipeline
1. **Parsing**
   - Legacy (flat) parser: `parse_struct_definition()` uses regex to extract members into tuples/dicts. It recognizes nested declarations but does not materialize inner members in-place (nested items appear as `("struct", name)`/`("union", name)` placeholders). Bitfields are recognized.
   - AST parser: `parse_struct_definition_ast()` / `parse_c_definition_ast()` produce `StructDef`/`UnionDef` and `MemberDef` objects with `array_dims` and `nested` trees. Supports nested struct/union, arrays, and anonymous bitfields.

2. **Layout Calculation**
   - `calculate_layout(members, pack_alignment=None)` computes the memory layout.
   - If `members` are AST objects (`MemberDef`), they are processed directly by a layout calculator; otherwise legacy dict/tuple members are normalized.
   - The resulting layout is a list of `LayoutItem` entries (dataclass), convertible to dict for UI consumption.

### LayoutItem schema

`src/model/layout.py` defines the layout record shape via `LayoutItem`:
```python
@dataclass
class LayoutItem:
    name: Optional[str]
    type: str
    size: int
    offset: int
    is_bitfield: bool
    bit_offset: int
    bit_size: int
```
The model converts these to dicts for the view. Fields:
- `name`: member name; may be `None` for anonymous bitfields; `"(padding)"`/`"(final padding)"` for padding.
- `type`: C/C++ type or `"padding"`.
- `size`/`offset`: byte size and byte offset.
- `is_bitfield`/`bit_offset`/`bit_size`: bitfield metadata (bit offset within storage unit and field width).

#### Bitfield packing rules
- 連續且同型別的 bitfield 共用一個 storage unit（例如 `int` 4 bytes = 32 bits），依序分配 `bit_offset`。
- 若超過 storage unit 容量或型別不同，開啟新的 storage unit（先依 alignment 對齊）。
- 支援匿名 bitfield（`name = None`）。
- 普通欄位與 bitfield 可混用，依宣告順序排列。

#### Arrays and nesting
- 陣列：多維陣列展開時採 row-major 順序計算偏移，元素大小由基本型別或巢狀型別佈局決定。
- 巢狀 `struct`/`union`：遞迴計算內部佈局與對齊，並在父結構中以整體對齊插入。

#### Alignment and padding
- 成員依型別對齊；結構總大小補齊至最大對齊倍數（有 `(final padding)`）。
- 可傳入 `pack_alignment` 參數限制有效對齊（模擬 `#pragma pack`）。若未指定則使用預設對齊。

#### Why this structure
- **Clarity**: `LayoutItem` explicitly captures required fields for display and data slicing.
- **Accuracy**: Padding entries model true memory layout.
- **Extensible**: New attributes can be added without breaking consumers.

3. **Hex data parsing**
   - `StructModel.parse_hex_data()` uses `self.layout` to interpret hex input.
   - Input hex is left-padded with zeros to `total_size * 2` via `zfill` to match the memory size.
   - For bitfields, it reads the storage unit, then applies `(value >> bit_offset) & ((1 << bit_size) - 1)`.
   - For non-bitfields, `int.from_bytes(..., endian)` is used; `bool` is rendered as `True/False`.

## Manual struct definition (GUI)

Manual mode uses explicit C/C++ types and optional `bit_size` (for bitfields). There is no byte-size-to-type inference.

### Layout
- `StructModel.calculate_manual_layout(members, total_size)` normalizes members, then calls `calculate_layout()` to apply C++ alignment and padding and to add final padding.

### Validation
- `StructModel.validate_manual_struct(members, total_size)` checks:
  - Supported type names and bitfield type constraints (`int/unsigned int/char/unsigned char` for bitfields).
  - Duplicate names.
  - `total_size` is positive and not smaller than computed layout size.

### Export
- `StructModel.export_manual_struct_to_h(struct_name)` generates a valid C header snippet with bitfield syntax and a `// total size: N bytes` trailer.

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

## Union support
Unions are supported in the AST parser (`parse_union_definition_ast`) and layout (`UnionLayoutCalculator`) where all members have offset `0` and the union size equals the largest member rounded up to alignment. Nested unions and arrays of unions are supported via the AST path.

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

## Pointer Size Modes (v14)

- Runtime switching between 64-bit and 32-bit pointer modes is supported.
- API:
  - `set_pointer_mode(32|64)`: Overrides `pointer` type to size/align 4/4 or 8/8 via the central type registry.
  - `get_pointer_mode()`, `reset_pointer_mode()` for querying and test cleanup.
- Layout calculators always resolve size/align through the registry, so switching pointer mode immediately affects member offsets, sizes, and final padding where `pointer` is present.
- GUI integration:
  - Both File and Manual tabs include a “32-bit 模式” checkbox that triggers `presenter.on_pointer_mode_toggle(checked)`.
  - Presenter updates `context['arch_mode']` to `"x86"`/`"x64"`, clears layout cache, and pushes the refreshed context to the view.
- Default mode: 64-bit for backward compatibility.

## 支援限制
- 不支援 `enum`、`typedef`、`__attribute__` 等完整 C/C++ 語法。
- 解析/佈局支援 struct 與 union；legacy 平面 parser 對巢狀內容僅作占位，完整巢狀需走 AST 路徑。
- bitfield 僅支援 `int/unsigned int/char/unsigned char`；不支援 pointer bitfield。
- `#pragma pack` 未提供 UI 控制；可透過 `pack_alignment` 參數啟用等效行為（預設不啟用）。

## Future Enhancements

### Planned Features
- **Pragma Pack Controls**: Expose `pack_alignment` to GUI/config.
- **Extended Types**: Additional C types and attributes as needed.

### Maintenance Notes
- **Backward Compatibility**: Maintained for existing functionality
- **Documentation**: All changes documented and tested
- **Code Quality**: TDD approach ensures robust implementation

## GUI Integration & real-time behavior

- 「手動 struct 定義」與「載入 .H」兩個頁籤共用輸入驗證、hex grid、Treeview 顯示等邏輯。
- 即時驗證 hex 輸入與錯誤提示；Treeview 即時反映 bitfield、padding、offset 等資訊。
- View 可切換樹狀/平面顯示，並提供 Debug/Cache 視圖（詳見 MVP 文件）。
