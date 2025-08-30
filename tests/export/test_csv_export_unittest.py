import io
import os
import unittest

from src.export.csv_export import (
    CsvExportOptions,
    DefaultCsvExportService,
    CsvRowSerializer,
    CsvExportError,
)


class TestCsvExport(unittest.TestCase):
    def test_row_serializer_basic_quotes_and_escaping(self):
        opts = CsvExportOptions()
        columns = ["field_name", "comment"]
        row = {"field_name": "Name", "comment": 'Customer "display" name'}
        s = CsvRowSerializer.serialize_row(row, columns, opts)
        self.assertEqual(s, 'Name,"Customer ""display"" name"')

    def test_service_stream_basic_with_header(self):
        model = {
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
                    "comment": 'Customer "display" name',
                    "source_file": "customer.h",
                    "source_line": 13,
                    "tags": ["core", "pii"],
                },
            ]
        }
        opts = CsvExportOptions(include_header=True)
        buf = io.StringIO()
        svc = DefaultCsvExportService()
        report = svc.export_to_csv(model, {"type": "stream", "stream": buf}, opts)
        out = buf.getvalue()
        self.assertEqual(report.records_written, 2)
        self.assertTrue(report.header_written)
        self.assertTrue(out.splitlines()[0].startswith("entity_name,"))
        self.assertIn('Customer ""display"" name', out)

    def test_service_file_bom_and_crlf(self):
        model = {
            "fields": [
                {
                    "entity_name": "Customer",
                    "field_order": 1,
                    "field_name": "Id",
                    "physical_name": "ID",
                    "data_type": "int",
                    "nullable": False,
                    "source_file": "customer.h",
                    "source_line": 12,
                },
                {
                    "entity_name": "Customer",
                    "field_order": 2,
                    "field_name": "Name",
                    "physical_name": "NAME",
                    "data_type": "VARCHAR",
                    "length": 100,
                    "nullable": False,
                    "comment": 'Customer "display" name',
                    "source_file": "customer.h",
                    "source_line": 13,
                },
            ]
        }
        opts = CsvExportOptions(include_header=False, include_bom=True, line_ending="\r\n")
        svc = DefaultCsvExportService()
        out_path = os.path.join(os.path.dirname(__file__), "tmp_out.csv")
        try:
            report = svc.export_to_csv(model, {"type": "file", "path": out_path}, opts)
            self.assertEqual(report.records_written, 2)
            self.assertFalse(report.header_written)
            data = open(out_path, "rb").read()
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
            text = data.decode("utf-8-sig")
            self.assertIn("\r\n", text)
        finally:
            try:
                os.remove(out_path)
            except Exception:
                pass

    def test_invalid_options_raises(self):
        model = {"fields": [{"entity_name": "E", "field_order": 1, "field_name": "f"}]}
        svc = DefaultCsvExportService()
        with self.assertRaises(CsvExportError):
            svc.export_to_csv(model, {"type": "file", "path": ""}, CsvExportOptions())


if __name__ == "__main__":
    unittest.main()

