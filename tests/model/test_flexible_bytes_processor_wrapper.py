import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.model.input_field_processor import InputFieldProcessor


class TestFlexibleBytesProcessorWrapper(unittest.TestCase):
    def setUp(self):
        self.p = InputFieldProcessor()

    def test_wrapper_success(self):
        res = self.p.process_flexible_input("0x01,0x0203", None)
        self.assertEqual(res.data.hex(), "010302")
        self.assertFalse(res.warnings)

    def test_wrapper_with_padding_and_truncation(self):
        # padding
        res = self.p.process_flexible_input("0x01", 2)
        self.assertEqual(res.data.hex(), "0100")
        self.assertTrue(res.warnings)

        # truncation
        res2 = self.p.process_flexible_input("0x01,0x0302", 2)
        self.assertEqual(res2.data.hex(), "0102")
        self.assertTrue(res2.warnings)

    def test_wrapper_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.p.process_flexible_input("0x, 01", None)


if __name__ == "__main__":
    unittest.main()
