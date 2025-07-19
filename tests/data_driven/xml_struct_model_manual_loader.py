import xml.etree.ElementTree as ET
from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

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

class StructModelManualXMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        data = super().parse_common_fields(case)
        members_elem = case.find('members')
        members = []
        if members_elem is not None:
            for m in members_elem.findall('member'):
                members.append({
                    'name': m.get('name'),
                    'type': m.get('type'),
                    'bit_size': int(m.get('bit_size', '0'))
                })
        data['members'] = members
        total_size_elem = case.find('total_size')
        if total_size_elem is not None:
            data['total_size'] = int(total_size_elem.text)
        # 解析 expected_layout
        expected_layout = []
        layout_elem = case.find('expected_layout')
        if layout_elem is not None:
            for item in layout_elem.findall('item'):
                expected_layout.append({k: item.get(k) for k in item.keys()})
        data['expected_layout'] = expected_layout
        # 解析 expect_error
        expect_error_elem = case.find('expect_error')
        if expect_error_elem is not None:
            data['expect_error'] = expect_error_elem.text
        return data

def load_struct_model_manual_tests(xml_path):
    return StructModelManualXMLTestLoader(xml_path).cases 