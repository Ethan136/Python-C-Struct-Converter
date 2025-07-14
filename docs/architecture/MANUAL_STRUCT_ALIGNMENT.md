# Manual Struct Alignment Behavior

This document explains the alignment and padding behavior of manually defined structs (MyStruct) in the C++ Struct Memory Parser.

## Overview

Manual struct definition now fully supports C++ standard alignment and padding rules. When you define a struct manually through the GUI, the system automatically:

1. **Infers C++ types** from byte/bit size specifications
2. **Applies C++ alignment rules** to all members
3. **Inserts padding** between members as needed
4. **Aligns the final struct size** to the largest member's alignment

This ensures that manually defined structs produce the same memory layout as C++ compilers.

## Type Inference Rules

### Byte Size to C++ Type Mapping

| Byte Size | Inferred C++ Type | Alignment | Notes |
|-----------|-------------------|-----------|-------|
| 1 | `char` | 1 | 8-bit character |
| 2 | `short` | 2 | 16-bit integer |
| 4 | `int` | 4 | 32-bit integer |
| 8 | `long long` | 8 | 64-bit integer |
| >8 | `unsigned char[]` | 1 | Array of bytes |

### Bit Size Handling

- **Bit size > 0**: Automatically inferred as `unsigned int` bitfield
- **Bit size = 0**: Uses byte size for type inference
- **Multiple bitfields**: Packed into the same storage unit when possible

## Alignment and Padding Rules

### C++ Standard Alignment Rules

The system follows standard C++ alignment rules:

1. **Member Alignment**: Each member is aligned to its type's alignment requirement
2. **Struct Alignment**: The entire struct is aligned to the largest member's alignment
3. **Padding Insertion**: Padding bytes are inserted between members to satisfy alignment
4. **Final Padding**: The struct size is padded to be a multiple of the struct's alignment

### Alignment Values (64-bit System)

| Type | Size | Alignment |
|------|------|-----------|
| `char` | 1 | 1 |
| `short` | 2 | 2 |
| `int` | 4 | 4 |
| `long long` | 8 | 8 |
| `pointer` | 8 | 8 |

## Examples

### Example 1: Simple Alignment

**Manual Input:**
```
Member 1: name="a", byte_size=1, bit_size=0  (char)
Member 2: name="b", byte_size=4, bit_size=0  (int)
Total Size: 8
```

**C++ Equivalent:**
```cpp
struct MyStruct {
    char a;     // offset 0, size 1
    // 3 bytes padding
    int b;      // offset 4, size 4
};
// total size: 8 bytes
```

**Memory Layout:**
```
Offset: 0  1  2  3  4  5  6  7
        [a][pad][pad][pad][  b  ][  b  ][  b  ][  b  ]
```

### Example 2: Bitfield Packing

**Manual Input:**
```
Member 1: name="flags1", byte_size=0, bit_size=3
Member 2: name="flags2", byte_size=0, bit_size=5
Member 3: name="flags3", byte_size=0, bit_size=8
Total Size: 4
```

**C++ Equivalent:**
```cpp
struct MyStruct {
    unsigned int flags1 : 3;   // bit offset 0
    unsigned int flags2 : 5;   // bit offset 3
    unsigned int flags3 : 8;   // bit offset 8
};
// total size: 4 bytes (one storage unit)
```

**Memory Layout:**
```
Storage Unit (4 bytes): [flags1:3][flags2:5][flags3:8][unused:16]
```

### Example 3: Mixed Types with Alignment

**Manual Input:**
```
Member 1: name="status", byte_size=1, bit_size=0   (char)
Member 2: name="flags", byte_size=0, bit_size=12   (bitfield)
Member 3: name="count", byte_size=2, bit_size=0    (short)
Member 4: name="id", byte_size=0, bit_size=4       (bitfield)
Total Size: 16
```

**C++ Equivalent:**
```cpp
struct MyStruct {
    char status;                    // offset 0, size 1
    // 3 bytes padding
    unsigned int flags : 12;        // offset 4, size 4, bit offset 0
    short count;                    // offset 8, size 2
    // 2 bytes padding
    unsigned int id : 4;            // offset 12, size 4, bit offset 0
};
// total size: 16 bytes
```

**Memory Layout:**
```
Offset:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
        [status][pad][pad][pad][   flags   ][   flags   ][   flags   ][   flags   ][count][count][pad][pad][   id   ][   id   ][   id   ][   id   ]
```

## Implementation Details

### Type Conversion Process

1. **Input Processing**: GUI collects member information (name, byte_size, bit_size)
2. **Type Inference**: `_convert_to_cpp_members()` converts to C++ types
3. **Layout Calculation**: `calculate_layout()` applies C++ alignment rules
4. **Validation**: `validate_manual_struct()` ensures consistency

### Key Functions

#### `_convert_to_cpp_members(members)`
Converts manual member definitions to C++ type specifications:

