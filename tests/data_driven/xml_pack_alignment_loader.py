from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

def parse_member(elem):
    member = {'type': elem.get('type'), 'name': elem.get('name')}
    if elem.get('is_bitfield'):
        member['is_bitfield'] = elem.get('is_bitfield') == 'true'
    if elem.get('bit_size'):
        member['bit_size'] = int(elem.get('bit_size'))
    if elem.get('array_dims'):
        member['array_dims'] = [int(x) for x in elem.get('array_dims').split(',')]
    nested = elem.find('nested_members')
    if nested is not None:
        member['nested'] = {'members': [parse_member(c) for c in nested.findall('member')]}
    return member

class PackAlignmentXMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        data = super().parse_common_fields(case)
        if case.get('pack'):
            data['pack'] = int(case.get('pack'))
        data['type'] = case.get('type')
        return data

    def parse_extra(self, case):
        members = []
        members_elem = case.find('members')
        if members_elem is not None:
            for m in members_elem.findall('member'):
                members.append(parse_member(m))
        offsets = {}
        off_elem = case.find('expected_offsets')
        if off_elem is not None:
            for e in off_elem.findall('entry'):
                offsets[e.get('name')] = int(e.get('offset'))
        ets = case.find('expected_total_size')
        total = int(ets.text.strip()) if ets is not None and ets.text else None
        return {'members': members, 'expected_offsets': offsets, 'expected_total_size': total}

def load_pack_alignment_tests(xml_path):
    return PackAlignmentXMLTestLoader(xml_path).cases
