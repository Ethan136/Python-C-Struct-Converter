import unittest
import tempfile
import os
from config import ui_strings
import pytest
from config.ui_strings import get_string, load_ui_strings

SAMPLE_XML = """<strings>
    <string name='greet'>Hello</string>
    <string name='farewell'>Goodbye</string>
</strings>"""

class TestStringParser(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.xml')
        self.tmp.write(SAMPLE_XML)
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_load_ui_strings(self):
        data = ui_strings.load_ui_strings(self.tmp.name)
        self.assertEqual(data['greet'], 'Hello')
        self.assertEqual(data['farewell'], 'Goodbye')

    def test_get_string(self):
        ui_strings.load_ui_strings(self.tmp.name)
        self.assertEqual(ui_strings.get_string('greet'), 'Hello')
        self.assertEqual(ui_strings.get_string('missing'), 'missing')

def test_get_string_existing(tmp_path):
    # 建立臨時 xml 字串檔
    xml = '<resources><string name="hello">Hello</string></resources>'
    xml_path = tmp_path / "ui_strings.xml"
    xml_path.write_text(xml)
    load_ui_strings(str(xml_path))
    assert get_string("hello") == "Hello"

def test_get_string_missing(tmp_path):
    xml = '<resources><string name="foo">bar</string></resources>'
    xml_path = tmp_path / "ui_strings.xml"
    xml_path.write_text(xml)
    load_ui_strings(str(xml_path))
    assert get_string("not_exist") == "not_exist"

if __name__ == '__main__':
    unittest.main()
