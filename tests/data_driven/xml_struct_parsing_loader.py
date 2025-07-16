from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

class StructParsingXMLTestLoader(BaseXMLTestLoader):
    """Load struct parsing and layout test cases from XML."""

    def parse_cases(self):
        cases = []
        for case in self.root.findall('test_case'):
            data = {
                'name': case.get('name', ''),
                'type': case.get('type', 'parse'),
                'struct_definition': self._get_text_or_none(case.find('struct_definition')),
                'expect_none': case.find('expect_none') is not None,
                'expected_struct_name': self._get_text_or_none(case.find('expected_struct_name')),
            }
            # expected members for parsing
            members = []
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
                    if m.get('array_dims'):
                        member['array_dims'] = [int(x) for x in m.get('array_dims').split(',') if x.strip()]
                    members.append(member)
            data['expected_members'] = members

            # layout expectations
            ets = case.find('expected_total_size')
            if ets is not None and ets.text:
                data['expected_total_size'] = int(ets.text.strip())
            ea = case.find('expected_alignment')
            if ea is not None and ea.text:
                data['expected_alignment'] = int(ea.text.strip())
            layout_elem = case.find('expected_layout')
            layout = []
            if layout_elem is not None:
                for e in layout_elem.findall('entry'):
                    entry = {
                        'name': e.get('name'),
                        'type': e.get('type'),
                        'offset': int(e.get('offset', 0)),
                        'size': int(e.get('size', 0)),
                    }
                    if e.get('bit_offset'):
                        entry['bit_offset'] = int(e.get('bit_offset'))
                    if e.get('bit_size'):
                        entry['bit_size'] = int(e.get('bit_size'))
                    layout.append(entry)
            data['expected_layout'] = layout

            cases.append(data)
        return cases

def load_struct_parsing_tests(xml_path):
    return StructParsingXMLTestLoader(xml_path).cases
