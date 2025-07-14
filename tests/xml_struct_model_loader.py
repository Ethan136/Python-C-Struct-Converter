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
        # 若未來有特殊欄位可在此擴充，目前無特殊欄位
        return {}

def load_struct_model_tests(xml_path):
    return StructModelXMLTestLoader(xml_path).cases 