# Input Field Processor Module Analysis

## Overview

This document outlines the requirements and design for a new module responsible for processing user input field values in the C++ Struct Memory Parser application.

## Requirements

### 1. Automatic Left Zero Padding
- **4-byte fields**: Input `12` → Expands to `00000012`
- **8-byte fields**: Input `123` → Expands to `0000000000000123`
- **1-byte fields**: Input `1` → Expands to `01`
- Empty fields should be treated as all zeros

### 2. Endianness Conversion
- Convert padded values to raw byte data according to specified endianness
- Support both Little Endian and Big Endian formats
- Ensure consistent byte ordering across all field sizes

### 3. Raw Byte Data Generation
- Generate raw byte data that can be directly used by struct parsing
- Maintain data integrity during conversion process
- Provide clean interface for struct model integration

## Design Architecture

### Module Location
- **Path**: `src/model/input_field_processor.py`
- **Layer**: Model layer (business logic)
- **Dependencies**: No external dependencies beyond Python standard library

### Core Functions

#### 1. `pad_hex_input(input_value, byte_size)`
- **Purpose**: Automatically pad hex input with leading zeros
- **Parameters**:
  - `input_value` (str): User input hex string
  - `byte_size` (int): Target byte size (1, 4, or 8)
- **Returns**: Padded hex string
- **Behavior**:
  - Empty input → all zeros
  - Short input → left-pad with zeros
  - Full input → return as-is

#### 2. `convert_to_raw_bytes(padded_hex, byte_size, endianness)`
- **Purpose**: Convert padded hex to raw byte data with endianness
- **Parameters**:
  - `padded_hex` (str): Padded hex string
  - `byte_size` (int): Byte size (1, 4, or 8)
  - `endianness` (str): 'little' or 'big'
- **Returns**: Raw bytes object
- **Behavior**:
  - Parse hex string to integer
  - Convert to bytes with specified endianness
  - Return raw byte data

#### 3. `process_input_field(input_value, byte_size, endianness)`
- **Purpose**: Complete input processing pipeline
- **Parameters**:
  - `input_value` (str): User input hex string
  - `byte_size` (int): Target byte size
  - `endianness` (str): 'little' or 'big'
- **Returns**: Raw bytes object ready for struct parsing
- **Behavior**:
  - Pad input with zeros
  - Convert to raw bytes with endianness
  - Return processed data

## Integration Points

### With StructModel
- Replace current inline conversion logic in `parse_hex_data()`
- Use `InputFieldProcessor` for all field conversions
- Maintain existing interface for backward compatibility

### With Presenter
- Presenter can use processor for individual field validation
- Real-time input validation and preview
- Consistent error handling across all input scenarios

## Testing Strategy

### Unit Tests
- Test each function independently
- Cover all input scenarios (empty, short, full, invalid)
- Test both endianness modes
- Test all byte sizes (1, 4, 8)

### Integration Tests
- Test with actual struct parsing
- Verify data integrity through complete pipeline
- Test error handling and edge cases

### Test Data
- Use existing test configurations from `tests/data/test_config.xml`
- Add new test cases for edge scenarios
- Ensure comprehensive coverage of all requirements

## Benefits

1. **Separation of Concerns**: Input processing logic isolated from struct parsing
2. **Reusability**: Can be used by other parts of the application
3. **Testability**: Each function can be unit tested independently
4. **Maintainability**: Clear, focused functions with single responsibilities
5. **Extensibility**: Easy to add new input processing features

## Migration Plan

1. **Phase 1**: Create module with core functions
2. **Phase 2**: Write comprehensive tests
3. **Phase 3**: Integrate with StructModel
4. **Phase 4**: Update documentation
5. **Phase 5**: Verify all existing functionality works

## Future Enhancements

- Support for different number bases (binary, decimal)
- Custom padding patterns
- Input validation and sanitization
- Performance optimizations for large datasets
- **Bitfield input validation and processing:**
  - Future versions will support direct input and validation for bitfield fields (e.g., restrict input to valid bit width, auto-pack user input into correct storage unit for struct_model.py integration).
  - Will provide helper functions to convert user bitfield input into packed integer values, and vice versa.
  - Will integrate with struct_model.py to ensure bitfield input/output is consistent with memory layout and parsing logic. 

## GUI Integration & Real-time Validation (2024/07 Update)

- GUI 內所有 hex 輸入欄位（含手動 struct 與 .H 檔 tab）皆以共用方法產生，並於輸入時即時驗證長度與合法字元。
- 欄位驗證（如 hex 輸入長度、合法字元）於每次輸入時即時檢查，錯誤會即時顯示於 GUI。
- 欄位顯示、欄位寬度、tab 切換等行為完全一致，確保跨 tab 體驗一致。
- bitfield 欄位未來將支援直接輸入與即時驗證，並與 struct_model.py 的 bitfield packing 行為一致。
- 所有欄位驗證、bitfield 處理、欄位顯示等細節皆有自動化測試驗證。 