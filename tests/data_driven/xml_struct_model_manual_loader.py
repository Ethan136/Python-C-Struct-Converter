import xml.etree.ElementTree as ET

def parse_members(members_elem):
    members = []
    for m in members_elem.findall('member'):
        members.append({
            'name': m.get('name'),
            'type': m.get('type'),
            'bit_size': int(m.get('bit_size', '0'))
        })
    return members

def parse_expected_layout(layout_elem):
    layout = []
    for item in layout_elem.findall('item'):
        layout.append({
            'name': item.get('name'),
            'type': item.get('type'),
            'offset': int(item.get('offset')),
            'size': int(item.get('size')),
            'bit_offset': int(item.get('bit_offset', '0')),
            'bit_size': int(item.get('bit_size', '0'))
        })
    return layout

class StructModelManualXMLTestLoader:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.cases = self._parse_cases()

    def _parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            members = parse_members(case.find('members'))
            total_size = int(case.find('total_size').text.strip())
            expected_layout = parse_expected_layout(case.find('expected_layout'))
            cases.append({
                'name': case.get('name', ''),
                'members': members,
                'total_size': total_size,
                'expected_layout': expected_layout
            })
        return cases

def load_struct_model_manual_tests(xml_path):
    return StructModelManualXMLTestLoader(xml_path).cases 