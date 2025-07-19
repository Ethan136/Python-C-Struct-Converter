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

def parse_expected_h_contains(h_elem):
    return [line.text.strip() for line in h_elem.findall('line')]

class StructModelExportHXMLTestLoader(BaseXMLTestLoader):
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
        struct_name_elem = case.find('struct_name')
        if struct_name_elem is not None:
            data['struct_name'] = struct_name_elem.text
        # 解析 expected_h_contains
        expected_h_contains = []
        h_elem = case.find('expected_h_contains')
        if h_elem is not None:
            for line in h_elem.findall('line'):
                expected_h_contains.append(line.text)
        data['expected_h_contains'] = expected_h_contains
        return data

def load_struct_model_export_h_tests(xml_path):
    return StructModelExportHXMLTestLoader(xml_path).cases 