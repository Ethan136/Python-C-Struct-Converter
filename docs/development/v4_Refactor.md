# v4 Refactor Plan

This document outlines areas for code simplification in the Python source code (excluding tests). The goal is to reduce duplication and improve maintainability.

## Targets

1. **StructView duplicate display functions**
   - `show_parsed_values` and `show_manual_parsed_values` contain nearly identical logic for populating a `Treeview`.
   - `show_debug_bytes` and `show_manual_debug_bytes` repeat the same procedure for updating a `Text` widget.
   - `rebuild_hex_grid` and `_rebuild_manual_hex_grid` share almost the same hex grid creation code.

2. **Presenter parsing logic** (future work)
   - `parse_hex_data` and `parse_manual_hex_data` implement similar loops converting hex input parts to bytes and building debug lines. A shared helper could consolidate this behaviour.

## Refactor Approach

### 1. Create Private Helpers in `StructView`

- `_populate_tree(tree, parsed_values)` – insert parsed member values into the given `ttk.Treeview`.
- `_update_debug_text(text_widget, debug_lines)` – write debug output to a `tk.Text` widget.
- `_build_hex_grid(frame, entries_list, total_size, unit_size)` – generalized logic for creating the hex input grid. Existing `rebuild_hex_grid` and `_rebuild_manual_hex_grid` will call this helper.

These helpers keep current public methods intact so existing tests remain valid.

### 2. Optional Future Work

- Extract a common method in `StructPresenter` for processing hex input parts used by both `parse_hex_data` and `parse_manual_hex_data`.

## Benefits

- Removes repeated code blocks making the view easier to maintain.
- Public method interfaces stay the same ensuring backward compatibility with tests and user code.
- Provides a foundation for further presenter refactoring.

