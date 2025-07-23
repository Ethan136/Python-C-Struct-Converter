from tkinter import ttk
import tkinter as tk

from .struct_view import StructView, update_treeview_by_context
from .virtual_tree import VirtualTreeview


class StructViewV7(StructView):
    """Modern view with virtualized tree rendering and shortcuts."""

    def __init__(self, presenter=None, page_size=100):
        self._virtual_page_size = page_size
        super().__init__(presenter=presenter)

    def _switch_to_v7_gui(self):
        """Use modern GUI and setup virtualization."""
        super()._switch_to_modern_gui()
        if hasattr(self, "modern_tree"):
            self.virtual = VirtualTreeview(self.modern_tree, self._virtual_page_size)
            self.member_tree = self.modern_tree
            self._bind_member_tree_events()

    # override to load nodes into virtual tree
    def show_treeview_nodes(self, nodes, context, icon_map=None):
        if hasattr(self, "virtual"):
            flat = self._flatten_nodes(nodes, context=context)
            self.virtual.set_nodes(flat)
            update_treeview_by_context(self.modern_tree, context)
        else:
            super().show_treeview_nodes(nodes, context, icon_map)

    def _flatten_nodes(self, nodes, depth=0, context=None):
        result = []
        highlighted = set(context.get("highlighted_nodes", [])) if context else set()
        for n in nodes:
            n2 = n.copy()
            n2["label"] = ("  " * depth) + n2.get("label", n2.get("name", ""))
            tags = []
            t = n2.get("type")
            if t == "struct":
                tags.append("struct")
            elif t == "union":
                tags.append("union")
            elif t == "bitfield":
                tags.append("bitfield")
            elif t == "array":
                tags.append("array")
            if n2.get("id") in highlighted:
                tags.append("highlighted")
            if tags:
                n2["tags"] = tags
            result.append(n2)
            if n.get("children"):
                result.extend(self._flatten_nodes(n["children"], depth + 1, context))
        return result

    # keyboard shortcuts
    def _init_presenter_view_binding(self):
        super()._init_presenter_view_binding()
        self.bind_all("<Control-f>", lambda e: self.search_entry.focus_set())
        self.bind_all("<Control-l>", lambda e: self.filter_entry.focus_set())
        self.bind_all("<Delete>", lambda e: self._on_batch_delete())

    # context menu for nodes
    def _bind_member_tree_events(self):
        super()._bind_member_tree_events()
        if hasattr(self, "member_tree"):
            self.member_tree.bind("<Button-3>", lambda e: self._show_node_menu(e))

    def _show_node_menu(self, event, test_mode=False):
        tree = self.member_tree
        item = tree.identify_row(event.y)
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(label="Expand", command=lambda: self.presenter.on_expand(item) if self.presenter else None)
        menu.add_command(label="Collapse", command=lambda: self.presenter.on_collapse(item) if self.presenter else None)
        menu.add_separator()
        menu.add_command(label="Delete", command=self._on_batch_delete)
        self._node_menu = menu
        if not test_mode:
            menu.tk_popup(event.x_root, event.y_root)

