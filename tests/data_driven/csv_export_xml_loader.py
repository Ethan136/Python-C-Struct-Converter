import os
import xml.etree.ElementTree as ET


class CSVExportXMLCase:
    def __init__(self, case_elem, base_dir):
        self.id = case_elem.get('id') or ''
        self.name = case_elem.get('name') or ''
        self.input_file = os.path.join(base_dir, case_elem.find('Input').get('file'))
        self.output_file = os.path.join(base_dir, case_elem.find('Output').get('file'))
        self.hex_value = None
        self.endianness = 'little'
        hex_elem = case_elem.find('HexInput')
        if hex_elem is not None:
            self.hex_value = (hex_elem.get('value') or '').strip().replace(' ', '')
            self.endianness = (hex_elem.get('endianness') or 'little').lower()
        opt = case_elem.find('Options')
        self.options = {
            'delimiter': opt.get('delimiter', ','),
            'includeHeader': opt.get('includeHeader', 'true').lower() == 'true',
            'encoding': opt.get('encoding', 'UTF-8'),
            'includeBom': opt.get('includeBom', 'false').lower() == 'false' and False or True,
            'lineEnding': opt.get('lineEnding', 'LF'),
            'nullStrategy': opt.get('nullStrategy', 'empty'),
            'columns': opt.get('columns', None),
            'sortBy': opt.get('sortBy', None),
            'safeCast': opt.get('safeCast', 'true').lower() == 'true',
            'includeLayout': opt.get('includeLayout', 'true').lower() == 'true',
            'includeValues': opt.get('includeValues', 'true').lower() == 'true',
            'endianness': opt.get('endianness', 'little').lower(),
            # v24 additions (optional)
            'columnsSource': opt.get('columnsSource', None),
            'includeMetadata': opt.get('includeMetadata', 'false').lower() == 'true',
        }


def load_csv_export_cases(xml_path):
    base_dir = os.path.dirname(xml_path)
    tree = ET.parse(xml_path)
    root = tree.getroot()
    cases = []
    for case in root.findall('Case'):
        cases.append(CSVExportXMLCase(case, base_dir))
    return cases

