import xml.etree.ElementTree as ET
from collections import defaultdict
from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

class InputFieldProcessorXMLTestLoader(BaseXMLTestLoader):
    def parse_extra(self, case):
        tests = defaultdict(list)
        # 支援多種測試類型
        for pad in case.findall('pad_hex_input'):
            byte_size = int(pad.attrib['byte_size'])
            for c in pad.findall('case'):
                tests['pad_hex_input'].append({
                    'byte_size': byte_size,
                    'input': c.attrib['input'],
                    'expected': c.attrib['expected'],
                })
        for pad in case.findall('pad_hex_input_case_insensitive'):
            byte_size = int(pad.attrib['byte_size'])
            for c in pad.findall('case'):
                tests['pad_hex_input_case_insensitive'].append({
                    'byte_size': byte_size,
                    'input': c.attrib['input'],
                    'expected': c.attrib['expected'],
                })
        for conv in case.findall('convert_to_raw_bytes'):
            endianness = conv.attrib['endianness']
            for c in conv.findall('case'):
                tests['convert_to_raw_bytes'].append({
                    'endianness': endianness,
                    'padded_hex': c.attrib['padded_hex'],
                    'byte_size': int(c.attrib['byte_size']),
                    'expected': c.attrib['expected'],
                })
        for proc in case.findall('process_input_field'):
            for c in proc.findall('case'):
                tests['process_input_field'].append({
                    'input': c.attrib['input'],
                    'byte_size': int(c.attrib['byte_size']),
                    'endianness': c.attrib['endianness'],
                    'expected': c.attrib['expected'],
                })
        for proc in case.findall('process_input_field_edge_cases'):
            for c in proc.findall('case'):
                tests['process_input_field_edge_cases'].append({
                    'input': c.attrib['input'],
                    'byte_size': int(c.attrib['byte_size']),
                    'endianness': c.attrib['endianness'],
                    'expected': c.attrib['expected'],
                })
        for iss in case.findall('is_supported_field_size'):
            for c in iss.findall('case'):
                tests['is_supported_field_size'].append({
                    'size': int(c.attrib['size']),
                    'expected': c.attrib['expected'] == 'true',
                })
        return {'extra_tests': dict(tests)}

    def parse_error_cases(self, xml_path):
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        error_cases = []
        for err in root.findall('error_case'):
            error_cases.append({
                'name': err.get('name', ''),
                'input': err.get('input', ''),
                'byte_size': int(err.get('byte_size', 1)),
                'endianness': err.get('endianness', 'big'),
                'error_type': err.get('error_type', '')
            })
        return error_cases

def load_input_field_processor_tests(xml_path):
    return InputFieldProcessorXMLTestLoader(xml_path).cases 

def load_input_field_processor_error_tests(xml_path):
    loader = InputFieldProcessorXMLTestLoader(xml_path)
    return loader.parse_error_cases(xml_path) 