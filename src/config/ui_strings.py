import xml.etree.ElementTree as ET
from pathlib import Path

_strings = {}


def load_ui_strings(path: str) -> dict:
    """Load UI strings from an XML file."""
    global _strings
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"UI string file not found: {path}")
    tree = ET.parse(file_path)
    root = tree.getroot()
    loaded = {}
    for elem in root.findall("string"):
        name = elem.attrib.get("name")
        if name:
            loaded[name] = elem.text or ""
    _strings = loaded
    return loaded


def get_string(key: str) -> str:
    """Retrieve a UI string by key."""
    return _strings.get(key, f"{key}")
