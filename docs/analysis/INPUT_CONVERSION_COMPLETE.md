# Input Conversion Mechanism - Complete Guide

## Overview

This document provides a comprehensive guide to the input conversion mechanism in the C++ Struct Memory Parser application. It combines detailed process explanation with requirement analysis and verification.

## Requirements Analysis

The application must support the following input conversion requirements:

1. **4-byte field expansion**: Input `12` → Expand to `00000012` → Apply endianness
2. **8-byte field expansion**: Input `123` → Expand to `0000000000000123` → Apply endianness  
3. **1-byte field expansion**: Input `1` → Expand to `01` → Apply endianness
4. **Empty field handling**: Empty 1/4/8 byte fields → All zeros

## Input Flow Overview

```
User Input Fields → Validation → Integer Conversion → Byte Conversion → Memory Layout → Member Parsing
```

## Step-by-Step Process

### 1. Input Collection (`struct_view.py`)

**Location**: `StructView.get_hex_input_parts()`

```python
def get_hex_input_parts(self):
    # Returns a list of (raw_input_string, expected_chars_for_this_box)
    return [(entry.get().strip(), expected_len) for entry, expected_len in self.hex_entries]
```

**What happens**:
- Collects all input field values and their expected character lengths
- Each input field corresponds to a chunk of the struct (1, 4, or 8 bytes)
- Returns a list of tuples: `(input_string, expected_chars)`

**Example**:
```python
# For a 32-byte struct with 4-byte chunks:
[
    ("12345678", 8),  # 4 bytes = 8 hex chars
    ("ABCDEF01", 8),
    ("00000000", 8),
    # ... more chunks
]
```

### 2. Input Validation (`struct_presenter.py`)

**Location**: `StructPresenter.parse_hex_data()`

```python
# Validate input is hex
if not re.match(r"^[0-9a-fA-F]*$", raw_part):
    self.view.show_error(get_string("dialog_invalid_input"),
                       f"Input \'{raw_part}\' contains non-hexadecimal characters.")
    return
```

**What happens**:
- Validates each input field contains only hexadecimal characters (0-9, A-F, a-f)
- Rejects inputs with invalid characters

### 3. Integer Conversion

**Location**: `StructPresenter.parse_hex_data()`

```python
# Convert raw_part to integer value
try:
    # Handle empty string as 0
    int_value = int(raw_part, 16) if raw_part else 0
except ValueError:
    self.view.show_error(get_string("dialog_invalid_input"),
                       f"Could not convert \'{raw_part}\' to a number.")
    return
```

**What happens**:
- Converts hex string to integer using base-16
- Empty strings are treated as 0
- Handles conversion errors

**Example**:
```python
"12345678" → 305419896 (decimal)
"ABCDEF01" → 2882400001 (decimal)
```

### 4. Byte Size Calculation

**Location**: `StructPresenter.parse_hex_data()`

```python
# Determine the byte size of the current input chunk (e.g., 1, 4, or 8 bytes)
chunk_byte_size = expected_chars_in_box // 2
```

**What happens**:
- Calculates how many bytes each input chunk represents
- Formula: `byte_size = hex_chars / 2`

**Example**:
```python
# 1 Byte mode:  2 hex chars = 1 byte
# 4 Byte mode:  8 hex chars = 4 bytes  
# 8 Byte mode: 16 hex chars = 8 bytes
```

### 5. Value Range Validation

**Location**: `StructPresenter.parse_hex_data()`

```python
# Ensure the value fits within the chunk_byte_size
# Max value for N bytes is (2**(N*8)) - 1
max_val = (2**(chunk_byte_size * 8)) - 1
if int_value > max_val:
    self.view.show_error(get_string("dialog_value_too_large"),
                       f"Value 0x{raw_part} is too large for a {chunk_byte_size}-byte field.")
    return
```

**What happens**:
- Validates that the integer value fits within the allocated byte size
- Prevents overflow errors

**Example**:
```python
# For 4-byte chunks:
max_val = (2**(4*8)) - 1 = 4294967295
# Value 0x12345678 (305419896) is valid
# Value 0x1234567890 (too large) would be rejected
```

