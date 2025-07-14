import xml.etree.ElementTree as ET
from tests.base_xml_test_loader import BaseXMLTestLoader

class ManualStructXMLTestLoader(BaseXMLTestLoader):
    def parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            data = self.parse_common_fields(case)
            extra = self.parse_extra(case)
            if extra:
                data.update(extra)
            cases.append(data)
        return cases

    def parse_common_fields(self, case):
        struct_name = self._get_text_or_none(case.find('struct_name'))
        total_size = int(self._get_text_or_none(case.find('total_size')) or 0)
        # 解析 members
        members = []
        members_elem = case.find('members')
        if members_elem is not None:
            for m in members_elem.findall('member'):
                member = {"name": m.get("name", ""), "type": m.get("type", ""), "bit_size": int(m.get("bit_size", 0))}
                members.append(member)
        # 解析 expected_errors
        expected_errors = []
        errors_elem = case.find('expected_errors')
        if errors_elem is not None:
            for err in errors_elem.findall('error'):
                if err.text:
                    expected_errors.append(err.text.strip())
        # 解析 expected_bits
        expected_bits = None
        bits_elem = case.find('expected_bits')
        if bits_elem is not None and bits_elem.text:
            expected_bits = int(bits_elem.text.strip())
        # 解析 expected_export_contains
        expected_export_contains = []
        export_elem = case.find('expected_export_contains')
        if export_elem is not None:
            for line in export_elem.findall('line'):
                if line.text:
                    expected_export_contains.append(line.text.strip())
        # 解析 expected_types
        expected_types = []
        types_elem = case.find('expected_types')
        if types_elem is not None:
            for t in types_elem.findall('type'):
                if t.text:
                    expected_types.append(t.text.strip())
        return {
            'name': case.attrib.get('name', ''),
            'description': case.attrib.get('description', ''),
            'struct_name': struct_name,
            'total_size': total_size,
            'members': members,
            'expected_errors': expected_errors,
            'expected_bits': expected_bits,
            'expected_export_contains': expected_export_contains,
            'expected_types': expected_types,
        }

    def parse_extra(self, case):
        return {}

def load_manual_struct_tests(xml_path):
    return ManualStructXMLTestLoader(xml_path).cases 