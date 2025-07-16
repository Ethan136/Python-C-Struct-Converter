import xml.etree.ElementTree as ET

class StructParserV2XMLTestLoader:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.cases = self._parse_cases()

    def _parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            line = case.find('line').text.strip()
            expected_elem = case.find('expected')
            expected = {
                'type': expected_elem.get('type'),
                'name': expected_elem.get('name')
            }
            if expected_elem.get('is_bitfield'):
                expected['is_bitfield'] = expected_elem.get('is_bitfield') == 'true'
            if expected_elem.get('bit_size'):
                expected['bit_size'] = int(expected_elem.get('bit_size'))
            cases.append({
                'name': case.get('name', ''),
                'line': line,
                'expected': expected
            })
        return cases

def load_struct_parser_v2_tests(xml_path):
    return StructParserV2XMLTestLoader(xml_path).cases
