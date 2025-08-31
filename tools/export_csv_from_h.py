#!/usr/bin/env python3
"""CLI: Parse a .H file and export parsed layout to CSV (v19).

Usage:
  python tools/export_csv_from_h.py --input path/to/file.h --output out.csv \
    [--struct StructName] [--delimiter ,] [--no-header] [--bom] \
    [--line-ending CRLF] [--null NULL] [--columns col1,col2] \
    [--sort entity_name:ASC,field_order:ASC]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.model.struct_model import StructModel
from src.export.csv_export import (
    DefaultCsvExportService,
    CsvExportOptions,
    build_parsed_model_from_struct,
)


def parse_sort(spec: str):
    items = []
    for token in (spec or "").split(','):
        token = token.strip()
        if not token:
            continue
        if ':' in token:
            k, o = token.split(':', 1)
            items.append((k.strip(), o.strip().upper()))
        else:
            items.append((token, 'ASC'))
    return items or None


def main():
    ap = argparse.ArgumentParser(description="Export parsed .H layout to CSV (v19)")
    ap.add_argument("--input", required=True, help="Path to .h header file")
    ap.add_argument("--output", required=True, help="Path to output CSV file")
    ap.add_argument("--struct", dest="struct_name", help="Target struct/union name")
    ap.add_argument("--delimiter", default=",", help="CSV delimiter")
    ap.add_argument("--no-header", action="store_true", help="Do not include header row")
    ap.add_argument("--bom", action="store_true", help="Write UTF-8 BOM")
    ap.add_argument("--line-ending", choices=["LF", "CRLF"], default="LF")
    ap.add_argument("--null", dest="null_strategy", choices=["empty", "NULL", "dash"], default="empty")
    ap.add_argument("--columns", help="Comma-separated column names")
    ap.add_argument("--sort", dest="sort_by", help="Comma-separated sort spec like k1:ASC,k2:DESC")
    ap.add_argument("--include-layout", action="store_true", help="Include layout columns (offset/size/bit_*)")
    ap.add_argument("--include-values", action="store_true", help="Include values (value,hex_raw,hex_value)")
    ap.add_argument("--endianness", choices=["little", "big"], default="little")
    ap.add_argument("--hex", dest="hex_input", help="Hex string for value computation")
    # v24 options
    ap.add_argument("--columns-source", choices=["gui_unified", "legacy", "explicit"], default=os.environ.get("CSV_COLUMNS_SOURCE", "gui_unified"))
    ap.add_argument("--include-metadata", action="store_true", help="Append metadata columns after unified set")

    args = ap.parse_args()

    model = StructModel()
    model.load_struct_from_file(args.input, target_name=args.struct_name)
    parsed = build_parsed_model_from_struct(model)

    opts = CsvExportOptions(
        delimiter=args.delimiter,
        include_header=not args.no_header,
        include_bom=args.bom,
        line_ending="\n" if args.line_ending == "LF" else "\r\n",
        null_strategy=args.null_strategy,
        columns=[c.strip() for c in args.columns.split(',')] if args.columns else None,
        sort_by=parse_sort(args.sort_by) if args.sort_by else None,
        include_layout=args.include_layout,
        include_values=args.include_values,
        endianness=args.endianness,
        hex_input=(args.hex_input or None),
        columns_source=args.columns_source,
        include_metadata=args.include_metadata,
    )

    svc = DefaultCsvExportService()
    report = svc.export_to_csv(parsed, {"type": "file", "path": args.output}, opts)
    print(f"Wrote {report.records_written} records to {report.file_path} in {report.duration_ms} ms")


if __name__ == "__main__":
    main()

