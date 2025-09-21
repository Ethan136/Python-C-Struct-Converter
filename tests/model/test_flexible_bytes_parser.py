import unittest
import sys
import os

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model import flexible_bytes_parser as fbp


class TestFlexibleBytesParserTokenize(unittest.TestCase):
    def test_tokenize_basic_and_mixed_separators(self):
        cases = [
            ("0x01,0x02,0x03", ["0x01", "0x02", "0x03"]),
            ("0x01, 0x02, 0x03", ["0x01", "0x02", "0x03"]),
            ("0x01 0x02 0x03", ["0x01", "0x02", "0x03"]),
            ("0x01\t0x02\t0x03", ["0x01", "0x02", "0x03"]),
            ("0x01 ,  0x02\t,0x03", ["0x01", "0x02", "0x03"]),
            ("   0x01 ,  0x02   ", ["0x01", "0x02"]),
            (",,,0x01,,,0x02,,,", ["0x01", "0x02"]),
            ("", []),
            ("   \t ,  ", []),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(fbp.tokenize_flexible_hex(raw), expected)


class TestFlexibleBytesParserParseToken(unittest.TestCase):
    def test_parse_token_little_endian_and_padding(self):
        # Basic little-endian expansion
        self.assertEqual(fbp.parse_token_to_bytes("0x01"), bytes.fromhex("01"))
        self.assertEqual(fbp.parse_token_to_bytes("0x0201"), bytes.fromhex("01 02"))
        self.assertEqual(fbp.parse_token_to_bytes("0x030201"), bytes.fromhex("01 02 03"))

        # Odd digits pad left with 0 (0xABC -> 0x0ABC -> BC 0A in LE)
        self.assertEqual(fbp.parse_token_to_bytes("0xABC"), bytes.fromhex("BC 0A"))

        # Underscores and uppercase prefix supported
        self.assertEqual(fbp.parse_token_to_bytes("0xAB_CD_EF"), bytes.fromhex("EF CD AB"))
        self.assertEqual(fbp.parse_token_to_bytes("0Xab"), bytes.fromhex("ab"))

    def test_parse_token_invalid(self):
        invalid = [
            "0x",        # missing digits
            "0xG1",      # non-hex char
            "01",        # missing 0x prefix
            "0x 01",     # whitespace inside token
        ]
        for tok in invalid:
            with self.subTest(tok=tok):
                with self.assertRaises(ValueError):
                    fbp.parse_token_to_bytes(tok)


class TestFlexibleBytesParserAssemble(unittest.TestCase):
    def test_assemble_no_target_len(self):
        tokens = ["0x01", "0x0302"]
        data, meta = fbp.assemble_bytes(tokens, target_len=None)
        self.assertEqual(data.hex(), "010203")
        self.assertFalse(meta.get("warnings"))
        self.assertFalse(meta.get("trunc_info"))
        self.assertEqual(len(meta.get("byte_spans", [])), 3)

    def test_assemble_fixed_len_padding(self):
        tokens = ["0x01"]
        data, meta = fbp.assemble_bytes(tokens, target_len=3)
        # expect 01 00 00
        self.assertEqual(data.hex(), "010000")
        # padding range should be indices 1..2
        pad = meta.get("padding_info")
        self.assertIsNotNone(pad)
        self.assertEqual(pad["from"], 1)
        self.assertEqual(pad["to"], 2)
        self.assertTrue(meta.get("warnings"))
        # spans for padded bytes marked
        spans = meta.get("byte_spans", [])
        self.assertEqual(len(spans), 3)
        self.assertTrue(all(isinstance(s, dict) for s in spans))
        self.assertTrue(spans[1].get("padded"))
        self.assertTrue(spans[2].get("padded"))

    def test_assemble_fixed_len_truncate(self):
        tokens = ["0x01", "0x0302"]  # -> 01 02 03
        data, meta = fbp.assemble_bytes(tokens, target_len=2)
        # expect keep head 01 02, truncate tail 03
        self.assertEqual(data.hex(), "0102")
        trunc = meta.get("trunc_info")
        self.assertTrue(trunc)
        self.assertEqual(trunc[0]["global_index"], 2)
        self.assertEqual(trunc[0]["token_index"], 1)  # token 1 is "0x0302"
        self.assertEqual(trunc[0]["offset"], 1)       # byte offset within that token (LE)
        self.assertTrue(meta.get("warnings"))


class TestFlexibleBytesParserIntegrated(unittest.TestCase):
    def test_parse_flexible_input_ok_cases(self):
        cases = [
            ("0x030201", None, "010203"),
            ("0x01,0x02,0x03", None, "010203"),
            ("0x01, 0x0302", None, "010203"),
            ("0x0201 0x03", None, "010203"),
        ]
        for raw, n, expected_hex in cases:
            with self.subTest(raw=raw):
                res = fbp.parse_flexible_input(raw, n)
                self.assertEqual(res.data.hex(), expected_hex)
                self.assertFalse(res.warnings)
                self.assertFalse(res.trunc_info)

    def test_parse_flexible_input_invalid_tokens(self):
        raw = "0x01, 0x, 0xGG, 01"
        with self.assertRaises(ValueError) as cm:
            fbp.parse_flexible_input(raw, None)
        msg = str(cm.exception)
        # Should point out each invalid token position (2-based for 0x?)
        self.assertIn("token #2", msg)
        self.assertIn("token #3", msg)
        self.assertIn("token #4", msg)

    def test_parse_flexible_input_fixed_len_padding_and_truncation(self):
        res = fbp.parse_flexible_input("0x01", 3)
        self.assertEqual(res.data.hex(), "010000")
        self.assertTrue(res.warnings)
        self.assertTrue(res.byte_spans[1]["padded"])  # padded markers

        res2 = fbp.parse_flexible_input("0x01,0x0302", 2)
        self.assertEqual(res2.data.hex(), "0102")
        self.assertTrue(res2.trunc_info)
        self.assertTrue(res2.warnings)


if __name__ == "__main__":
    unittest.main()

