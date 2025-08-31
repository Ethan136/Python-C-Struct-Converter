import unittest

from src.model.struct_model import StructModel


class TestV25UnifiedRows(unittest.TestCase):
    def test_build_unified_rows_after_parse(self):
        m = StructModel()
        # Prepare a simple layout with one normal int and one bitfield in same storage
        m.layout = [
            {
                "name": "field_int",
                "type": "int",
                "size": 4,
                "offset": 0,
                "is_bitfield": False,
                "bit_offset": 0,
                "bit_size": 32,
            },
            {
                "name": "field_bf",
                "type": "int",
                "size": 4,
                "offset": 0,
                "is_bitfield": True,
                "bit_offset": 8,
                "bit_size": 8,
            },
        ]
        m.total_size = 4

        # hex bytes: 78 56 34 12 -> little-endian value = 0x12345678 = 305419896
        parsed = m.parse_hex_data("78563412", "little")
        self.assertIsInstance(parsed, list)
        rows = m.build_unified_rows()
        self.assertGreaterEqual(len(rows), 2)

        # Validate normal int row
        r0 = next(r for r in rows if r["name"] == "field_int")
        for k in [
            "name",
            "type",
            "offset",
            "size",
            "bit_offset",
            "bit_size",
            "is_bitfield",
            "value",
            "hex_value",
            "hex_raw",
        ]:
            self.assertIn(k, r0)
        self.assertEqual(r0["value"], "305419896")
        self.assertEqual(r0["hex_value"], hex(0x12345678))
        # hex_raw reflects big-endian byte order of the slice
        self.assertEqual(r0["hex_raw"], "78563412")

        # Validate bitfield row (extract 8 bits at offset 8 -> 0x56 = 86)
        r1 = next(r for r in rows if r["name"] == "field_bf")
        self.assertEqual(r1["value"], "86")
        self.assertEqual(r1["hex_value"], hex(0x56))
        self.assertEqual(r1["hex_raw"], "78563412")


if __name__ == "__main__":
    unittest.main()

