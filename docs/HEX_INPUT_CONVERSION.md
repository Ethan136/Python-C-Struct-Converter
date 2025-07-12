# Hex Input Conversion Process

## Overview

This document explains how the application converts user input from hex input fields into individual byte values for each struct member. The process involves multiple steps of data transformation and validation.

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
```

**What happens**:
- Iterates through each struct member
- Extracts bytes for each member based on offset and size
- Converts member bytes to integer value
- Stores both decimal value and hex representation

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
   
   # Member at offset 4, size 4:
   member_bytes = b'\x01\xEF\xCD\xAB'
   value = int.from_bytes(member_bytes, 'little') = 2882400001
   ```

## Key Design Decisions

### 1. Chunked Input
- **Why**: Makes large structs easier to input
- **Benefit**: User can focus on smaller, manageable chunks

### 2. Endianness Consistency
- **Why**: Input and output use same endianness
- **Benefit**: Predictable behavior across different systems

### 3. Auto-Padding
- **Why**: Handles incomplete input gracefully
- **Benefit**: User doesn't need to fill every field

### 4. Validation at Multiple Levels
- **Why**: Catches errors early and provides clear feedback
- **Benefit**: Better user experience and debugging

## Error Handling

The process includes comprehensive error handling:

1. **Invalid Hex Characters**: Rejected with clear error message
2. **Value Too Large**: Validated against byte size limits
3. **Conversion Errors**: Handled gracefully with user feedback
4. **Incomplete Input**: Auto-padded with zeros
5. **Overflow**: Prevented through range validation

This multi-step process ensures that user input is correctly converted into the byte-level representation needed for accurate struct member parsing. 