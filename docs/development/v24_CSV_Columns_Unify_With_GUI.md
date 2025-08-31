### V24: CSV export columns match GUI unified Struct Layout + Member Value

#### 1) Goal
- Make CSV export columns exactly match the GUI unified table columns used on Import .H (layout + values) by default.
- Remove confusion between legacy CSV default columns and GUI-visible columns.

#### 2) Scope
- In scope:
  - Define a single source of truth for the unified GUI columns (order, ids) and reuse it in CSV export defaults.
  - Add `hex_value` to CSV output by default when values are included.
  - Keep optional metadata columns (entity_name, field_order, source_file, source_line, tags) configurable.
- Out of scope:
  - Changing GUI visuals/wording beyond column identity/order already established in V22.
  - Any schema change to struct parsing or layout calculation.

#### 3) Current Behavior (V23)
- GUI unified columns (V22 spec): `name`, `type`, `offset`, `size`, `bit_offset`, `bit_size`, `is_bitfield`, `value`, `hex_value`, `hex_raw`.
- CSV default columns (src/export/csv_export.py): a generic DEFAULT_COLUMNS, then optionally appends `offset`, `size`, `bit_offset`, `bit_size`, and value fields `value`, `hex_raw` when enabled. It does NOT include `hex_value`, and uses different naming like `field_name` instead of `name`.

#### 4) Design Overview
- Establish a shared columns definition module: `src/config/columns.py`.
  - Export `UNIFIED_LAYOUT_VALUE_COLUMNS = ["name", "type", "offset", "size", "bit_offset", "bit_size", "is_bitfield", "value", "hex_value", "hex_raw"]`.
  - GUI (`src/view/struct_view.py`) and CSV export (`src/export/csv_export.py`) both import from this module, avoiding cross-layer imports.
- CSV export default behavior in V24:
  - By default, when `include_layout=True` and/or `include_values=True`, the CSV header is exactly `UNIFIED_LAYOUT_VALUE_COLUMNS` in that order.
  - `hex_value` is produced alongside `value`/`hex_raw` for numeric values; non-numeric or unavailable values result in empty per null strategy.
  - Optional metadata columns can be included via a new flag; see Options below.
- Data mapping consistency:
  - Ensure `build_parsed_model_from_struct(...)` populates row keys needed by unified columns: `name`, `type`, `offset`, `size`, `bit_offset`, `bit_size`, `is_bitfield`.
  - Retain backward keys (e.g., `field_name`) internally for legacy mode; not used by the new default.

#### 5) Options/API Changes
- `CsvExportOptions` additions:
  - `columns_source: Literal["gui_unified", "legacy", "explicit"] = "gui_unified"`
    - `gui_unified`: use `UNIFIED_LAYOUT_VALUE_COLUMNS` by default; if `include_layout=False` or `include_values=False`, still emit the unified header but value/layout cells may be empty per null strategy.
    - `legacy`: preserve V23 column composition behavior (DEFAULT_COLUMNS + layout/value appends), for compatibility.
    - `explicit`: use `columns` exactly as provided by caller.
  - `include_metadata: bool = False` (default). When True, append metadata columns after the unified set: `entity_name`, `field_order`, `source_file`, `source_line`, `tags`.
- Behavior changes:
  - Compute and output `hex_value` whenever `include_values` is True and a numeric `value` can be derived (from `hex_input` or `value_provider`).
  - Export `is_bitfield` as boolean (true/false) aligned with GUI semantics.

#### 6) Backward Compatibility
- Default switches to `columns_source="gui_unified"` in V24 (breaking header for consumers relying on V23 defaults). Mitigations:
  - Provide `columns_source="legacy"` to fully restore V23 header behavior.
  - CLI flag `--columns-source legacy|gui_unified|explicit` with default `gui_unified`.
  - Release notes and migration guide: advise consumers to either pin `legacy` or update their parsers to the new unified header.

#### 7) Implementation Steps
1) Create `src/config/columns.py` with `UNIFIED_LAYOUT_VALUE_COLUMNS`.
2) Update `src/view/struct_view.py` to import and use `UNIFIED_LAYOUT_VALUE_COLUMNS` in building `LAYOUT_TREEVIEW_COLUMNS` (append value columns as already planned in V22, but now sourced centrally).
3) Update `src/export/csv_export.py`:
   - Add new `CsvExportOptions` fields and logic for `columns_source`/`include_metadata`.
   - When `columns_source == "gui_unified"`, set `columns = UNIFIED_LAYOUT_VALUE_COLUMNS (+ metadata if requested)` unless `explicit` is chosen.
   - Compute `hex_value` when `include_values` (use `hex(int(value))` for numeric/boolean; empty if not applicable).
   - Ensure rows contain `name` and `is_bitfield` keys; add `is_bitfield` to `build_parsed_model_from_struct(...)` rows.
4) Update CLI `tools/export_csv_from_h.py` to pass through `--columns-source` and `--include-metadata`.
5) Documentation and release notes updates.

#### 8) Acceptance Criteria
- Default CSV header equals exactly: `name,type,offset,size,bit_offset,bit_size,is_bitfield,value,hex_value,hex_raw` (in this order).
- Values exported match GUI rendering rules:
  - `value` numeric/boolean derived from `hex_input` and endianness with bitfield handling.
  - `hex_value` is `hex(int(value))` for numeric/boolean values; otherwise empty per null strategy.
  - `hex_raw` uses normalized big-endian representation as in current V23 behavior.
- Enabling `include_metadata` appends the 5 metadata columns at the end, preserving the unified header order at the front.
- Setting `columns_source=legacy` reproduces V23 outputs bit-by-bit on existing tests.

#### 9) Test Plan
- Unit tests (export):
  - `test_default_columns_are_gui_unified_order`
  - `test_hex_value_is_present_and_correct`
  - `test_bitfield_value_and_hex_value`
  - `test_include_metadata_appends_columns`
  - `test_columns_source_legacy_matches_v23`
  - `test_columns_source_explicit_respects_order`
- E2E XML-driven export tests:
  - Update/add v24 suite with expected headers for unified mode and coverage for little/big endian, arrays, nested structs, bitfields.
- GUI tests (smoke):
  - Verify `LAYOUT_TREEVIEW_COLUMNS` still matches unified schema imported from `src/config/columns.py`.

#### 10) Risks & Mitigations
- Cross-module dependency: avoid importing view from export; use `src/config/columns.py` as a neutral module.
- Backward compatibility: default change may break consumer pipelines; provide `legacy` mode and clear documentation.
- Performance: computing `hex_value` is trivial compared to existing value/hex_raw computation; negligible impact.

#### 11) Rollout
- Behind a soft flag: environment variable `CSV_COLUMNS_SOURCE` read by CLI defaults (overridable by CLI arg), defaulting to `gui_unified` in V24.
- Staged release: ship with both modes and deprecate `legacy` in a future version.

#### 12) Follow-ups (Post-V24)
- Per-column show/hide for CSV mirroring GUI user preferences (if/when GUI adds preference persistence for columns).
- Optional localized CSV headers by mapping ids to i18n strings (currently headers use column ids).