```python
def infer_type(byte_size, bit_size):
    if bit_size > 0:
        return {"type": "unsigned int", "name": "", "is_bitfield": True, "bit_size": bit_size}
    if byte_size == 1:
        return {"type": "char", "name": ""}
    elif byte_size == 2:
        return {"type": "short", "name": ""}
    # ... etc
```

#### `calculate_manual_layout(members, total_size)`
Produces C++-standard layout:

```python
def calculate_manual_layout(self, members, total_size):
    expanded_members = self._convert_to_cpp_members(members)
    layout, total, align = calculate_layout(expanded_members)
    return layout
```

## Validation Rules

### Size Validation
- **Layout Size ≤ Total Size**: The calculated layout size must not exceed the specified total size
- **Member Validation**: All members must have valid byte/bit sizes
- **Name Uniqueness**: Member names must be unique within the struct

### Error Messages
- `"Layout 總長度 (X bytes) 超過指定 struct 大小 (Y bytes)"`: When C++ alignment requires more space than specified
- `"member 'name' byte_size 需為 0 或正整數"`: Invalid byte size
- `"member 'name' bit_size 需為 0 或正整數"`: Invalid bit size
- `"成員名稱 'name' 重複"`: Duplicate member names

## GUI Integration (2024/07 Update)

- GUI 內「手動 struct 定義」tab 及「.H 檔載入」tab 的欄位顯示、hex grid 輸入、欄位驗證、Treeview 欄位等行為已完全一致，皆以共用方法（如 _build_hex_grid、_rebuild_manual_hex_grid、_populate_tree）實作。
- 欄位驗證（如 hex 輸入長度、合法字元）於輸入時即時檢查，錯誤會即時顯示於 GUI。
- Treeview 於欄位變更、tab 切換、hex grid 變更時自動更新，確保顯示內容與 C++ 標準一致。
- bitfield、padding、offset 等資訊於 Treeview 內即時顯示，完全對齊 C++ 記憶體配置。
- 所有欄位、padding、bitfield 的顯示與驗證邏輯皆有自動化測試驗證。

## GUI Display Behavior (2024/07 Update)

- The manual struct definition page **only displays the standard struct layout (ttk.Treeview) at the bottom**, showing all members, paddings, and offsets in real time, fully matching C++ standards.
- The previous custom memory layout table has been removed.
- This behavior is fully verified by automated tests (see tests/test_struct_view_padding.py).

### 2024/07 GUI 顯示一致性更新

- **Scroll Bar 行為**：MyStruct（手動設定資料結構）tab 右側已不再顯示垂直 scroll bar，所有內容直接顯示於單一 Frame。
- **欄位寬度統一**：MyStruct 與載入.h檔的成員顯示表格（ttk.Treeview）欄位寬度完全一致，提升跨 tab 的視覺一致性與可讀性。
- **Debug Bytes 格式統一**：兩個 tab 的 Debug Bytes 區塊皆顯示「Box N (X bytes): ...」格式，便於比對與除錯。

## Testing

### Alignment Tests
All alignment behavior is thoroughly tested:

```python
def test_manual_struct_alignment(self):
    members = [
        {"name": "a", "byte_size": 1, "bit_size": 0},  # char
        {"name": "b", "byte_size": 4, "bit_size": 0},  # int
    ]
    total_size = 8
    layout = self.model.calculate_manual_layout(members, total_size)
    
    # Verify alignment
    self.assertEqual(layout[0]["offset"], 0)  # char at offset 0
    self.assertEqual(layout[1]["offset"], 4)  # int at offset 4 (after padding)
```

### Bitfield Tests
Bitfield packing is verified:

```python
def test_manual_struct_bitfield_packing(self):
    members = [
        {"name": "a", "byte_size": 0, "bit_size": 3},
        {"name": "b", "byte_size": 0, "bit_size": 5},
    ]
    layout = self.model.calculate_manual_layout(members, 4)
    
    # Verify bitfield packing
    self.assertEqual(layout[0]["bit_offset"], 0)
    self.assertEqual(layout[1]["bit_offset"], 3)
```

## Benefits

### Consistency with C++
- **Identical Layout**: Manual structs produce the same memory layout as C++ compilers
- **Predictable Behavior**: No surprises when comparing with C++ code
- **Compatibility**: Exported headers can be used in C++ projects

### User Experience
- **Intuitive**: Users can specify byte/bit sizes naturally
- **Automatic**: No need to manually calculate padding
- **Real-time**: Immediate feedback on layout and validation

### Maintainability
- **Standard Compliance**: Follows established C++ rules
- **Testable**: All behavior is thoroughly tested
- **Extensible**: Framework ready for future enhancements

## Future Enhancements

### Planned Features
- **Custom Alignment**: Support for `#pragma pack` directives
- **Extended Types**: Support for more C++ types (float, double, etc.)
- **Nested Structs**: Support for struct members within structs
- **Union Support**: Support for union members

### Backward Compatibility
- **Legacy Support**: Maintains compatibility with existing manual struct definitions
- **Migration Path**: Clear upgrade path for existing users
- **Documentation**: Comprehensive documentation for all changes 