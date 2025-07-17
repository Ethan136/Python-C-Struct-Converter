import os
import xml.etree.ElementTree as ET

def fix_nested_members(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    changed = False
    for member in root.findall('.//member'):
        t = member.get('type')
        if t in ('struct', 'union'):
            if member.find('nested_members') is None:
                ET.SubElement(member, 'nested_members')
                changed = True
    if changed:
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
        print(f"Fixed: {xml_path}")

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'tests', 'data')
    for fname in os.listdir(data_dir):
        if fname.endswith('.xml'):
            fix_nested_members(os.path.join(data_dir, fname)) 