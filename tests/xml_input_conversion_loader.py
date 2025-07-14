import xml.etree.ElementTree as ET
from tests.base_xml_test_loader import BaseXMLTestLoader

class InputConversionXMLTestLoader(BaseXMLTestLoader):
    def parse_cases(self):
        cases = []
        for case in self.root.findall('test_config'):
            data = self.parse_common_fields(case)
            extra = self.parse_extra(case)
            if extra:
                data.update(extra)
            cases.append(data)
        return cases

    def parse_common_fields(self, case):
        # 基本欄位
        name = case.attrib.get('name', '')
        unit_size = int(case.attrib.get('unit_size', 1))
        description = case.attrib.get('description', '')
        # input_values: list
        input_values = []
        input_values_elem = case.find('input_values')
        if input_values_elem is not None:
            array_elem = input_values_elem.find('array')
            if array_elem is not None and array_elem.text:
                import re
                values = [v.strip() for v in re.split(r'[\s,]+', array_elem.text.strip()) if v.strip()]
                input_values.extend(values)
            for value_elem in input_values_elem.findall('value'):
                input_values.append(value_elem.text or "")
        # expected_results: list of dicts
        expected_results = []
        expected_elem = case.find('expected_results')
        if expected_elem is not None:
            for result_elem in expected_elem.findall('result'):
                entry = {
                    'index': int(result_elem.get('index', 0)),
                    'big_endian': result_elem.get('big_endian', ''),
                    'little_endian': result_elem.get('little_endian', ''),
                    'original_value': result_elem.text or ''
                }
                expected_results.append(entry)
        return {
            'name': name,
            'unit_size': unit_size,
            'description': description,
            'input_values': input_values,
            'expected_results': expected_results,
        }

    def parse_extra(self, case):
        # 保持原有功能
        return {}

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
                'error_type': err.get('error_type', '')
            })
        return error_cases

def load_input_conversion_tests(xml_path):
    return InputConversionXMLTestLoader(xml_path).cases 

def load_input_conversion_error_tests(xml_path):
    loader = InputConversionXMLTestLoader(xml_path)
    return loader.parse_error_cases(xml_path) 