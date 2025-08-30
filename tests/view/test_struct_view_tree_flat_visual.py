import os
import pytest
import tkinter as tk

pytestmark = pytest.mark.skipif(
    not os.environ.get('DISPLAY'), reason="No display found, skipping GUI tests"
)

def test_tree_mode_shows_tree_column_and_nested_children():
    from src.view.struct_view import StructView
    from tests.view.test_struct_view import PresenterStub
    root = tk.Tk(); root.withdraw()
    presenter = PresenterStub()
    view = StructView(presenter=presenter)
    presenter.view = view
    nodes = [
        {"id": "root", "label": "Root", "type": "struct", "children": [
            {"id": "child", "label": "Child", "type": "int", "children": []}
        ]}
    ]
    presenter.get_display_nodes = lambda mode: nodes
    presenter.context["display_mode"] = "tree"
    presenter.context["expanded_nodes"] = ["root"]
    view.update_display(nodes, presenter.context)
    assert "tree" in str(view.member_tree.cget("show"))
    root_items = view.member_tree.get_children("")
    assert root_items, "Tree should have root items"
    child_items = view.member_tree.get_children(root_items[0])
    assert child_items, "Tree mode should show nested children"
    view.destroy(); root.destroy()

def test_flat_mode_hides_tree_column_and_has_no_children():
    from src.view.struct_view import StructView
    from tests.view.test_struct_view import PresenterStub
    root = tk.Tk(); root.withdraw()
    presenter = PresenterStub()
    view = StructView(presenter=presenter)
    presenter.view = view
    nodes = [
        {"id": "root", "label": "Root", "type": "struct", "children": [
            {"id": "child", "label": "Child", "type": "int", "children": []}
        ]}
    ]
    presenter.get_display_nodes = lambda mode: nodes
    presenter.context["display_mode"] = "flat"
    presenter.context["expanded_nodes"] = ["root"]
    view.update_display(nodes, presenter.context)
    assert str(view.member_tree.cget("show")) == "headings"
    # 所有根項目應無子節點（平面列表）
    root_items = view.member_tree.get_children("")
    for iid in root_items:
        assert not view.member_tree.get_children(iid)
    view.destroy(); root.destroy()