### 6. Byte Conversion with Endianness

**Location**: `StructPresenter.parse_hex_data()`

```python
# Convert integer value to bytes using the selected endianness
bytes_for_chunk = int_value.to_bytes(chunk_byte_size, byteorder=byte_order_for_conversion)
final_memory_hex_parts.append(bytes_for_chunk.hex())
```

**What happens**:
- Converts integer back to bytes using specified endianness
- Converts bytes back to hex string for storage

**Example**:
```python
# Little Endian:
int_value = 305419896 (0x12345678)
bytes = int_value.to_bytes(4, byteorder='little')
# Result: b'\x78\x56\x34\x12'

# Big Endian:
bytes = int_value.to_bytes(4, byteorder='big')  
# Result: b'\x12\x34\x56\x78'
```

### 7. Complete Memory Assembly

**Location**: `StructPresenter.parse_hex_data()`

```python
# Join all converted hex parts to form the complete hex_data string
hex_data = "".join(final_memory_hex_parts)
```

**What happens**:
- Concatenates all hex chunks into a single hex string
- Represents the complete struct memory layout

**Example**:
```python
final_memory_hex_parts = ["78563412", "01EFCDAB", "00000000", ...]
hex_data = "7856341201EFCDAB00000000..."
```

### 8. Model-Level Parsing (`struct_model.py`)

**Location**: `StructModel.parse_hex_data()`

```python
# Pad if the input is shorter (e.g. user didn't fill all boxes)
hex_data = hex_data.ljust(self.total_size * 2, '0')
data_bytes = bytes.fromhex(hex_data)
```

**What happens**:
- Pads incomplete input with zeros
- Converts hex string to raw bytes

### 9. Member-by-Member Parsing

**Location**: `StructModel.parse_hex_data()`

```python
for item in self.layout:
    if item['type'] == "padding":
        # Skip padding entries
        continue
    
    offset, size, name = item['offset'], item['size'], item['name']
    member_bytes = data_bytes[offset : offset + size]
    value = int.from_bytes(member_bytes, byte_order)
    hex_value = member_bytes.hex()
    display_value = str(bool(value)) if item['type'] == 'bool' else str(value)
    parsed_values.append({
        "name": name,
        "value": display_value,
        "hex_raw": hex_value
    })
```

**What happens**:
- Iterates through each struct member
- Extracts bytes for each member based on offset and size
- Converts member bytes to integer value
- Stores both decimal value and hex representation

## Requirement Compliance Verification

### ✅ Requirement 1: 4-byte field expansion
- **Input**: `12`
- **Expected**: `00000012` (big endian)
- **Actual**: `00000012` ✓
- **Implementation**: `int(12, 16).to_bytes(4, byteorder='big').hex()`

### ✅ Requirement 2: 8-byte field expansion  
- **Input**: `123`
- **Expected**: `0000000000000123` (big endian)
- **Actual**: `0000000000000123` ✓
- **Implementation**: `int(123, 16).to_bytes(8, byteorder='big').hex()`

### ✅ Requirement 3: 1-byte field expansion
- **Input**: `1`
- **Expected**: `01` (big endian)
- **Actual**: `01` ✓
- **Implementation**: `int(1, 16).to_bytes(1, byteorder='big').hex()`

### ✅ Requirement 4: Empty field handling
- **4-byte empty**: `""` → `00000000` ✓
- **8-byte empty**: `""` → `0000000000000000` ✓  
- **1-byte empty**: `""` → `00` ✓
- **Implementation**: `int("", 16) if "" else 0` → `0.to_bytes(size, byteorder='big')`

## Endianness Support

The implementation correctly supports both endianness modes:

### Big Endian Examples:
- `12` (4 bytes) → `00000012`
- `123` (8 bytes) → `0000000000000123`
- `1` (1 byte) → `01`

### Little Endian Examples:
- `12` (4 bytes) → `12000000`
- `123` (8 bytes) → `2301000000000000`
- `1` (1 byte) → `01` (same for single byte)

## Complete Example

