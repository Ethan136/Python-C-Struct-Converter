from tests.data_driven.base_xml_test_loader import BaseXMLTestLoader

class UnionPreparationXMLTestLoader(BaseXMLTestLoader):
    def parse_common_fields(self, case):
        data = super().parse_common_fields(case)
        data['type'] = case.get('type')
        if case.get('expected_total'):
            data['expected_total'] = int(case.get('expected_total'))
        if case.get('expected_align'):
            data['expected_align'] = int(case.get('expected_align'))
        if case.get('expected_name'):
            data['expected_name'] = case.get('expected_name')
        return data

    def parse_extra(self, case):
        struct_def = self._get_text_or_none(case.find('struct_definition'))
        return {'struct_definition': struct_def}

def load_union_preparation_tests(xml_path):
    return UnionPreparationXMLTestLoader(xml_path).cases
