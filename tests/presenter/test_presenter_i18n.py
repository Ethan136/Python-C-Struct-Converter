import types

import pytest


def make_presenter_with_stubs(monkeypatch, *, layout_present=True):
    from src.presenter.struct_presenter import StructPresenter

    class DummyModel:
        def __init__(self):
            self.layout = [{}] if layout_present else None
            self.total_size = 8

        def parse_hex_data(self, hex_data, byte_order, layout=None, total_size=None):
            return []

    class DummyView:
        def get_hex_input_parts(self):
            # Include invalid hex to trigger invalid_input error
            return [("GG", 2)]

        def get_selected_endianness(self):
            return "Little Endian"

    model = DummyModel()
    presenter = StructPresenter(model, view=DummyView())
    return presenter


def test_browse_file_dialog_title_uses_xml_key(monkeypatch):
    # Arrange: monkeypatch get_string to return sentinel, and filedialog to capture title
    sentinel = "SENTINEL_TITLE"
    import src.presenter.struct_presenter as sp

    # Patch the symbol used inside struct_presenter
    monkeypatch.setattr("src.presenter.struct_presenter.get_string", lambda key: sentinel)

    captured = {}

    def fake_askopenfilename(*args, **kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(sp, "filedialog", types.SimpleNamespace(askopenfilename=fake_askopenfilename))

    # Act
    presenter = make_presenter_with_stubs(monkeypatch)
    presenter.browse_file()

    # Assert
    assert captured.get("title") == sentinel


def test_parse_hex_error_title_uses_xml_key_prefix(monkeypatch):
    # Arrange: return a recognizable value for dialog_invalid_input
    def fake_get_string(key: str):
        return f"i18n:{key}"

    # Patch the symbol used inside struct_presenter
    monkeypatch.setattr("src.presenter.struct_presenter.get_string", fake_get_string)

    presenter = make_presenter_with_stubs(monkeypatch, layout_present=True)

    # Act: Trigger invalid_input by providing non-hex characters via DummyView
    result = presenter.parse_hex_data()

    # Assert: Expect error message to begin with the i18n title
    assert result["type"] == "error"
    assert result["message"].startswith("i18n:dialog_invalid_input")

