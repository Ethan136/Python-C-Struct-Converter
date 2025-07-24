import sys, types; sys.modules.setdefault("jsonschema", types.ModuleType("jsonschema"))
import os
from src.model.parser import V7StructParser
from src.model.flattening_strategy import StructFlatteningStrategy
from tests.data_driven.xml_v7_struct_loader import load_v7_struct_tests

class TestV7XMLParsingFlattening:
    @classmethod
    def setup_class(cls):
        xml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_struct_v7_config.xml')
        cls.cases = load_v7_struct_tests(xml_path)
        cls.parser = V7StructParser()
        cls.strategy = StructFlatteningStrategy()

    def test_v7_cases(self):
        for case in self.cases:
            struct = self.parser.parse_struct_definition(case['struct_definition'])
            assert struct is not None
            flattened = self.strategy.flatten_node(struct)
            def norm(name):
                parts = []
                for p in name.split('.'):
                    if p.startswith('anonymous_'):
                        parts.append('anonymous')
                    else:
                        parts.append(p)
                return '.'.join(parts)

            names = [norm(n.name) for n in flattened]
            expected_names = [norm(e['name']) for e in case['expected_flattened']]
            assert names == expected_names
            for node, expect in zip(flattened, case['expected_flattened']):
                assert node.type == expect['type']
                if 'bit_size' in expect:
                    assert node.bit_size == expect['bit_size']
                if 'bit_offset' in expect:
                    assert node.bit_offset == expect['bit_offset']
