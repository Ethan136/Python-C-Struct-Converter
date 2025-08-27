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
- **[ast_serialization.md](development/ast_serialization.md)** - ASTNode serialization helpers

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
- **GUI 一致性提升**：MyStruct 與載入.h檔的成員表格欄位寬度統一，Debug Bytes 僅於載入.h檔或 Debug Tab 顯示，介面更簡潔。

For detailed technical information, see [v3_define_struct_input2_design_plan.md](development/v3_define_struct_input2_design_plan.md). 

### v14: GUI 32-bit/64-bit Pointer Mode
- New GUI toggle to switch pointer size/alignment between 32-bit (4/4) and 64-bit (8/8)
- Runtime API to control pointer mode; layouts are recalculated automatically
- See: [Pointer Mode User Guide](development/v14_GUI_pointer_mode_switch.md)
 - Also see: [Manual Struct Alignment Notes](architecture/MANUAL_STRUCT_ALIGNMENT.md)