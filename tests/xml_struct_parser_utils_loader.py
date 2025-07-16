import xml.etree.ElementTree as ET

class StructParserUtilsXMLTestLoader:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.member_cases = self._parse_member_cases()
        self.body_cases = self._parse_body_cases()

    def _parse_member_cases(self):
        cases = []
        member_section = self.root.find('parse_member_line_cases')
        if member_section is not None:
            for case in member_section.findall('case'):
                line = case.find('line').text.strip()
                expected_elem = case.find('expected')
                expected = dict(expected_elem.attrib)
                return_type = expected.pop('return_type', 'tuple')
                if 'is_bitfield' in expected:
                    expected['is_bitfield'] = expected['is_bitfield'] == 'true'
                if 'bit_size' in expected:
                    expected['bit_size'] = int(expected['bit_size'])
                if 'array_dims' in expected:
                    expected['array_dims'] = [int(x) for x in expected['array_dims'].split(',') if x.strip()]
                cases.append({
                    'name': case.get('name', ''),
                    'line': line,
                    'expected': expected,
                    'return_type': return_type,
                    'xfail': case.get('xfail', 'false') == 'true'
                })
        return cases

    def _parse_body_cases(self):
        cases = []
        body_section = self.root.find('extract_struct_body_cases')
        if body_section is not None:
            for case in body_section.findall('case'):
                content = case.find('content').text
                expected_name = case.find('expected_name').text.strip()
                expected_lines = []
                ec = case.find('expected_contains')
                if ec is not None:
                    for line in ec.findall('line'):
                        if line.text:
                            expected_lines.append(line.text.strip())
                cases.append({
                    'name': case.get('name', ''),
                    'content': content,
                    'expected_name': expected_name,
                    'expected_contains': expected_lines
                })
        return cases

def load_struct_parser_utils_tests(xml_path):
    loader = StructParserUtilsXMLTestLoader(xml_path)
    return loader.member_cases, loader.body_cases
