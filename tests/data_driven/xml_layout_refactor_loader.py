from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

def parse_members(elem):
    members = []
    if elem is not None:
        for m in elem.findall('member'):
            members.append((m.get('type'), m.get('name')))
    return members

class LayoutRefactorXMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        data = super().parse_common_fields(case)
        data['type'] = case.get('type')
        return data

    def parse_extra(self, case):
        return {
            'members': parse_members(case.find('members'))
        }

def load_layout_refactor_tests(xml_path):
    return LayoutRefactorXMLTestLoader(xml_path).cases
