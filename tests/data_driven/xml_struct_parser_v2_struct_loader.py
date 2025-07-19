import xml.etree.ElementTree as ET

def parse_expected_members(members_elem):
    members = []
    for m in members_elem.findall('member'):
        members.append({
            'type': m.get('type'),
            'name': m.get('name')
        })
    return members

def parse_expected_layout(layout_elem):
    layout = []
    for item in layout_elem.findall('item'):
        layout.append({
            'name': item.get('name'),
            'type': item.get('type'),
            'offset': int(item.get('offset')),
            'size': int(item.get('size'))
        })
    return layout

class StructParserV2StructXMLTestLoader:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.cases = self._parse_cases()

    def _parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            struct_def = case.find('struct_definition').text.strip()
            expected_struct_name = case.find('expected_struct_name').text.strip()
            expected_members = parse_expected_members(case.find('expected_members'))
            expected_layout = parse_expected_layout(case.find('expected_layout'))
            expected_total_size = int(case.find('expected_total_size').text.strip())
            expected_align = int(case.find('expected_align').text.strip())
            cases.append({
                'name': case.get('name', ''),
                'struct_definition': struct_def,
                'expected_struct_name': expected_struct_name,
                'expected_members': expected_members,
                'expected_layout': expected_layout,
                'expected_total_size': expected_total_size,
                'expected_align': expected_align
            })
        return cases

def load_struct_parser_v2_struct_tests(xml_path):
    return StructParserV2StructXMLTestLoader(xml_path).cases 