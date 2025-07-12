import unittest
import tempfile
import os
from src.config import ui_strings

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

if __name__ == '__main__':
    unittest.main()
