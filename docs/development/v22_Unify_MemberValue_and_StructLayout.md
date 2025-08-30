## V22: Unify MemberValue and StructLayout into a single view (Import .H)

### 1) Background and Goal
- Problem: Import .H tab currently uses two separate Treeviews: `MemberValue` (values/hex) and `StructLayout` (type/offset/size/bit info). This causes duplicated navigation and mismatched selection states.
- Goal: Present a single, unified Treeview that shows both layout and values in one table. Reduce cognitive load and simplify workflows like inspection, CSV export, and future filtering/sorting.

### 2) Scope
- In scope:
  - Unify UI within Import .H tab to a single Treeview.
  - Add value columns to the layout Treeview: `value`, `hex_value`, `hex_raw`.
  - Ensure correct display before and after hex parsing.
  - Preserve CSV export behavior and enablement logic.
- Out of scope:
  - Backend data model format changes (no schema change planned for V22).
  - Presenter APIs (keep existing methods; only the View wiring changes).

### 3) Rationale and Feasibility
- `StructModel.parse_hex_data()` iterates `self.layout` to produce `parsed_values`. The row-by-row order and names align with layout entries, including arrays (`name[index]`) and nested fields (`parent.child`).
- This enables index-based merging of rows without complex key matching. Padding entries are preserved and can display `-` for `value`.

### 4) UI Specification
- Base on `LAYOUT_TREEVIEW_COLUMNS` and append value columns:
  - Columns: `name`, `type`, `offset`, `size`, `bit_offset`, `bit_size`, `is_bitfield`, `value`, `hex_value`, `hex_raw`.
  - Display behavior:
    - After load (.h parsed, before hex parse): fill layout columns; leave value columns empty.
    - After hex parsed: fill value columns per row using `parsed_values` in-order mapping.
  - CSV export: remains enabled after `show_struct_layout(...)`. No behavior change in V22.

### 5) Data Flow
- Load .H → Model sets `layout/total_size/struct_align` → View `show_struct_layout(...)` inserts rows with empty value fields.
- Parse hex → Presenter calls `model.parse_hex_data(...)` → View `show_parsed_values(...)` merges values into existing rows by index (or rebuilds rows with merged data for simplicity and consistency).
- Optional: keep `member_values` in Model for AST tree context display; not required for unified table.

### 6) Implementation Plan (View-focused)
- Add value columns into `LAYOUT_TREEVIEW_COLUMNS` in `src/view/struct_view.py`.
- Deprecate the separate `member_tree` rendering in Import .H tab (V22 keeps the widget but hides/ignores it behind a feature flag for rollback).
- Update `show_struct_layout(...)` to populate only layout columns and set value columns to empty strings.
- Update `show_parsed_values(...)` to:
  - Either: iterate current `layout_tree` rows and update the appended value columns by index.
  - Or: reconstruct the unified rows by zipping `layout` and `parsed_values` and reinsert (simpler and deterministic).
- Keep manual struct tab behavior unchanged in V22; consider unification there in a later version.

### 6.1) Concrete edit points
- File: `src/view/struct_view.py`
  - Constants:
    - Extend `LAYOUT_TREEVIEW_COLUMNS` by appending:
      - `{ "name": "value", "title": "member_col_value", "width": 100 }`
      - `{ "name": "hex_value", "title": "member_col_hex_value", "width": 100 }`
      - `{ "name": "hex_raw", "title": "member_col_hex_raw", "width": 120 }`
    - Rationale: reuse existing i18n keys already used by `MEMBER_TREEVIEW_COLUMNS`.
  - StructView state:
    - Add view-level flag: `self.enable_unified_layout_values: bool = True` (constructor). Optionally allow injection via env/config in future.
    - Add cached references: `self._last_layout: list | None = None`, `self._last_parsed_values: list | None = None` (to support refresh/rebuild flows).
  - Methods:
    - `show_struct_layout(struct_name, layout, total_size, struct_align)`
      - Assign `self._last_layout = layout`
      - If `enable_unified_layout_values`:
        - Build rows with layout columns filled; set `value/hex_value/hex_raw` to empty strings; insert into `self.layout_tree`.
      - Else: current behavior (no value columns) — legacy mode.
      - Preserve CSV export button enable logic.
    - `show_parsed_values(parsed_values, byte_order_str=None)`
      - Assign `self._last_parsed_values = parsed_values`
      - If unified mode and `self._last_layout` exists:
        - Rebuild `self.layout_tree` rows by zipping `self._last_layout` with `parsed_values` (index-based). For each pair `item`, `val`:
          - Compute `hex_value` as today (from value when not `-`).
          - Normalize `hex_raw` with `｜` separators as today.
          - Insert full row (layout + value columns).
      - Else: fallback to existing `_populate_tree(self.member_tree, parsed_values)` for legacy mode.
    - `create_layout_treeview(...)`: no change besides extra columns handled automatically by the constants.
  - Manual struct tab:
    - No change in V22. Continue writing parsed values into `self.manual_member_tree` and layout into `self.manual_layout_tree`.

