import xml.etree.ElementTree as ET
from tests.base_xml_test_loader import BaseXMLTestLoader

class StructModelXMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        data = super().parse_common_fields(case)
        # 解析 <input_data><hex> 作為 input_hex
        input_data_elem = case.find('input_data')
        input_hex = None
        if input_data_elem is not None:
            hex_elem = input_data_elem.find('hex')
            if hex_elem is not None and hex_elem.text:
                input_hex = hex_elem.text.strip()
        data['input_hex'] = input_hex
        return data

    def parse_extra(self, case):
        extra = {}
        # optional numeric expectations
        ets = case.find('expected_total_size')
        if ets is not None and ets.text:
            extra['expected_total_size'] = int(ets.text.strip())
        esa = case.find('expected_struct_align')
        if esa is not None and esa.text:
            extra['expected_struct_align'] = int(esa.text.strip())
        ell = case.find('expected_layout_len')
        if ell is not None and ell.text:
            extra['expected_layout_len'] = int(ell.text.strip())
        exc = case.find('expected_exception')
        if exc is not None and exc.text:
            extra['expected_exception'] = exc.text.strip()
        return extra

def load_struct_model_tests(xml_path):
    return StructModelXMLTestLoader(xml_path).cases 