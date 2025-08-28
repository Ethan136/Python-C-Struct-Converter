import pytest
from src.model.struct_parser import parse_struct_definition_ast, StructDef
from src.model.struct_model import calculate_layout


def _names(layout):
    return [x.name if hasattr(x, "name") else x.get("name") for x in layout if (hasattr(x, "type") and x.type != "padding") or (isinstance(x, dict) and x.get("type") != "padding")]


def test_referenced_struct_single_member():
    src = """
    struct Inner { int x; char y; };
    struct Outer { struct Inner a; };
    """
    sdef = parse_struct_definition_ast(src)
    assert isinstance(sdef, StructDef)
    layout, total, align = calculate_layout(sdef.members)
    names = _names(layout)
    # a 應展開其成員
    assert any(n.startswith("a.") for n in names)


def test_referenced_struct_array_1d():
    src = """
    struct Inner { int x; };
    struct Outer { struct Inner arr[2]; };
    """
    sdef = parse_struct_definition_ast(src)
    layout, total, align = calculate_layout(sdef.members)
    names = _names(layout)
    assert "arr[0].x" in names
    assert "arr[1].x" in names


def test_referenced_struct_array_2d():
    src = """
    struct Inner { int x; };
    struct Outer { struct Inner nd[2][2]; };
    """
    sdef = parse_struct_definition_ast(src)
    layout, total, align = calculate_layout(sdef.members)
    names = _names(layout)
    assert "nd[0][0].x" in names
    assert "nd[1][1].x" in names


def test_referenced_union_array():
    src = """
    union U { int a; char b; };
    struct S { union U u_arr[2]; };
    """
    sdef = parse_struct_definition_ast(src)
    layout, total, align = calculate_layout(sdef.members)
    names = _names(layout)
    # union layout 目前會列出各欄位於 offset=0，此處僅驗證展開節點存在
    assert any(n.startswith("u_arr[0].") for n in names)
    assert any(n.startswith("u_arr[1].") for n in names)


def test_forward_reference():
    src = """
    struct Outer { struct Inner a; };
    struct Inner { int x; };
    """
    sdef = parse_struct_definition_ast(src, target_name="Outer")
    layout, total, align = calculate_layout(sdef.members)
    names = _names(layout)
    assert "a.x" in names


def test_self_reference_pointer_only():
    src = """
    struct Node { struct Node *next; };
    """
    sdef = parse_struct_definition_ast(src)
    layout, total, align = calculate_layout(sdef.members)
    names = _names(layout)
    # 僅應有 next（pointer），不展開 Node 成員
    assert "next" in names