### 6.2) Non-goals and compatibility
- Presenter (`src/presenter/struct_presenter.py`) and Model (`src/model/struct_model.py`) APIs unchanged.
- `member_values` in Model remains for AST tree context; unified table does not rely on it.
- CSV export behavior and entry point unchanged; still driven by `show_struct_layout(...)` success.

### 7) Feature Flag and Rollout
- Introduce a view-level flag (e.g., `enable_unified_layout_values = True`) to switch between:
  - Unified single Treeview (default in V22).
  - Legacy two-Treeview mode (fallback during rollout/testing).
- Flag can be set via config or environment variable for CI A/B execution.

### 8) Risks and Mitigations
- GUI test breakage expecting `member_tree`: guard with the feature flag and update tests to check unified mode paths. Retain minimal compatibility tests for legacy mode during the transition.
- Anonymous/duplicate names: index-based merge avoids key collisions.
- Not yet parsed: value columns are blank; ensure no sorting/filtering assumes numeric values.

### 9) Acceptance Criteria
- After loading a .h, layout is shown with correct rows; CSV export button is enabled.
- After parsing hex, unified table shows `value`, `hex_value`, and `hex_raw` aligned with each row.
- Bitfields show correct `bit_offset/bit_size/is_bitfield` and decoded values.
- Arrays and nested fields render with expanded rows and correct values.
- All relevant GUI tests pass in unified mode; no regressions in parsing or CSV export.

### 10) Test Plan
- Update GUI tests to operate in unified mode:
  - Load-and-show flow: `show_struct_layout(...)` enables export and renders rows without values.
  - Parse flow: `show_parsed_values(...)` fills the appended value columns; verify by row index.
  - Bitfield/array/nested struct: verify row count, offsets, and decoded values.
  - Padding rows display `value` as `-` and proper hex dump.
  - Headless CI skip conditions remain intact.
- Keep a small set of legacy-mode tests behind the flag to validate rollback path.

### 10.1) Test changes by phase
- Phase 1 (Introduce unified columns + rebuild logic):
  - New tests (Import .H tab):
    - `test_unified_layout_adds_value_columns_after_load` — after `show_struct_layout(...)`, assert the layout tree has the extra value columns with empty strings.
    - `test_unified_layout_fills_values_after_parse` — simulate `show_struct_layout(...)` then `show_parsed_values(...)`; assert each row’s `value/hex_value/hex_raw` populated, with `hex_raw` grouping and `hex_value` formatting consistent with `_populate_tree` behavior.
    - `test_unified_layout_padding_value_dash` — assert padding rows keep `value == '-'` and meaningful `hex_raw` bytes.
    - `test_unified_layout_bitfield_and_arrays_values` — cover rows with bitfields and arrays; verify both layout columns and decoded `value` alignment.
  - Adjustments:
    - Any existing Import .H tests that previously asserted values in `member_tree` should be redirected to `layout_tree` when unified flag is enabled. Keep legacy assertions under legacy-mode switch if still valuable.
  - Unchanged:
    - Manual struct tab tests remain unchanged (still separate value/layout trees).

- Phase 2 (Optional removal of legacy member-value table for Import .H):
  - Remove or downgrade legacy-mode tests to smoke tests.
  - Ensure A/B flag remains for one release window to ease rollbacks.

### 10.2) Concrete test file updates
- `tests/view/test_struct_view.py`:
  - Add new tests listed above under Phase 1.
  - Where applicable, gate old assertions with unified-flag checks to avoid brittle failures.
- `tests/view/test_struct_view_export_csv_button.py`:
  - Keep as-is; verify CSV export button state remains enabled after `show_struct_layout(...)` in unified mode.
- Bitfield/nested/array coverage can reuse existing fixtures and helper stubs, focusing on row/value assertions in `layout_tree`.

### 10.3) Explicit unified-mode test tasks (to be implemented)
- Create `tests/view/test_struct_view_unified_mode.py` containing:
  - `test_unified_layout_adds_value_columns_after_load`
    - Arrange: load layout and call `view.show_struct_layout(...)` with flag on.
    - Assert: first row `values` length includes the 3 extra columns and they are empty strings.
  - `test_unified_layout_fills_values_after_parse`
    - Arrange: call `show_struct_layout(...)` then `show_parsed_values(...)` with mock parsed results aligned by index.
    - Assert: `value`, `hex_value`, `hex_raw` are populated and formatted (hex_value via `hex(int(value))`; hex_raw grouped with `｜`).
  - `test_unified_layout_padding_value_dash`
    - Arrange: include padding entries in layout and parsed values with `value == '-'`.
    - Assert: padding row keeps `value == '-'` and has proper `hex_raw` when bytes present.
  - `test_unified_layout_bitfield_and_arrays_values`
    - Arrange: layout with bitfields and arrays; parsed values paired by index.
    - Assert: correct row count, offsets, and decoded values appear in the value columns.
