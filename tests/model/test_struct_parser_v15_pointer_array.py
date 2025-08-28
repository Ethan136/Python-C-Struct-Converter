import pytest

from src.model.struct_parser import parse_struct_definition_ast
from src.model.struct_model import calculate_layout


def _flatten_layout_names(layout):
    return [item.get("name") if isinstance(item, dict) else getattr(item, "name", None) for item in layout if (isinstance(item, dict) and item.get("type") != "padding") or (hasattr(item, "type") and getattr(item, "type") != "padding")]


def test_pointer_2d_array_dims_preserved_and_layout_expands():
    src = """
    struct S {
        U8* arr2d[2][3];
    };
    """
    sdef = parse_struct_definition_ast(src)
    # 找到 arr2d 成員
    m = next(mm for mm in sdef.members if mm.name == "arr2d")
    assert m.type == "pointer"
    assert m.array_dims == [2, 3]

    layout, total, align = calculate_layout(sdef.members)
    names = [x.name if hasattr(x, "name") else x.get("name") for x in layout if (hasattr(x, "type") and x.type != "padding") or (isinstance(x, dict) and x.get("type") != "padding")]
    # 6 個元素應展開
    for i in range(2):
        for j in range(3):
            assert f"arr2d[{i}][{j}]" in names


def test_pointer_1d_array_dims_preserved():
    src = """
    struct S {
        int* a[4];
    };
    """
    sdef = parse_struct_definition_ast(src)
    m = next(mm for mm in sdef.members if mm.name == "a")
    assert m.type == "pointer"
    assert m.array_dims == [4]


def test_scalar_pointer_unchanged():
    src = """
    struct S {
        int* p;
    };
    """
    sdef = parse_struct_definition_ast(src)
    m = next(mm for mm in sdef.members if mm.name == "p")
    assert m.type == "pointer"
    assert m.array_dims == []


