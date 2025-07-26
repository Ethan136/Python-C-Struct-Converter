import os
import sys
import tkinter as tk
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'), reason="No display found, skipping GUI tests")

from src.view.struct_view import StructView


class DummyPresenter:
    def __init__(self):
        self.search_called = None
        self.filter_called = None
        self.expand_called = None
        self.collapse_called = None
        self.delete_called = False

    def on_search(self, s):
        self.search_called = s

    def on_filter(self, s):
        self.filter_called = s

    def on_expand(self, i):
        self.expand_called = i

    def on_collapse(self, i):
        self.collapse_called = i

    def on_batch_delete(self, nodes):
        self.delete_called = True


class TestStructViewV7:
    def setup_method(self):
        self.root = tk.Tk(); self.root.withdraw()
        self.presenter = DummyPresenter()
        self.view = StructView(presenter=self.presenter, enable_virtual=True,
                              virtual_page_size=10)
        self.view.update()

    def teardown_method(self):
        self.view.destroy(); self.root.destroy()

    def test_virtual_tree_limits_nodes(self):
        nodes = [{"id": f"n{i}", "name": f"N{i}", "label": f"N{i}", "children": []} for i in range(50)]
        context = {"highlighted_nodes": []}
        self.view._switch_to_modern_gui()
        self.view.show_treeview_nodes(nodes, context)
        assert len(self.view.modern_tree.get_children()) <= 10

    def test_search_and_filter_calls_presenter(self):
        self.view.search_var.set("abc")
        self.view._on_search_entry_change(None)
        assert self.presenter.search_called == "abc"
        self.view.filter_var.set("def")
        self.view._on_filter_entry_change(None)
        assert self.presenter.filter_called == "def"

    def test_keyboard_shortcut_focus(self):
        self.view.event_generate('<Control-f>'); self.view.update()
        assert self.view.focus_get() is self.view.search_entry

    def test_context_menu_calls_presenter(self):
        self.view._switch_to_modern_gui()
        tree = self.view.member_tree
        tree.insert('', 'end', iid='x', text='x')
        tree.update()
        self.view._show_node_menu(type('E', (object,), {'x_root':0,'y_root':0,'y':0})(), test_mode=True)
        assert isinstance(self.view._node_menu, tk.Menu)

    def test_highlight_nodes(self):
        nodes = [{"id": "a", "name": "A", "label": "A", "children": []}]
        ctx = {"highlighted_nodes": ["a"]}
        self.view._switch_to_modern_gui()
        self.view.show_treeview_nodes(nodes, ctx)
        assert "highlighted" in self.view.modern_tree.item("a", "tags")

    def test_switch_sets_active_tree_and_bindings(self):
        self.view._switch_to_modern_gui()
        assert self.view.member_tree is self.view.modern_tree
        # context menu binding should exist on active tree
        assert self.view.member_tree.bind("<Button-3>")

    def test_select_all_shortcut(self):
        self.view._switch_to_modern_gui()
        tree = self.view.member_tree
        for i in range(3):
            tree.insert('', 'end', iid=f'n{i}', text=f'n{i}')
        self.view.event_generate('<Control-a>'); self.view.update()
        assert set(tree.selection()) == set(tree.get_children())

    def test_context_menu_selects_node(self):
        self.view._switch_to_modern_gui()
        tree = self.view.member_tree
        tree.insert('', 'end', iid='x', text='x')
        tree.update()
        self.view._show_node_menu(type('E',(object,),{'x_root':0,'y_root':0,'y':0})(), test_mode=True)
        assert tree.selection() == ('x',)

    def test_scroll_preserves_selection(self):
        self.view._switch_to_modern_gui()
        nodes = [{"id": f"n{i}", "name": f"N{i}", "label": f"N{i}", "children": []} for i in range(20)]
        self.view.show_treeview_nodes(nodes, {"highlighted_nodes": []})
        tree = self.view.member_tree
        tree.selection_set('n0')
        # simulate scroll down
        self.view.virtual._on_scroll(type('E',(object,),{'delta':-120})())
        assert 'n0' in tree.selection()

