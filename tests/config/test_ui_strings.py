import os
from pathlib import Path

import pytest

from src.config import load_ui_strings, get_string


def test_load_ui_strings_success():
    xml_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'config', 'ui_strings.xml')
    xml_path = os.path.abspath(xml_path)
    loaded = load_ui_strings(xml_path)
    # 基本鍵應存在（依現有 XML）
    assert 'app_title' in loaded
    assert 'dialog_select_file' in loaded


def test_get_string_fallback_to_key(tmp_path):
    # 先載入一份最小 XML
    xml_content = """
<strings>
    <string name="only_key">value</string>
</strings>
""".strip()
    xml_file = tmp_path / 'ui_strings.xml'
    xml_file.write_text(xml_content, encoding='utf-8')
    load_ui_strings(str(xml_file))
    # 存在鍵
    assert get_string('only_key') == 'value'
    # 不存在鍵時回傳鍵名本身
    assert get_string('not_exist_key') == 'not_exist_key'


def test_load_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        load_ui_strings(str(Path('/nonexistent/path/ui_strings.xml')))

