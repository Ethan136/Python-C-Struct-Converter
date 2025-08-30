import os
import pytest


pytestmark = pytest.mark.skipif(os.environ.get("DISPLAY") is None, reason="GUI tests require DISPLAY")


def test_window_title_and_tabs_use_xml(monkeypatch):
    from src.view.struct_view import StructView

    # Patch get_string
    def fake_get_string(key: str):
        mapping = {
            "window_title": "WT",
            "tab_load_h": "TAB1",
            "tab_manual_struct": "TAB2",
        }
        return mapping.get(key, key)

    monkeypatch.setattr("src.view.struct_view.get_string", fake_get_string)

    class DummyPresenter:
        pass

    view = StructView(presenter=DummyPresenter())
    try:
        assert view.title() == "WT"
        texts = [view.tab_control.tab(t, "text") for t in view.tab_control.tabs()]
        assert "TAB1" in texts
        assert "TAB2" in texts
    finally:
        view.destroy()

