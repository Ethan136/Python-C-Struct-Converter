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

class StructModelManualErrorXMLTestLoader:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.cases = self._parse_cases()

    def _parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            members = parse_members(case.find('members'))
            total_size = int(case.find('total_size').text.strip())
            expect_error = case.find('expect_error').text.strip()
            cases.append({
                'name': case.get('name', ''),
                'members': members,
                'total_size': total_size,
                'expect_error': expect_error
            })
        return cases

def load_struct_model_manual_error_tests(xml_path):
    return StructModelManualErrorXMLTestLoader(xml_path).cases 