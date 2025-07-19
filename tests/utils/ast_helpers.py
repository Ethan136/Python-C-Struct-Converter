def flatten_member_names(sdef):
    """遞迴展平所有成員名稱（含 array 展開）"""
    result = []
    def walk(m, prefix=""):
        if hasattr(m, 'array_dims') and m.array_dims:
            from itertools import product
            dims = [range(d) for d in m.array_dims]
            for idxs in product(*dims):
                idx_str = ''.join(f"[{i}]" for i in idxs)
                if getattr(m, 'nested', None):
                    for nm in m.nested.members:
                        walk(nm, prefix + m.name + idx_str + ".")
                else:
                    result.append(prefix + m.name + idx_str)
        elif getattr(m, 'nested', None):
            for nm in m.nested.members:
                walk(nm, prefix + (m.name + "." if m.name else ""))
        else:
            result.append(prefix + (m.name if m.name else ""))
    for m in sdef.members:
        walk(m)
    return result

def assert_ast_equal(ast1, ast2):
    """遞迴比對兩個 AST 結構與型別，None/'' 視為等價"""
    assert type(ast1) == type(ast2)
    if hasattr(ast1, 'name'):
        n1 = ast1.name if ast1.name is not None else ''
        n2 = ast2.name if ast2.name is not None else ''
        assert n1 == n2
    if hasattr(ast1, 'type'):
        assert ast1.type == ast2.type
    if hasattr(ast1, 'members'):
        assert len(ast1.members) == len(ast2.members)
        for m1, m2 in zip(ast1.members, ast2.members):
            assert_ast_equal(m1, m2)
    if hasattr(ast1, 'nested') and ast1.nested:
        assert_ast_equal(ast1.nested, ast2.nested) 