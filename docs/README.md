# Documentation

This directory contains comprehensive documentation for the C++ Struct Memory Parser project.

## Architecture Documentation

- **[ARCHITECTURE.md](architecture/)** - Detailed architecture documentation
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Project structure and organization

## Development Documentation

- **[v3_define_struct_input2_design_plan.md](development/v3_define_struct_input2_design_plan.md)** - V3 manual struct input improvements and TDD refactor
- **[v2_bit_field_design_plan.md](development/v2_bit_field_design_plan.md)** - Bit field support design
- **[string_refactor_plan.md](development/string_refactor_plan.md)** - String management refactoring
- **[run_all_tests_usage.md](development/run_all_tests_usage.md)** - Test execution guide

## Analysis Documentation

- **[input_conversion_analysis.md](analysis/input_conversion_analysis.md)** - Input conversion mechanism analysis

## Recent Updates

### TDD Refactor: Unified Parsing Logic (2024)
- **Unified parsing engine**: Both `.H file tab` and `Manual Struct tab` now use the same `parse_struct_bytes` method
- **Eliminated code duplication**: Reduced parsing logic duplication by ~50%
- **Enhanced maintainability**: Single point of modification for parsing logic
- **Comprehensive testing**: 31 automated tests covering all functionality
- **Backward compatibility**: GUI operations remain unchanged
- **Real-time size display**: Each struct member shows actual memory size in editing table
- **GUI 一致性提升**：MyStruct 與載入.h檔的成員表格欄位寬度、Debug Bytes 顯示機制完全統一，MyStruct tab 右側 scroll bar 已移除，介面更簡潔。

For detailed technical information, see [v3_define_struct_input2_design_plan.md](development/v3_define_struct_input2_design_plan.md). 