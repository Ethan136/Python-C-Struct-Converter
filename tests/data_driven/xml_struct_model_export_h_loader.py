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

def parse_expected_h_contains(h_elem):
    return [line.text.strip() for line in h_elem.findall('line')]

class StructModelExportHXMLTestLoader:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.cases = self._parse_cases()

    def _parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            members = parse_members(case.find('members'))
            total_size = int(case.find('total_size').text.strip())
            struct_name_elem = case.find('struct_name')
            struct_name = struct_name_elem.text.strip() if struct_name_elem is not None else None
            expected_h_contains = parse_expected_h_contains(case.find('expected_h_contains'))
            cases.append({
                'name': case.get('name', ''),
                'members': members,
                'total_size': total_size,
                'struct_name': struct_name,
                'expected_h_contains': expected_h_contains
            })
        return cases

def load_struct_model_export_h_tests(xml_path):
    return StructModelExportHXMLTestLoader(xml_path).cases 