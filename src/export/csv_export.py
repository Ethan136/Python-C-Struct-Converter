"""CSV export service for parsed .H results (v19).

Implements:
- CsvExportOptions
- ExportReport
- CsvExportError
- CsvRowSerializer
- CsvWritePipeline
- DefaultCsvExportService

Also includes a helper to adapt from StructModel to a generic parsed model.
"""

from __future__ import annotations

import io
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, TextIO, Tuple


# --------------------------- Exceptions & Types ------------------------------


class CsvExportError(Exception):
    def __init__(self, message: str, code: str = "IO_ERROR", details: Any = None):
        super().__init__(message)
        self.code = code
        self.details = details


@dataclass
class CsvExportOptions:
    delimiter: str = ","
    quote_char: str = '"'
    include_header: bool = True
    encoding: str = "UTF-8"
    line_ending: str = "\n"  # "\n" or "\r\n"
    null_strategy: str = "empty"  # "empty" | "NULL" | "dash"
    decimal_separator: str = "."  # "." | ","
    include_bom: bool = False
    columns: Optional[List[str]] = None
    sort_by: Optional[List[Tuple[str, str]]] = None  # [(key, 'ASC'|'DESC')]
    safe_cast: bool = True


@dataclass
class ExportReport:
    records_written: int
    header_written: bool
    file_path: Optional[str]
    duration_ms: int
    warnings: List[str] = field(default_factory=list)


# --------------------------- Row Serialization -------------------------------


class CsvRowSerializer:
    @staticmethod
    def _stringify(value: Any, options: CsvExportOptions) -> str:
        if value is None:
            if options.null_strategy == "NULL":
                return "NULL"
            if options.null_strategy == "dash":
                return "-"
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int,)):
            return str(value)
        if isinstance(value, float):
            s = ("%f" % value).rstrip("0").rstrip(".")
            if options.decimal_separator == ",":
                s = s.replace(".", ",")
            return s
        if isinstance(value, (list, tuple)):
            # join using '|', escape internal '|'
            return "|".join(str(x).replace("|", "\\|") for x in value)
        return str(value)

    @staticmethod
    def _needs_quote(s: str, delimiter: str, quote_char: str) -> bool:
        if s == "":
            return False
        if s[0].isspace() or s[-1].isspace():
            return True
        for ch in (delimiter, quote_char, "\n", "\r"):
            if ch and ch in s:
                return True
        return False

    @staticmethod
    def serialize_row(row: Dict[str, Any], columns: List[str], options: CsvExportOptions) -> str:
        parts: List[str] = []
        for col in columns:
            raw = row.get(col)
            s = CsvRowSerializer._stringify(raw, options)
            if options.quote_char in s:
                s = s.replace(options.quote_char, options.quote_char * 2)
            if CsvRowSerializer._needs_quote(s, options.delimiter, options.quote_char):
                s = f"{options.quote_char}{s}{options.quote_char}"
            parts.append(s)
        return options.delimiter.join(parts)


# ------------------------------- Writer Pipeline -----------------------------


class CsvWritePipeline:
    def __init__(self, output: TextIO, options: CsvExportOptions):
        self.output = output
        self.options = options

    def write_header(self, columns: List[str]) -> None:
        if not self.options.include_header:
            return
        line = CsvRowSerializer.serialize_row({c: c for c in columns}, columns, self.options)
        self._write_line(line)

    def write_rows(self, rows: Iterable[Dict[str, Any]], columns: List[str]) -> int:
        count = 0
        for row in rows:
            line = CsvRowSerializer.serialize_row(row, columns, self.options)
            self._write_line(line)
            count += 1
        return count

    def _write_line(self, s: str) -> None:
        self.output.write(s)
        self.output.write(self.options.line_ending)


# ------------------------------- Export Service ------------------------------


DEFAULT_COLUMNS = [
    "entity_name",
    "field_order",
    "field_name",
    "physical_name",
    "data_type",
    "length",
    "precision",
    "scale",
    "nullable",
    "default",
    "comment",
    "source_file",
    "source_line",
    "tags",
]


