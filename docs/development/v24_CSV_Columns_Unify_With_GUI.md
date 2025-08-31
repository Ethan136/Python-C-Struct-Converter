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

#### 7) Implementation Steps (code edits checklist)
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

#### 9) Implementation Details (per file)
- `src/config/columns.py` (new):
  - Add constant:
    - `UNIFIED_LAYOUT_VALUE_COLUMNS = ["name", "type", "offset", "size", "bit_offset", "bit_size", "is_bitfield", "value", "hex_value", "hex_raw"]`
  - Optional helper:
    - `def get_unified_layout_value_columns(): return list(UNIFIED_LAYOUT_VALUE_COLUMNS)`

- `src/view/struct_view.py`:
  - Import: `from src.config.columns import UNIFIED_LAYOUT_VALUE_COLUMNS`
  - Ensure `LAYOUT_TREEVIEW_COLUMNS` includes entries for each of the unified names with their titles and widths, and in the same order:
    - `name`, `type`, `offset`, `size`, `bit_offset`, `bit_size`, `is_bitfield`, `value`, `hex_value`, `hex_raw`.
  - If any of the three value columns are currently appended inline, replace with a construction that derives from `UNIFIED_LAYOUT_VALUE_COLUMNS` to guarantee order alignment.
  - Keep existing i18n `title` keys: `layout_col_*` for layout columns and `member_col_*` for value columns.

- `src/export/csv_export.py`:
  - In `CsvExportOptions`:
    - Add fields: `columns_source = "gui_unified"`, `include_metadata = False`.
  - In `DefaultCsvExportService.export_to_csv(...)` column selection block:
    - If `opts.columns_source == "explicit"` and `opts.columns` is set: use `opts.columns`.
    - Elif `opts.columns_source == "legacy"`: keep existing behavior (DEFAULT_COLUMNS + layout/value appends).
    - Else (`gui_unified` default): `columns = list(UNIFIED_LAYOUT_VALUE_COLUMNS)`.
      - If `opts.include_metadata`: append `["entity_name", "field_order", "source_file", "source_line", "tags"]`.
  - In values computation section:
    - After deriving `row["value"]`, set `row["hex_value"] = hex(int(row["value"]))` when value is int/bool; else leave empty/None.
  - In `build_parsed_model_from_struct(...)`:
    - Add `"is_bitfield": bool(item.get("is_bitfield"))` to `row`.
    - Ensure `"name"` and `"type"` keys align with GUI naming.

- `tools/export_csv_from_h.py`:
  - argparse:
    - Add `--columns-source` with choices: `gui_unified`, `legacy`, `explicit` (default `gui_unified`).
    - Add `--include-metadata` flag (store_true).
    - If `--columns-source explicit` and `--columns` provided, pass through as-is.
    - Default value can read `os.environ.get("CSV_COLUMNS_SOURCE", "gui_unified")`.
  - Pass new options into `CsvExportOptions`.

- Documentation:
  - Update release notes (v24) and migration guide with header changes and how to switch to `legacy`.

#### 10) Test Plan (what to add/change)
- Unit tests (export):
  - `test_default_columns_are_gui_unified_order`: no options passed → header matches unified order.
  - `test_hex_value_is_present_and_correct`: with numeric and boolean values, verify `hex_value` correctness.
  - `test_bitfield_value_and_hex_value`: verify bitfield extraction and corresponding hex_value.
  - `test_include_metadata_appends_columns`: confirm appended metadata after unified set.
  - `test_columns_source_legacy_matches_v23`: verify byte-for-byte compatibility with previous behavior.
  - `test_columns_source_explicit_respects_order`: provide custom `columns` and verify output.
  - `test_invalid_columns_source_raises_or_ignores`: ensure invalid is handled.

- E2E XML-driven export tests:
  - Add `tests/resources/v24/cases.xml` with unified header expectations covering:
    - little/big endian
    - arrays, nested structs
    - bitfields (incl. anonymous)
  - Update loader to allow selecting `columnsSource` and `includeMetadata` per case.

- CLI tests (new `tests/tools/test_export_csv_from_h_cli.py`):
  - Verify `--columns-source gui_unified` default outputs unified header.
  - Verify `--columns-source legacy` reproduces V23 expectations.
  - Verify `--include-metadata` appends columns.
  - Verify `CSV_COLUMNS_SOURCE` environment variable defaulting.

- GUI tests (smoke):
  - Ensure `LAYOUT_TREEVIEW_COLUMNS` order/names align with `UNIFIED_LAYOUT_VALUE_COLUMNS`.
  - Ensure `hex_value` column is still present in GUI and remains unaffected by exporter changes.

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

#### 13) Documentation/Artifacts to Update After V24
- User/README docs:
  - `docs/development/v20_TargetStruct_UI_Sync_and_CSV_Export_GUI.md`: update CSV export description to reflect unified default header and new options.
  - `doc/development/v19-csv-export-tdd.md` (legacy): add a top note pointing to V24 unified columns and how to enable `legacy` mode.
  - Any user-facing README or How-To mentioning CSV columns and examples (add a new example with unified header).

- i18n resources:
  - `src/config/ui_strings.xml`: ensure keys for `layout_col_*` and `member_col_*` remain consistent; add any new labels if GUI changes wording.

- Developer docs and architecture notes:
  - `docs/development/v22_Unify_MemberValue_and_StructLayout.md`: reference that CSV now defaults to unified columns and includes `hex_value`.
  - `docs/development/v6_GUI_view.md`: if it enumerates column orders or names, align examples with `UNIFIED_LAYOUT_VALUE_COLUMNS`.
  - `docs/analysis/INPUT_CONVERSION_COMPLETE.md`: update any CSV column mapping tables.

- Tests and fixtures:
  - `tests/export/` unit tests: update expectations for default header/content to include `hex_value` in unified mode.
  - `tests/export/test_csv_export_xml_e2e.py` and loader `tests/data_driven/csv_export_xml_loader.py`: add support for `columnsSource` and `includeMetadata`; update/add v24 cases and expected CSV files under `tests/resources/v24/`.
  - `tests/view/test_struct_view.py`: smoke-check that `LAYOUT_TREEVIEW_COLUMNS` aligns with the unified list defined in `src/config/columns.py`.

- CLI help and examples:
  - `tools/export_csv_from_h.py`: update `--help` text, README usage examples, and document `--columns-source` and `--include-metadata` with samples.

- Changelog/Release notes:
  - Add V24 entry describing the default column change, migration path (`legacy` mode), and implications for downstream consumers.

