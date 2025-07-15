import unittest
from model.struct_parser import parse_c_definition, parse_c_definition_ast, UnionDef

class TestUnionParser(unittest.TestCase):
    def test_parse_union_definition(self):
        content = """
        union U {
            int a;
            char b;
        };
        """
        kind, name, members = parse_c_definition(content)
        self.assertEqual(kind, 'union')
        self.assertEqual(name, 'U')
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0], ('int', 'a'))
        self.assertEqual(members[1], ('char', 'b'))

    def test_parse_union_definition_ast(self):
        content = """
        union U {
            int a;
            char b;
        };
        """
        result = parse_c_definition_ast(content)
        self.assertIsInstance(result, UnionDef)
        self.assertEqual(result.name, 'U')
        self.assertEqual(len(result.members), 2)
        self.assertEqual(result.members[0].type, 'int')
        self.assertEqual(result.members[0].name, 'a')
        self.assertEqual(result.members[1].type, 'char')
        self.assertEqual(result.members[1].name, 'b')

if __name__ == '__main__':
    unittest.main()
