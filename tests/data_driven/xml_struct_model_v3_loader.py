import xml.etree.ElementTree as ET
from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

class StructModelV3XMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        name = case.get('name', '')
        description = case.get('description', '')
        members = []
        members_elem = case.find('members')
        if members_elem is not None:
            for m in members_elem.findall('member'):
                members.append({
                    'name': m.get('name', ''),
                    'type': m.get('type', ''),
                    'bit_size': int(m.get('bit_size', '0')),
                })
        total_size_elem = case.find('total_size')
        total_size = int(total_size_elem.text.strip()) if total_size_elem is not None and total_size_elem.text else None
        expected_bits_elem = case.find('expected_bits')
        expected_bits = int(expected_bits_elem.text.strip()) if expected_bits_elem is not None and expected_bits_elem.text else None
        expected_export_contains = []
        export_elem = case.find('expected_export_contains')
        if export_elem is not None:
            for line in export_elem.findall('line'):
                if line.text:
                    expected_export_contains.append(line.text.strip())
        return {
            'name': name,
            'description': description,
            'members': members,
            'total_size': total_size,
            'expected_bits': expected_bits,
            'expected_export_contains': expected_export_contains,
        }

def load_struct_model_v3_tests(xml_path):
    return StructModelV3XMLTestLoader(xml_path).cases
