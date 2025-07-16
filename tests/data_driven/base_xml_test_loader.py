import xml.etree.ElementTree as ET

class BaseXMLTestLoader:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.cases = self.parse_cases()

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
        struct_def = self._get_text_or_none(case.find('struct_definition'))
        struct_file = case.attrib.get('struct_file') or (case.find('struct_file').text.strip() if case.find('struct_file') is not None else None)
        # input_data: list of dicts
        input_data = []
        input_data_elem = case.find('input_data')
        if input_data_elem is not None:
            for input_elem in input_data_elem.findall('input'):
                input_data.append({
                    'index': int(input_elem.get('index', 0)),
                    'value': input_elem.get('value', ''),
                    'unit_size': int(input_elem.get('unit_size', 1)),
                    'description': input_elem.get('description', '')
                })
        # expected_results: dict by endianness
        expected_results = {}
        expected_elem = case.find('expected_results')
        if expected_elem is not None:
            for endianness in expected_elem.findall('endianness'):
                endian_name = endianness.get('name', 'little')
                expected_results[endian_name] = {}
                for member in endianness.findall('member'):
                    member_name = member.get('name')
                    expected_results[endian_name][member_name] = {
                        'expected_value': member.get('expected_value'),
                        'expected_hex': member.get('expected_hex'),
                        'description': member.get('description', '')
                    }
        expected = []
        for member in case.find('expected_results').findall('member') if case.find('expected_results') is not None else []:
            entry = {'name': member.attrib['name']}
            for k in member.attrib:
                if k != 'name':
                    entry[k] = member.attrib[k]
            expected.append(entry)
        return {
            'name': case.attrib.get('name', ''),
            'description': case.attrib.get('description', ''),
            'struct_definition': struct_def,
            'struct_file': struct_file,
            'input_data': input_data,
            'expected_results': expected_results,
            'expected': expected,
            'endianness': case.attrib.get('endianness', 'little'),
        }

    def parse_extra(self, case):
        """子類可 override，parse 自訂欄位"""
        return {}

    def _get_text_or_none(self, elem):
        if elem is not None and elem.text:
            return elem.text.strip()
        return None 