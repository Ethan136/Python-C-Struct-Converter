import os
import io
import unittest

from tests.data_driven.csv_export_xml_loader import load_csv_export_cases
from src.model.struct_model import StructModel
from src.export.csv_export import DefaultCsvExportService, CsvExportOptions, build_parsed_model_from_struct


class TestCSVExportXML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = os.path.join(os.path.dirname(__file__), '..', 'resources', 'v19')
        cls.xml_path = os.path.join(cls.base, 'cases.xml')

    def test_xml_cases(self):
        if not os.path.exists(self.xml_path):
            self.skipTest("v19 cases.xml not found")
        cases = load_csv_export_cases(self.xml_path)
        for c in cases:
            with self.subTest(case=c.id or c.name):
                model = StructModel()
                model.load_struct_from_file(c.input_file)
                parsed = build_parsed_model_from_struct(model)
                # prepare options
                columns = [x.strip() for x in c.options['columns'].split(',')] if c.options['columns'] else None
                sortBy = None
                if c.options['sortBy']:
                    sortBy = []
                    for t in c.options['sortBy'].split(','):
                        if not t: continue
                        if ':' in t:
                            k, o = t.split(':', 1)
                            sortBy.append((k.strip(), o.strip().upper()))
                        else:
                            sortBy.append((t.strip(), 'ASC'))
                opts = CsvExportOptions(
                    delimiter=c.options['delimiter'],
                    include_header=c.options['includeHeader'],
                    encoding=c.options['encoding'],
                    include_bom=c.options['includeBom'],
                    line_ending='\n' if c.options['lineEnding'] == 'LF' else '\r\n',
                    null_strategy=c.options['nullStrategy'],
                    columns=columns,
                    sort_by=sortBy,
                    safe_cast=c.options['safeCast'],
                    include_layout=c.options['includeLayout'],
                    include_values=c.options['includeValues'],
                    endianness=c.options['endianness'],
                    hex_input=c.hex_value,
                )
                svc = DefaultCsvExportService()
                buf = io.StringIO()
                svc.export_to_csv(parsed, {"type": "stream", "stream": buf}, opts)
                out = buf.getvalue().encode('utf-8')
                expected = open(c.output_file, 'rb').read()
                self.assertEqual(out, expected)


if __name__ == '__main__':
    unittest.main()