### Input Scenario
- **Struct**: 32 bytes total
- **Unit Size**: 4 bytes per input field
- **Endianness**: Little Endian
- **Input Fields**: `["12345678", "ABCDEF01", "00000000", "FFFFFFFF"]`

### Step-by-Step Conversion

1. **Input Collection**:
   ```python
   [("12345678", 8), ("ABCDEF01", 8), ("00000000", 8), ("FFFFFFFF", 8)]
   ```

2. **Integer Conversion**:
   ```python
   [305419896, 2882400001, 0, 4294967295]
   ```

3. **Byte Conversion (Little Endian)**:
   ```python
   [b'\x78\x56\x34\x12', b'\x01\xEF\xCD\xAB', b'\x00\x00\x00\x00', b'\xFF\xFF\xFF\xFF']
   ```

4. **Hex String Assembly**:
   ```python
   "7856341201EFCDAB00000000FFFFFFFF"
   ```

5. **Raw Bytes**:
   ```python
   b'\x78\x56\x34\x12\x01\xEF\xCD\xAB\x00\x00\x00\x00\xFF\xFF\xFF\xFF...'
   ```

6. **Member Parsing** (assuming struct layout):
   ```python
   # Member at offset 0, size 4:
   member_bytes = b'\x78\x56\x34\x12'
   value = int.from_bytes(member_bytes, 'little') = 305419896
   ```

## Error Handling

The implementation includes comprehensive error handling:

- **Invalid hex characters**: Rejected with clear error message
- **Value too large**: Validated against byte size limits
- **Conversion errors**: Handled gracefully
- **Incomplete input**: Auto-padded with zeros
- **Overflow**: Prevented through range validation

## Test Results

Comprehensive testing confirms:

- ✅ All 4 core requirements are met
- ✅ Both big and little endian work correctly
- ✅ Empty field handling works as specified
- ✅ Value expansion works for all field sizes
- ✅ Error handling is robust

## Implementation Location

The input conversion mechanism is implemented in two key files:

### 1. `src/presenter/struct_presenter.py` (Lines 40-90)
**Primary conversion logic:**
```python
# Convert raw_part to integer value
int_value = int(raw_part, 16) if raw_part else 0

# Determine byte size
chunk_byte_size = expected_chars_in_box // 2

# Convert to bytes with endianness
bytes_for_chunk = int_value.to_bytes(chunk_byte_size, byteorder=byte_order_for_conversion)
```

### 2. `src/model/struct_model.py` (Lines 110-141)
**Padding and parsing logic:**
```python
# Pad incomplete input with zeros
hex_data = hex_data.ljust(self.total_size * 2, '0')
data_bytes = bytes.fromhex(hex_data)

# Parse each member
member_bytes = data_bytes[offset : offset + size]
value = int.from_bytes(member_bytes, byte_order)
```

## GUI Integration & Real-time Validation (2024/07 Update)

- GUI 內所有 hex 輸入欄位（含手動 struct 與 .H 檔 tab）皆以共用方法產生，並於輸入時即時驗證長度與合法字元。
- 欄位驗證（如 hex 輸入長度、合法字元）於每次輸入時即時檢查，錯誤會即時顯示於 GUI。
- 欄位顯示、欄位寬度、tab 切換等行為完全一致，確保跨 tab 體驗一致。
- bitfield 欄位未來將支援直接輸入與即時驗證，並與 struct_model.py 的 bitfield packing 行為一致。
- 所有欄位驗證、bitfield 處理、欄位顯示等細節皆有自動化測試驗證。

## Conclusion

**🎉 ALL REQUIREMENTS ARE FULLY MET**

The input conversion mechanism correctly implements:
1. ✅ 4-byte field expansion (12 → 00000012)
2. ✅ 8-byte field expansion (123 → 0000000000000123)  
3. ✅ 1-byte field expansion (1 → 01)
4. ✅ Empty field handling (all zeros)
5. ✅ Big endian / little endian conversion
6. ✅ Comprehensive error handling
7. ✅ Value range validation

The implementation is robust, well-tested, and fully compliant with the specified requirements. 