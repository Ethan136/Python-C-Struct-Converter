import os
import xml.etree.ElementTree as ET

def find_struct_with_empty_nested(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for member in root.findall('.//member'):
        t = member.get('type')
        if t in ('struct', 'union'):
            nested = member.find('nested_members')
            if nested is not None and len(list(nested.findall('member'))) == 0:
                print(f"[EMPTY] {xml_path} <member type='{t}' name='{member.get('name')}' />")

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'tests', 'data')
    for fname in os.listdir(data_dir):
        if fname.endswith('.xml'):
            find_struct_with_empty_nested(os.path.join(data_dir, fname)) 