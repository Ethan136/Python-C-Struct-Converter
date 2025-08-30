import io
import os

from src.export.csv_export import (
    CsvExportOptions,
    DefaultCsvExportService,
    CsvRowSerializer,
    CsvExportError,
)


def _sample_parsed_model():
    return {
        "fields": [
            {
                "entity_name": "Customer",
                "field_order": 1,
                "field_name": "Id",
                "physical_name": "ID",
                "data_type": "int",
                "length": None,
                "precision": 10,
                "scale": 0,
                "nullable": False,
                "default": None,
                "comment": "Primary key",
                "source_file": "customer.h",
                "source_line": 12,
                "tags": [],
            },
            {
                "entity_name": "Customer",
                "field_order": 2,
                "field_name": "Name",
                "physical_name": "NAME",
                "data_type": "VARCHAR",
                "length": 100,
                "precision": None,
                "scale": None,
                "nullable": False,
                "default": None,
                "comment": "Customer \"display\" name",
                "source_file": "customer.h",
                "source_line": 13,
                "tags": ["core", "pii"],
            },
        ]
    }


def test_row_serializer_basic_quotes_and_escaping():
    opts = CsvExportOptions()
    columns = ["field_name", "comment"]
    row = {"field_name": "Name", "comment": 'Customer "display" name'}
    s = CsvRowSerializer.serialize_row(row, columns, opts)
    # Expect quotes around comment because it contains quote and space
    assert s == 'Name,"Customer ""display"" name"'


def test_service_stream_basic_with_header():
    model = _sample_parsed_model()
    opts = CsvExportOptions(include_header=True)
    buf = io.StringIO()
    svc = DefaultCsvExportService()
    report = svc.export_to_csv(model, {"type": "stream", "stream": buf}, opts)
    out = buf.getvalue()
    assert report.records_written == 2
    assert report.header_written is True
    # header present
    assert out.splitlines()[0].startswith("entity_name,")
    # escaped quotes in second row
    assert 'Customer ""display"" name' in out


def test_service_file_bom_and_crlf(tmp_path):
    model = _sample_parsed_model()
    p = tmp_path / "out.csv"
    opts = CsvExportOptions(include_header=False, include_bom=True, line_ending="\r\n")
    svc = DefaultCsvExportService()
    report = svc.export_to_csv(model, {"type": "file", "path": str(p)}, opts)
    assert report.records_written == 2
    assert report.header_written is False
    # Verify BOM
    data = p.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")
    text = data.decode("utf-8-sig")
    assert "\r\n" in text


def test_invalid_options_raises():
    model = _sample_parsed_model()
    svc = DefaultCsvExportService()
    try:
        svc.export_to_csv(model, {"type": "file", "path": ""}, CsvExportOptions())
        raise AssertionError("Expected error not raised")
    except CsvExportError as e:
        assert e.code in ("INVALID_OPTIONS", "IO_ERROR")

