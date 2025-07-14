import unittest
from model.struct_parser import parse_member_line, _extract_struct_body

class TestParseMemberLine(unittest.TestCase):
    def test_regular_member(self):
        self.assertEqual(parse_member_line('int value'), ('int', 'value'))

    def test_pointer_member(self):
        self.assertEqual(parse_member_line('char* ptr'), ('pointer', 'ptr'))

    def test_bitfield_member(self):
        result = parse_member_line('int flag : 3')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'int')
        self.assertEqual(result['name'], 'flag')
        self.assertTrue(result['is_bitfield'])
        self.assertEqual(result['bit_size'], 3)

    def test_array_member_dims(self):
        result = parse_member_line('short data[4][2]')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'short')
        self.assertEqual(result['name'], 'data')
        self.assertEqual(result.get('array_dims'), [4, 2])


class TestExtractStructBody(unittest.TestCase):
    def test_simple_body_extraction(self):
        content = """
        struct Simple {
            int a;
            char b;
        };
        """
        name, body = _extract_struct_body(content)
        self.assertEqual(name, "Simple")
        self.assertIn("int a;", body)
        self.assertIn("char b;", body)

if __name__ == '__main__':
    unittest.main()
