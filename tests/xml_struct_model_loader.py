import xml.etree.ElementTree as ET

def load_struct_model_tests(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    tests = []
    for case in root.findall('test_case'):
        struct_def = case.find('struct_definition').text.strip()
        input_hex = case.find('input_data/hex').text.strip()
        expected = []
        for member in case.find('expected_results').findall('member'):
            # 支援 value_little/value_big/hex_raw 屬性
            entry = {'name': member.attrib['name']}
            if 'value' in member.attrib:
                entry['value'] = member.attrib['value']
            if 'value_little' in member.attrib:
                entry['value_little'] = member.attrib['value_little']
            if 'value_big' in member.attrib:
                entry['value_big'] = member.attrib['value_big']
            if 'hex_raw' in member.attrib:
                entry['hex_raw'] = member.attrib['hex_raw']
            expected.append(entry)
        tests.append({
            'name': case.attrib['name'],
            'description': case.attrib.get('description', ''),
            'struct_definition': struct_def,
            'input_hex': input_hex,
            'expected': expected,
            'endianness': case.attrib.get('endianness', 'little'),
        })
    return tests 