import os
import pytest

tkinter = None
try:
    import tkinter as tk
    from src.view.struct_view import StructView
    tkinter = tk
except Exception:
    tkinter = None


skip_if_no_display = pytest.mark.skipif(
    not os.environ.get('DISPLAY') or not tkinter, reason="No display/tkinter; skipping GUI tests"
)


def _make_view():
    view = StructView(presenter=None)
    view.enable_unified_layout_values = True
    return view


@skip_if_no_display
def test_unified_layout_adds_value_columns_after_load():
    view = _make_view()
    layout = [
        {"name": "a", "type": "int", "offset": 0, "size": 4, "bit_offset": None, "bit_size": None, "is_bitfield": False},
    ]
    view.show_struct_layout("S", layout, total_size=4, struct_align=4)
    items = view.layout_tree.get_children("")
    assert items, "layout tree should have at least one row"
    vals = view.layout_tree.item(items[0], "values")
    # Expect 10 columns with last 3 empty strings
    assert len(vals) == 10
    assert vals[7] == "" and vals[8] == "" and vals[9] == ""


@skip_if_no_display
def test_unified_layout_fills_values_after_parse():
    view = _make_view()
    layout = [
        {"name": "a", "type": "int", "offset": 0, "size": 4, "bit_offset": None, "bit_size": None, "is_bitfield": False},
    ]
    parsed = [
        {"name": "a", "value": str(int("01020304", 16)), "hex_raw": "01020304"},
    ]
    view.show_struct_layout("S", layout, total_size=4, struct_align=4)
    view.show_parsed_values(parsed)
    items = view.layout_tree.get_children("")
    vals = view.layout_tree.item(items[0], "values")
    assert vals[7] == str(int("01020304", 16))
    assert vals[8] == hex(int(vals[7]))
    assert vals[9] == "01｜02｜03｜04"


@skip_if_no_display
def test_unified_layout_padding_value_dash():
    view = _make_view()
    layout = [
        {"name": "(padding)", "type": "padding", "offset": 0, "size": 2, "bit_offset": None, "bit_size": None, "is_bitfield": False},
    ]
    parsed = [
        {"name": "(padding)", "value": "-", "hex_raw": "0000"},
    ]
    view.show_struct_layout("S", layout, total_size=2, struct_align=1)
    view.show_parsed_values(parsed)
    items = view.layout_tree.get_children("")
    vals = view.layout_tree.item(items[0], "values")
    assert vals[7] == "-"
    assert vals[9] == "00｜00"


@skip_if_no_display
def test_unified_layout_bitfield_and_arrays_values():
    view = _make_view()
    layout = [
        {"name": "f", "type": "unsigned int", "offset": 0, "size": 4, "bit_offset": 0, "bit_size": 3, "is_bitfield": True},
        {"name": "arr[0]", "type": "char", "offset": 4, "size": 1, "bit_offset": None, "bit_size": None, "is_bitfield": False},
        {"name": "arr[1]", "type": "char", "offset": 5, "size": 1, "bit_offset": None, "bit_size": None, "is_bitfield": False},
    ]
    parsed = [
        {"name": "f", "value": "5", "hex_raw": "05000000"},
        {"name": "arr[0]", "value": str(int("41", 16)), "hex_raw": "41"},
        {"name": "arr[1]", "value": str(int("42", 16)), "hex_raw": "42"},
    ]
    view.show_struct_layout("S", layout, total_size=6, struct_align=4)
    view.show_parsed_values(parsed)
    items = view.layout_tree.get_children("")
    assert len(items) == 3
    vals0 = view.layout_tree.item(items[0], "values")
    vals1 = view.layout_tree.item(items[1], "values")
    vals2 = view.layout_tree.item(items[2], "values")
    assert vals0[7] == "5" and vals0[9] == "05｜00｜00｜00"
    assert vals1[7] == str(int("41", 16)) and vals1[9] == "41"
    assert vals2[7] == str(int("42", 16)) and vals2[9] == "42"


@skip_if_no_display
def test_unified_layout_nested_struct_values():
    view = _make_view()
    # Simulate flattened nested names as produced by layout calculator (e.g., s.a, s.b)
    layout = [
        {"name": "s.a", "type": "int", "offset": 0, "size": 4, "bit_offset": None, "bit_size": None, "is_bitfield": False},
        {"name": "s.b", "type": "short", "offset": 4, "size": 2, "bit_offset": None, "bit_size": None, "is_bitfield": False},
    ]
    parsed = [
        {"name": "s.a", "value": "123", "hex_raw": "7b000000"},
        {"name": "s.b", "value": "258", "hex_raw": "0201"},
    ]
    view.show_struct_layout("S", layout, total_size=6, struct_align=4)
    view.show_parsed_values(parsed)
    items = view.layout_tree.get_children("")
    assert len(items) == 2
    vals0 = view.layout_tree.item(items[0], "values")
    vals1 = view.layout_tree.item(items[1], "values")
    assert vals0[0] == "s.a" and vals0[7] == "123" and vals0[9] == "7b｜00｜00｜00"
    assert vals1[0] == "s.b" and vals1[7] == "258" and vals1[9] == "02｜01"

