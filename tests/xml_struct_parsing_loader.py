from tests.base_xml_test_loader import BaseXMLTestLoader

class StructParsingXMLTestLoader(BaseXMLTestLoader):
    """Load struct parsing test cases from XML."""

    def parse_extra(self, case):
        extra = {}
        name_elem = case.find('expected_struct_name')
        if name_elem is not None and name_elem.text:
            extra['expected_struct_name'] = name_elem.text.strip()
        members_elem = case.find('expected_members')
        if members_elem is not None:
            expected_members = []
            for m in members_elem.findall('member'):
                member = {'type': m.get('type'), 'name': m.get('name')}
                if m.get('is_bitfield'):
                    member['is_bitfield'] = m.get('is_bitfield') == 'true'
                if m.get('bit_size'):
                    member['bit_size'] = int(m.get('bit_size'))
                expected_members.append(member)
            extra['expected_members'] = expected_members
        layout_members_elem = case.find('members')
        if layout_members_elem is not None:
            layout_members = []
            for m in layout_members_elem.findall('member'):
                member = {'type': m.get('type'), 'name': m.get('name')}
                if m.get('is_bitfield'):
                    member['is_bitfield'] = m.get('is_bitfield') == 'true'
                if m.get('bit_size'):
                    member['bit_size'] = int(m.get('bit_size'))
                if m.get('array_dims'):
                    dims = [int(x) for x in m.get('array_dims').split(',') if x]
                    member['array_dims'] = dims
                layout_members.append(member)
            extra['members'] = layout_members
        layout_elem = case.find('expected_layout')
        if layout_elem is not None:
            layout_expect = []
            for item in layout_elem.findall('member'):
                entry = {'name': item.get('name')}
                if item.get('type'):
                    entry['type'] = item.get('type')
                if item.get('offset'):
                    entry['offset'] = int(item.get('offset'))
                if item.get('size'):
                    entry['size'] = int(item.get('size'))
                if item.get('bit_offset'):
                    entry['bit_offset'] = int(item.get('bit_offset'))
                if item.get('bit_size'):
                    entry['bit_size'] = int(item.get('bit_size'))
                layout_expect.append(entry)
            extra['expected_layout'] = layout_expect
        ets = case.find('expected_total_size')
        if ets is not None and ets.text:
            extra['expected_total_size'] = int(ets.text.strip())
        ea = case.find('expected_alignment')
        if ea is not None and ea.text:
            extra['expected_alignment'] = int(ea.text.strip())
        ell = case.find('expected_layout_len')
        if ell is not None and ell.text:
            extra['expected_layout_len'] = int(ell.text.strip())
        if case.find('expect_none') is not None:
            extra['expect_none'] = True
        if case.find('check_dataclass') is not None:
            extra['check_dataclass'] = True
        return extra

def load_struct_parsing_tests(xml_path):
    return StructParsingXMLTestLoader(xml_path).cases
