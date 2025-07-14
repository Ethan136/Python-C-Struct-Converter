import xml.etree.ElementTree as ET

class StructParseDefinitionXMLTestLoader:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.cases = self.parse_cases()

    def parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            struct_def = case.find('struct_definition').text.strip()
            expect_none = case.find('expect_none') is not None
            expected_struct_name = None
            expected_members = []
            if not expect_none:
                expected_struct_name = case.find('expected_struct_name').text.strip()
                members_elem = case.find('expected_members')
                if members_elem is not None:
                    for m in members_elem.findall('member'):
                        member = {
                            'type': m.get('type'),
                            'name': m.get('name'),
                        }
                        if m.get('is_bitfield'):
                            member['is_bitfield'] = m.get('is_bitfield') == 'true'
                        if m.get('bit_size'):
                            member['bit_size'] = int(m.get('bit_size'))
                        expected_members.append(member)
            cases.append({
                'name': case.get('name', ''),
                'struct_definition': struct_def,
                'expect_none': expect_none,
                'expected_struct_name': expected_struct_name,
                'expected_members': expected_members
            })
        return cases

def load_struct_parse_definition_tests(xml_path):
    return StructParseDefinitionXMLTestLoader(xml_path).cases 