- Adjust Import .H value assertions in existing tests to check `layout_tree` under unified flag. Keep legacy-mode branches where needed.

### 11) Migration Notes
- No Model/Presenter API changes in V22; View-only changes with a feature flag.
- Downstream customizations relying on `member_tree` should switch to unified mode columns; legacy mode remains available temporarily.

### 12) Follow-ups (Post-V22)
- Consider unifying manual struct tab to the same model for consistency.
- Add per-column show/hide management and saved user preferences.
- Optional: enrich CSV export to include value columns when available.

---

## Appendix A: Step-by-step Implementation Checklist

This appendix is a prescriptive edit list. Follow steps in order.

### A.1 Add unified columns and flag
1) File: `src/view/struct_view.py`
   - Locate `LAYOUT_TREEVIEW_COLUMNS` and append three entries:
     - `{ "name": "value", "title": "member_col_value", "width": 100 }`
     - `{ "name": "hex_value", "title": "member_col_hex_value", "width": 100 }`
     - `{ "name": "hex_raw", "title": "member_col_hex_raw", "width": 120 }`
   - In `StructView.__init__`, set:
     - `self.enable_unified_layout_values = True`
     - `self._last_layout = None`
     - `self._last_parsed_values = None`

### A.2 Populate layout rows with empty value columns
2) File: `src/view/struct_view.py`
   - In `show_struct_layout(struct_name, layout, total_size, struct_align)`:
     - Before inserting rows, assign `self._last_layout = layout`.
     - If `self.enable_unified_layout_values` is True:
       - For each `item` in `layout`, compute strings for `name/type/offset/size/bit_offset/bit_size/is_bitfield` as today.
       - Append empty strings for the 3 new columns: `value`, `hex_value`, `hex_raw`.
       - Insert the combined tuple into `self.layout_tree`.
     - Keep the CSV export button enable logic exactly as-is.

### A.3 Rebuild rows after parsing to include values
3) File: `src/view/struct_view.py`
   - In `show_parsed_values(parsed_values, byte_order_str=None)`:
     - Assign `self._last_parsed_values = parsed_values`.
     - If unified mode and `self._last_layout` exists:
       - Clear all rows in `self.layout_tree`.
       - Zip `self._last_layout` with `parsed_values` by index. For each pair:
         - Derive `value_str` from `val.get("value", "")`.
         - Derive `hex_value_str`:
           - If `value_str != '-'`, attempt `hex(int(value_str))` else `'-'`.
         - Derive `hex_raw_str`:
           - From `val.get("hex_raw", "")` and join every two hex chars with `｜` if length > 2.
         - Insert the full 10-column row.
     - Else (legacy mode): fall back to `self._populate_tree(self.member_tree, parsed_values)`.

### A.4 Leave manual struct tab unchanged for V22
4) No edits to manual tab methods; ensure existing tests still pass.

### A.5 Add a simple config toggle (optional)
5) If desired, wire an environment/config reader to set `self.enable_unified_layout_values` at runtime. Otherwise keep default True for V22.

### A.6 Update tests — unified mode
6) File: `tests/view/test_struct_view.py`
   - Add new tests:
     - `test_unified_layout_adds_value_columns_after_load`
       - After `show_struct_layout(...)`, fetch first row values; assert the tuple length includes 3 extra empty value columns.
     - `test_unified_layout_fills_values_after_parse`
       - Call `show_struct_layout(...)` then simulate `show_parsed_values(...)` with a small `parsed_values` list; assert values/hex formatting present in `layout_tree` rows.
     - `test_unified_layout_padding_value_dash`
       - Ensure padding row has `value == '-'` and `hex_raw` is non-empty when applicable.
     - `test_unified_layout_bitfield_and_arrays_values`
       - Construct a layout with bitfields/arrays; provide `parsed_values`; assert proper row-value alignment.
   - Adjust existing Import .H tests that asserted on `member_tree` values to assert against `layout_tree` in unified mode. Keep legacy assertions under a feature-flag guard if still required.

### A.7 Verify no regressions
7) Run full test suite. Validate:
   - CSV export button state unchanged.
   - Headless CI safeguards remain (skip GUI tests when no display/tkinter).
   - Presenter/Model APIs unaffected.

