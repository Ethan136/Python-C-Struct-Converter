"""StructLayout component that renders unified layout+values in a Treeview.

This component encapsulates insertion of rows following UNIFIED_LAYOUT_VALUE_COLUMNS.
It can either create its own Treeview or be bound to an existing one.
"""

from typing import List, Dict, Optional

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:
    class _DummyTkModule:
        class Tk: ...
        class Label: ...
        class LabelFrame: ...
        class Frame: ...
        class Entry: ...
        class Scrollbar: ...
        END = "end"
    tk = _DummyTkModule()

    class _DummyTtkModule:
        class Treeview: ...
        class Notebook: ...
        class Frame: ...
        class Button: ...
        class Entry: ...
        class Label: ...
        class Combobox: ...
        class LabelFrame: ...
    ttk = _DummyTtkModule()

from src.config.columns import UNIFIED_LAYOUT_VALUE_COLUMNS


class StructLayout:
    def __init__(self, parent=None, tree: Optional["ttk.Treeview"] = None):
        self.parent = parent
        self.tree = tree or self._create_tree(parent)
        self.display_mode = "tree"  # placeholder for future behavior

    def _create_tree(self, parent):
        col_names = tuple(UNIFIED_LAYOUT_VALUE_COLUMNS)
        tree = ttk.Treeview(
            parent,
            columns=col_names,
            show="headings",
            height=10,
        )
        # Basic column widths; can be overridden by caller
        default_widths = {
            "name": 120,
            "type": 100,
            "offset": 80,
            "size": 80,
            "bit_offset": 80,
            "bit_size": 80,
            "is_bitfield": 80,
            "value": 100,
            "hex_value": 100,
            "hex_raw": 120,
        }
        for c in UNIFIED_LAYOUT_VALUE_COLUMNS:
            tree.heading(c, text=c)
            tree.column(c, width=default_widths.get(c, 100), stretch=False)
        tree["displaycolumns"] = col_names
        tree.pack(side="left", fill="both", expand=True)
        return tree

    def set_display_mode(self, mode: str):
        # Reserved for future: currently only records the mode
        if mode in ("tree", "flat"):
            self.display_mode = mode

    def set_rows(self, rows: List[Dict]):
        # Full rebuild
        try:
            for iid in self.tree.get_children():
                self.tree.delete(iid)
        except Exception:
            pass
        self._insert_rows(rows)

    def refresh_values(self, rows: List[Dict]):
        # For simplicity, rebuild just like set_rows to ensure correctness
        self.set_rows(rows)

    def _insert_rows(self, rows: List[Dict]):
        for row in rows or []:
            try:
                name_str = str(row.get("name", ""))
                type_str = str(row.get("type", ""))
                offset_str = str(row.get("offset", ""))
                size_str = str(row.get("size", ""))
                bit_offset = row.get("bit_offset")
                bit_size = row.get("bit_size")
                bit_offset_str = str(bit_offset) if bit_offset is not None else "-"
                bit_size_str = str(bit_size) if bit_size is not None else "-"
                is_bf_str = str(row.get("is_bitfield", False))
                value = row.get("value", "")
                hex_value = row.get("hex_value", "")
                hex_raw = row.get("hex_raw", "")
                if hex_raw and isinstance(hex_raw, str) and len(hex_raw) > 2:
                    try:
                        hex_raw = "｜".join(hex_raw[j:j+2] for j in range(0, len(hex_raw), 2))
                    except Exception:
                        pass
                self.tree.insert("", "end", values=(
                    name_str,
                    type_str,
                    offset_str,
                    size_str,
                    bit_offset_str,
                    bit_size_str,
                    is_bf_str,
                    str(value) if value is not None else "",
                    str(hex_value) if hex_value is not None else "",
                    str(hex_raw) if hex_raw is not None else "",
                ))
            except Exception:
                continue

