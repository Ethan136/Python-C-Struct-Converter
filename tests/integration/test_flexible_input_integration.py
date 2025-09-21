import unittest
import tempfile
import os
import io

from src.model.struct_model import StructModel
from src.presenter.struct_presenter import StructPresenter
from src.export.csv_export import DefaultCsvExportService, CsvExportOptions, build_parsed_model_from_struct


class MockFlexGridView:
    def __init__(self, flex_str: str = "", endian: str = "Little Endian"):
        self._flex = flex_str
        self._endian = endian
        self._grid_parts = []  # list of (raw, expected_chars)
        self.last_nodes = None
        self.last_context = None
    def get_flexible_input_string(self):
        return self._flex
    def set_flexible_input_string(self, s):
        self._flex = s
    def get_selected_endianness(self):
        return self._endian
    def get_hex_input_parts(self):
        return list(self._grid_parts)
    def set_grid_parts(self, parts):
        self._grid_parts = list(parts)
    def update_display(self, nodes, context):
        self.last_nodes = nodes
        self.last_context = context
    def on_values_refreshed(self):
        pass


class TestFlexibleInputIntegration(unittest.TestCase):
    def setUp(self):
        # Create a minimal 3-byte struct to avoid padding issues
        self.header_content = """
struct S {
    char a;
    char b;
    char c;
};
"""
        self.tmp = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.h')
        self.tmp.write(self.header_content)
        self.tmp.close()

        self.model = StructModel()
        name, layout, total, align = self.model.load_struct_from_file(self.tmp.name)
        self.assertEqual(total, 3, "Struct total_size should be 3 for three chars")

        self.view = MockFlexGridView()
        self.presenter = StructPresenter(self.model, self.view)
        # Make push_context immediate
        self.presenter._debounce_interval = 0
        orig_push = self.presenter.push_context
        def sync_push(*args, **kwargs):
            return orig_push(immediate=True)
        self.presenter.push_context = sync_push

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except Exception:
            pass

    def _combine_hex_raw(self, parsed_values):
        # concatenate per-field hex_raw in struct order
        return "".join((pv.get('hex_raw') or '') for pv in parsed_values)

    def test_flex_vs_grid_consistency(self):
        # flex: 0x01,0x0302 -> 01 02 03
        self.presenter.set_input_mode('flex_string')
        self.view.set_flexible_input_string("0x01,0x0302")
        res = self.presenter.parse_flexible_hex_input()
        self.assertEqual(res.get('type'), 'ok')
        combined_flex = self._combine_hex_raw(res.get('parsed_values'))
        self.assertEqual(combined_flex, '010203')

        # grid: three 1-byte boxes -> 01, 02, 03
        self.presenter.set_input_mode('grid')
        self.view.set_grid_parts([("01", 2), ("02", 2), ("03", 2)])
        res2 = self.presenter.parse_hex_data()
        self.assertEqual(res2.get('type'), 'ok')
        combined_grid = self._combine_hex_raw(res2.get('parsed_values'))
        self.assertEqual(combined_grid, '010203')

    def test_csv_export_uses_last_flex_hex(self):
        # flex parse to populate context.extra.last_flex_hex
        self.presenter.set_input_mode('flex_string')
        self.view.set_flexible_input_string("0x01,0x0302")
        res = self.presenter.parse_flexible_hex_input()
        self.assertEqual(res.get('type'), 'ok')
        last_hex = (self.presenter.context.get('extra', {}) or {}).get('last_flex_hex')
        self.assertEqual(last_hex, '010203')

        # Build parsed model and export to an in-memory stream using last_flex_hex
        parsed_model = build_parsed_model_from_struct(self.model)
        svc = DefaultCsvExportService()
        stream = io.StringIO()
        opts = CsvExportOptions(include_header=True, include_layout=True, include_values=True, endianness='little', hex_input=last_hex)
        report = svc.export_to_csv(parsed_model, {"type": "stream", "stream": stream}, opts)
        self.assertEqual(report.values_computed, 3)
        # Verify rows mutated with computed hex_raw per field
        rows = parsed_model.get('fields')
        self.assertEqual([r.get('hex_raw') for r in rows], ['01', '02', '03'])


if __name__ == '__main__':
    unittest.main()

