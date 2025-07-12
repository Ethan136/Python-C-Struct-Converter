# UI String Refactor Plan

## Goal
Separate user facing strings from code so that the GUI code no longer hard codes display texts or their sizes. Strings will reside in an XML file and will be read at runtime through a parser module.

## XML Schema
```xml
<strings>
    <string name="app_title">C++ Struct Parser</string>
    <string name="no_file_selected">No file selected.</string>
    <string name="browse_button">Browse...</string>
    <string name="layout_frame_title">Struct Layout</string>
    <string name="hex_input_title">Hex Data Input</string>
    <string name="input_unit_size">Input Unit Size:</string>
    <string name="byte_order">Byte Order:</string>
    <string name="parse_button">Parse Data</string>
    <string name="parsed_values_title">Parsed Values</string>
    <string name="dialog_select_file">Select a C++ header file</string>
    <string name="dialog_file_error">File Error</string>
    <string name="dialog_invalid_input">Invalid Input</string>
    <string name="dialog_value_too_large">Value Too Large</string>
    <string name="dialog_overflow_error">Overflow Error</string>
    <string name="dialog_conversion_error">Conversion Error</string>
    <string name="dialog_invalid_length">Invalid Length</string>
    <string name="dialog_parsing_error">Parsing Error</string>
    <string name="dialog_no_struct">No Struct</string>
</strings>
```
Each `<string>` element uses a `name` attribute as the lookup key. Additional strings can be appended when needed.

## Parser Module
Create `src/utils/string_parser.py` with:
- `load_ui_strings(path)` – Parse the XML and return a dictionary `{name: text}`.
- `get_string(key)` – Helper to fetch a string from the loaded dictionary.
The module stores the parsed dictionary in a module level variable so loading occurs once.

## Integration Changes
1. Load `ui_strings.xml` at application startup (in `main.py`). Pass the dictionary into the view and presenter.
2. Replace hard coded texts in `struct_view.py` and `struct_presenter.py` with lookups via `get_string`.
3. Remove any explicit character counts for these texts from the GUI code.

## Testing Approach
Following TDD:
1. Create tests in `tests/test_string_parser.py` that assert the parser correctly reads keys from a sample XML.
2. Initially run tests to fail (before implementation).
3. Implement the parser functions to satisfy the tests.
4. Ensure tests pass using `python -m unittest`.
