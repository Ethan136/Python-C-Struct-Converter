from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

def parse_member(elem):
    member = {'name': elem.get('name'), 'type': elem.get('type')}
    if elem.get('bit_size'):
        member['bit_size'] = int(elem.get('bit_size'))
    return member

class PresenterRefactorXMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        data = super().parse_common_fields(case)
        data['type'] = case.get('type')
        return data

    def parse_extra(self, case):
        members = []
        members_elem = case.find('members')
        if members_elem is not None:
            for m in members_elem.findall('member'):
                members.append(parse_member(m))
        expected_layout = []
        layout_elem = case.find('expected_layout')
        if layout_elem is not None:
            for item in layout_elem.findall('item'):
                entry = {'name': item.get('name'), 'type': item.get('type')}
                if item.get('size'):
                    entry['size'] = int(item.get('size'))
                expected_layout.append(entry)
        expected_remaining = None
        remain_elem = case.find('expected_remaining')
        if remain_elem is not None:
            expected_remaining = (
                int(remain_elem.get('bits')),
                int(remain_elem.get('bytes')),
            )
        return {'members': members, 'expected_layout': expected_layout, 'expected_remaining': expected_remaining}

def load_presenter_refactor_tests(xml_path):
    return PresenterRefactorXMLTestLoader(xml_path).cases
