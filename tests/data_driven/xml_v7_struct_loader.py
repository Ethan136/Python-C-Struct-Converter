import xml.etree.ElementTree as ET

class V7StructXMLLoader:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.cases = self._parse_cases()

    def _parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            struct_def = case.find('struct_definition').text.strip()
            expected = []
            for node in case.find('expected_flattened').findall('node'):
                entry = {
                    'name': node.get('name'),
                    'type': node.get('type')
                }
                if node.get('bit_size'):
                    entry['bit_size'] = int(node.get('bit_size'))
                if node.get('bit_offset'):
                    entry['bit_offset'] = int(node.get('bit_offset'))
                expected.append(entry)
            cases.append({
                'name': case.get('name', ''),
                'struct_definition': struct_def,
                'expected_flattened': expected
            })
        return cases

def load_v7_struct_tests(xml_path):
    return V7StructXMLLoader(xml_path).cases
