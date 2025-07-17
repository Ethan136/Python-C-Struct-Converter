import pytest
from src.model.struct_parser import parse_struct_definition_ast, MemberDef, StructDef, UnionDef

# 1. 巢狀 struct/union/array
@pytest.mark.parametrize("src, expect", [
    ("""
    struct Outer {
        struct Inner {
            int x;
            char y;
        } a;
        int b;
    };
    """, [
        ("a", StructDef, [
            ("x", "int"),
            ("y", "char")
        ]),
        ("b", "int")
    ]),
    # TODO(v5_union): 待 union AST/解析支援後恢復
    pytest.param(
        """
        struct S {
            union U {
                int a;
                char b;
            } u;
        };
        """,
        [
            ("u", UnionDef, [
                ("a", "int"),
                ("b", "char")
            ])
        ],
        # marks=pytest.mark.skip(reason="union not supported in MVP")  # 解除 skip
    ),
])
def test_nested_struct_union_array(src, expect):
    sdef = parse_struct_definition_ast(src)
    assert isinstance(sdef, StructDef)
    for idx, exp in enumerate(expect):
        m = sdef.members[idx]
        if isinstance(exp[1], type) and issubclass(exp[1], (StructDef, UnionDef)):
            assert isinstance(m.nested, exp[1])
            for j, (ename, etype) in enumerate(exp[2]):
                nm = m.nested.members[j]
                assert nm.name == ename
                assert nm.type == etype
        else:
            assert m.name == exp[0]
            assert m.type == exp[1]

# 2. 匿名 struct/union
# TODO(v5_anonymous): 待匿名 struct/union AST/展平支援後恢復
@pytest.mark.skip(reason="anonymous struct/union not supported in MVP")
@pytest.mark.parametrize("src, expect_names", [
    ("""
    struct S {
        struct { int x; char y; };
        int b;
    };
    """, ["x", "y", "b"]),
    ("""
    struct S {
        union { int a; char b; };
        int c;
    };
    """, ["a", "b", "c"]),
])
def test_anonymous_struct_union_flatten(src, expect_names):
    sdef = parse_struct_definition_ast(src)
    names = [m.name for m in sdef.members]
    for n in expect_names:
        assert n in names

# 3. struct/union array, N-D array
# TODO(v5_nd_array): 待 array/N-D array AST/展平支援後恢復
@pytest.mark.skip(reason="array/N-D array not supported in MVP")
@pytest.mark.parametrize("src, expect", [
    ("""
    struct S {
        struct Inner { int x; } arr[2];
    };
    """, ["arr[0].x", "arr[1].x"]),
    ("""
    struct S {
        int matrix[2][3];
    };
    """, ["matrix[0][0]", "matrix[1][2]"]),
])
def test_struct_union_nd_array_flatten(src, expect):
    sdef = parse_struct_definition_ast(src)
    flat_names = _flatten_member_names(sdef)
    for n in expect:
        assert n in flat_names

def _flatten_member_names(sdef):
    # Helper: 遞迴展平所有成員名稱（含 array 展開）
    result = []
    def walk(m, prefix=""):
        if m.array_dims:
            from itertools import product
            dims = [range(d) for d in m.array_dims]
            for idxs in product(*dims):
                idx_str = ''.join(f"[{i}]" for i in idxs)
                if m.nested:
                    for nm in m.nested.members:
                        walk(nm, prefix + m.name + idx_str + ".")
                else:
                    result.append(prefix + m.name + idx_str)
        elif m.nested:
            for nm in m.nested.members:
                walk(nm, prefix + (m.name + "." if m.name else ""))
        else:
            result.append(prefix + m.name)
    for m in sdef.members:
        walk(m)
    return result

# 4. 匿名 bitfield
# TODO(v5_anonymous_bitfield): 待匿名 bitfield AST/解析支援後恢復
@pytest.mark.skip(reason="anonymous bitfield not supported in MVP")
@pytest.mark.parametrize("src, expect", [
    ("""
    struct S {
        int a : 3;
        int : 2;
        int b : 5;
    };
    """, ["a", None, "b"]),
])
def test_anonymous_bitfield(src, expect):
    sdef = parse_struct_definition_ast(src)
    names = [m.name for m in sdef.members]
    assert names == expect 