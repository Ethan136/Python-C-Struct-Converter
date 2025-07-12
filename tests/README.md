# Tests Directory

This directory contains all test files for the C++ Struct Memory Parser project.

## Test Files

### `test_string_parser.py`
Tests for the UI string configuration system.
- Tests XML string loading functionality
- Tests string retrieval with fallback handling

### `test_input_conversion.py`
Tests for the input conversion mechanism.
- Tests 4-byte field expansion (12 → 00000012)
- Tests 8-byte field expansion (123 → 0000000000000123)
- Tests 1-byte field expansion (1 → 01)
- Tests empty field handling (empty → all zeros)
- Tests endianness conversion (big/little endian)
- Tests value range validation
- Tests invalid input handling
- Tests integration with model parsing

## Running Tests

### Run All Tests
```bash
# From project root
python3 -m unittest discover tests -v

# Or use the test runner
python3 run_tests.py
```

### Run Specific Test Module
```bash
# From project root
python3 -m unittest tests.test_input_conversion -v
python3 -m unittest tests.test_string_parser -v

# Or use the test runner
python3 run_tests.py --test test_input_conversion
python3 run_tests.py --test test_string_parser
```

### Run Specific Test Method
```bash
# From project root
python3 -m unittest tests.test_input_conversion.TestInputConversion.test_4byte_field_expansion -v
```

### Run Tests from Tests Directory
```bash
cd tests
python3 -m unittest test_input_conversion -v
python3 -m unittest test_string_parser -v
```

## Test Coverage

The tests cover the following areas:

### Input Conversion Mechanism (`test_input_conversion.py`)
- ✅ **4-byte field expansion**: Input `12` → Expand to `00000012`
- ✅ **8-byte field expansion**: Input `123` → Expand to `0000000000000123`
- ✅ **1-byte field expansion**: Input `1` → Expand to `01`
- ✅ **Empty field handling**: Empty fields → All zeros
- ✅ **Big endian conversion**: Correct byte ordering
- ✅ **Little endian conversion**: Correct byte ordering
- ✅ **Value range validation**: Prevents overflow
- ✅ **Invalid input handling**: Rejects non-hex characters
- ✅ **Model integration**: Works with struct parsing

### String Parser (`test_string_parser.py`)
- ✅ **XML loading**: Loads UI strings from XML files
- ✅ **String retrieval**: Gets strings with fallback handling

## Test Structure

All tests follow the standard Python `unittest` framework:

```python
import unittest

class TestClassName(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def tearDown(self):
        """Clean up test fixtures"""
        pass
    
    def test_specific_functionality(self):
        """Test description"""
        # Test implementation
        self.assertEqual(expected, actual)
```

## Adding New Tests

To add new tests:

1. Create a new file `test_<module_name>.py` in the `tests/` directory
2. Follow the existing naming convention and structure
3. Use descriptive test method names starting with `test_`
4. Include proper setup and teardown methods if needed
5. Add comprehensive docstrings explaining what each test does

## Test Requirements

- All tests must pass before merging code changes
- Tests should be comprehensive and cover edge cases
- Tests should be independent and not rely on external state
- Tests should clean up after themselves (use `tearDown` methods)
- Tests should provide clear error messages when they fail

## Continuous Integration

These tests are designed to be run in CI/CD pipelines. The test runner (`run_tests.py`) provides a simple interface for automated testing environments. 