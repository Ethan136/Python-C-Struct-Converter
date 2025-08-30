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

### 11) Migration Notes
- No Model/Presenter API changes in V22; View-only changes with a feature flag.
- Downstream customizations relying on `member_tree` should switch to unified mode columns; legacy mode remains available temporarily.

### 12) Follow-ups (Post-V22)
- Consider unifying manual struct tab to the same model for consistency.
- Add per-column show/hide management and saved user preferences.
- Optional: enrich CSV export to include value columns when available.

