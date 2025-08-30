import os
import re


def test_no_obvious_hardcoded_ui_strings():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sv_path = os.path.join(root_dir, "src", "view", "struct_view.py")
    content = open(sv_path, "r", encoding="utf-8").read()
    # Find patterns like text="..." with non-empty string literals
    pattern = re.compile(r"text=\s*\"[^\"]+\"|text=\s*'[^']+'")
    matches = pattern.findall(content)
    # Whitelist allowed terms that are not UI labels or are handled via get_string later
    whitelist_substrings = [
        "text=\"\"",  # empty
        "font=",         # font spec, not text
    ]
    offenders = []
    for m in matches:
        if not any(w in m for w in whitelist_substrings) and "get_string(" not in m:
            offenders.append(m)
    assert not offenders, f"Hardcoded UI text remains: {offenders[:5]}... total={len(offenders)}"

