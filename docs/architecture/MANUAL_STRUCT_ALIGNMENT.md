# Manual Struct Alignment & Validation (Up-to-date)

This document explains how manually defined structs (MyStruct) are aligned, padded, validated, and exported.

## Overview

Manual struct uses explicit C/C++ types with optional `bit_size` for bitfields. The system automatically:

1. **Applies C++ alignment rules** to all members
2. **Inserts padding** between members as needed
3. **Aligns the final struct size** to the largest effective alignment
4. **Validates configuration** and provides real-time feedback in the GUI

## Member specification

- 指定 `type` 與 `name`，如為位元欄位再加上 `bit_size`。
- 支援型別：`char/signed char/unsigned char/bool/short/unsigned short/int/unsigned int/long/unsigned long/long long/unsigned long long/float/double/pointer`。
- 位元欄位僅支援 `int/unsigned int/char/unsigned char`；名稱可省略（匿名 bitfield）。

## Alignment and Padding Rules

### C++ alignment rules

1. **Member alignment**: Each member aligns to its type alignment (with optional `pack_alignment` upper-bound when provided programmatically).
2. **Struct alignment**: Struct size is rounded up to the maximum effective alignment of its members.
3. **Padding**: Automatic padding between members; an explicit `(final padding)` may appear at the end.

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

### Example 2: Bitfield packing

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

### Example 3: Mixed types with alignment

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

## Implementation details

### Type Conversion Process

1. **Input**: GUI collects member info (`name`, `type`, `bit_size`, total_size)
2. **Normalization**: `_convert_to_cpp_members()` validates/sanitizes entries
3. **Layout**: `calculate_layout()` applies alignment/padding rules, adds final padding
4. **Validation**: `validate_manual_struct()` checks types, names, sizes, layout ≤ total_size

### Key Functions

#### `_convert_to_cpp_members(members)`
Normalizes manual definitions to the internal format and drops unsupported entries.

#### `calculate_manual_layout(members, total_size)`
Calls `calculate_layout()` and returns a list of dicts converted from `LayoutItem`.

## Validation Rules

### Size & rule validation
- **Layout size ≤ total size**: Computed layout must not exceed the specified struct size
- **Type/bit rules**: Types must be supported; bitfields must use supported types and non-negative `bit_size`
- **Name uniqueness**: Member names must be unique (non-empty names only)

### Error messages
- `Layout 總長度 (X bytes) 超過指定 struct 大小 (Y bytes)`
- `member 'name' 必須指定型別`
- `member 'name' 不支援的型別: T`
- `member 'name' bitfield 只支援 int/unsigned int/char/unsigned char`
- `member 'name' bit_size 需為 0 或正整數`
- `成員名稱 'name' 重複`

## GUI integration

- GUI 內「手動 struct 定義」tab 及「.H 檔載入」tab 的欄位顯示、hex grid 輸入、欄位驗證、Treeview 欄位等行為已完全一致，皆以共用方法（如 _build_hex_grid、_rebuild_manual_hex_grid、_populate_tree）實作。
- 欄位驗證（如 hex 輸入長度、合法字元）於輸入時即時檢查，錯誤會即時顯示於 GUI。
- Treeview 於欄位變更、tab 切換、hex grid 變更時自動更新，確保顯示內容與 C++ 標準一致。
- bitfield、padding、offset 等資訊於 Treeview 內即時顯示，完全對齊 C++ 記憶體配置。
- 所有欄位、padding、bitfield 的顯示與驗證邏輯皆有自動化測試驗證。

## GUI display behavior

- The manual struct definition page **only displays the standard struct layout (ttk.Treeview) at the bottom**, showing all members, paddings, and offsets in real time, fully matching C++ standards.
- The previous custom memory layout table has been removed.
- This behavior is fully verified by automated tests (see tests/test_struct_view_padding.py).

### 2024/07 GUI 顯示一致性更新

- **Scroll Bar 行為**：MyStruct（手動設定資料結構）tab 右側已不再顯示垂直 scroll bar，所有內容直接顯示於單一 Frame。
- **欄位寬度統一**：MyStruct 與載入.h檔的成員顯示表格（ttk.Treeview）欄位寬度完全一致，提升跨 tab 的視覺一致性與可讀性。
- **Debug Bytes 格式統一**：兩個 tab 的 Debug Bytes 區塊皆顯示「Box N (X bytes): ...」格式，便於比對與除錯。

## Testing

### Alignment tests
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

### Bitfield tests
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

## Future enhancements

### Planned features
- **Custom alignment**: Expose `pack_alignment` to UI/config
- **Extended types**: More C types (if needed)
- **Nested structs/arrays**: Already supported through AST path in parsing mode; manual editor remains flat member list
- **Union support in manual mode**: Not yet exposed in GUI editor

### Backward compatibility
- Existing manual structs continue to work
- Validation messages and Treeview columns remain stable
- Behavior covered by automated tests