class DefaultCsvExportService:
    def export_to_csv(
        self,
        parsed_model: Dict[str, Any],
        output_target: Dict[str, Any],
        options: Optional[CsvExportOptions] = None,
    ) -> ExportReport:
        start = time.time()
        opts = options or CsvExportOptions()
        warnings: List[str] = []

        fields: List[Dict[str, Any]] = list(parsed_model.get("fields", []))
        if not fields:
            raise CsvExportError("Empty parsed model", code="EMPTY_MODEL")

        # Sorting
        if opts.sort_by:
            def _sort_key(row):
                key_vals = []
                for key, order in opts.sort_by or []:
                    key_vals.append((row.get(key), order))
                return tuple((v if o == 'ASC' else _desc(v)) for v, o in key_vals)

            def _desc(v):
                try:
                    return (0, v) if v is None else (1, v)
                except Exception:
                    return (0, None)

            try:
                # We sort using multiple keys by re-applying reversed for stable sort
                for key, order in reversed(opts.sort_by or []):
                    reverse = (order.upper() == 'DESC')
                    fields.sort(key=lambda r, k=key: r.get(k), reverse=reverse)
            except Exception as e:
                warnings.append(f"sort_by ignored due to error: {e}")

        # Columns
        columns = list(opts.columns) if opts.columns else list(DEFAULT_COLUMNS)
        # Validate columns
        for c in columns:
            if not isinstance(c, str) or not c:
                raise CsvExportError(f"Invalid column name: {c}", code="INVALID_OPTIONS")

        # Destination
        target_type = output_target.get("type")
        file_path: Optional[str] = None

        # Prepare text stream with encoding and BOM handling
        text_stream: Optional[TextIO] = None
        stream_to_close: Optional[TextIO] = None
        try:
            if target_type == "file":
                file_path = output_target.get("path")
                if not file_path:
                    raise CsvExportError("file path required", code="INVALID_OPTIONS")
                # Ensure parent directory exists
                parent = os.path.dirname(file_path)
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)
                bin_stream = open(file_path, "wb")
                if opts.include_bom and opts.encoding.upper().startswith("UTF-8"):
                    bin_stream.write(b"\xef\xbb\xbf")
                text_stream = io.TextIOWrapper(bin_stream, encoding=opts.encoding, newline="")
                stream_to_close = text_stream
            elif target_type == "stream":
                base_stream = output_target.get("stream")
                if base_stream is None:
                    raise CsvExportError("output stream required", code="INVALID_OPTIONS")
                # Assume text stream
                text_stream = base_stream
            else:
                raise CsvExportError("Unknown output target type", code="INVALID_OPTIONS")

            pipeline = CsvWritePipeline(text_stream, opts)
            if opts.include_header:
                pipeline.write_header(columns)
                header_written = True
            else:
                header_written = False
            num = pipeline.write_rows(fields, columns)
        except CsvExportError:
            raise
        except Exception as e:
            raise CsvExportError(str(e), code="IO_ERROR", details=e)
        finally:
            try:
                if stream_to_close is not None:
                    stream_to_close.flush()
                    stream_to_close.detach()  # close underlying binary stream too
            except Exception:
                pass

        duration_ms = int((time.time() - start) * 1000)
        return ExportReport(
            records_written=num,
            header_written=header_written,
            file_path=file_path,
            duration_ms=duration_ms,
            warnings=warnings,
        )


# ------------------------------ Adapter Helpers ------------------------------


def build_parsed_model_from_struct(struct_model: Any) -> Dict[str, Any]:
    """Build a generic parsed model dict from a StructModel instance.

    The model will follow the DEFAULT_COLUMNS keys as much as possible.
    Missing data is left as None for safe casting.
    """
    entity_name = getattr(struct_model, "struct_name", None) or ""
    layout = getattr(struct_model, "layout", [])
    fields: List[Dict[str, Any]] = []
    order = 1
    source_file = getattr(struct_model, "last_loaded_file_path", None)
    for item in layout:
        name = item.get("name") if isinstance(item, dict) else getattr(item, "name", None)
        if not name:
            continue
        if item.get("type") == "padding":
            continue
        row: Dict[str, Any] = {
            "entity_name": entity_name,
            "field_order": order,
            "field_name": name,
            "physical_name": None,
            "data_type": item.get("type"),
            "length": None,
            "precision": None,
            "scale": None,
            "nullable": False,
            "default": None,
            "comment": None,
            "source_file": source_file or None,
            "source_line": 0,
            "tags": ["bitfield"] if item.get("is_bitfield") else [],
        }
        fields.append(row)
        order += 1
    return {"fields": fields, "metadata": {"entity": entity_name}}

