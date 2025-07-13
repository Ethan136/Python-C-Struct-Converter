import xml.etree.ElementTree as ET
from collections import defaultdict


def load_input_field_processor_tests(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    tests = defaultdict(list)

    for pad in root.findall('pad_hex_input'):
        byte_size = int(pad.attrib['byte_size'])
        for case in pad.findall('case'):
            tests['pad_hex_input'].append({
                'byte_size': byte_size,
                'input': case.attrib['input'],
                'expected': case.attrib['expected'],
            })

    for pad in root.findall('pad_hex_input_case_insensitive'):
        byte_size = int(pad.attrib['byte_size'])
        for case in pad.findall('case'):
            tests['pad_hex_input_case_insensitive'].append({
                'byte_size': byte_size,
                'input': case.attrib['input'],
                'expected': case.attrib['expected'],
            })

    for conv in root.findall('convert_to_raw_bytes'):
        endianness = conv.attrib['endianness']
        for case in conv.findall('case'):
            tests['convert_to_raw_bytes'].append({
                'endianness': endianness,
                'padded_hex': case.attrib['padded_hex'],
                'byte_size': int(case.attrib['byte_size']),
                'expected': case.attrib['expected'],
            })

    # 新增 process_input_field
    for proc in root.findall('process_input_field'):
        for case in proc.findall('case'):
            tests['process_input_field'].append({
                'input': case.attrib['input'],
                'byte_size': int(case.attrib['byte_size']),
                'endianness': case.attrib['endianness'],
                'expected': case.attrib['expected'],
            })
    # 新增 process_input_field_edge_cases
    for proc in root.findall('process_input_field_edge_cases'):
        for case in proc.findall('case'):
            tests['process_input_field_edge_cases'].append({
                'input': case.attrib['input'],
                'byte_size': int(case.attrib['byte_size']),
                'endianness': case.attrib['endianness'],
                'expected': case.attrib['expected'],
            })

    return tests 