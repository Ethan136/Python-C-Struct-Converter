"""Tests for the V7Presenter class."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.presenter.v7_presenter import V7Presenter


class TestV7Presenter:
    def test_load_struct_and_get_layout(self):
        content = """
        struct Simple {
            int x;
            char y;
        };
        """
        presenter = V7Presenter()
        assert presenter.load_struct_definition(content) is True
        ast = presenter.get_ast_tree()
        assert ast is not None
        assert ast.name == "Simple"
        layout = presenter.get_flattened_layout()
        assert len(layout) == 2
        assert presenter.context["loading"] is False
        assert presenter.context["error"] is None

    def test_load_struct_failure(self):
        presenter = V7Presenter()
        assert presenter.load_struct_definition("not a struct") is False
        assert presenter.context["error"] is not None

    def test_get_display_nodes_tree_and_flat(self):
        content = """
        struct Sample {
            int a;
            char b;
        };
        """
        presenter = V7Presenter()
        assert presenter.load_struct_definition(content) is True

        tree_nodes = presenter.get_display_nodes("tree")
        assert isinstance(tree_nodes, list)
        assert tree_nodes and tree_nodes[0]["type"] == "struct"
        child_labels = [c["label"] for c in tree_nodes[0]["children"]]
        assert "a: int" in child_labels
        assert "b: char" in child_labels

        flat_nodes = presenter.get_display_nodes("flat")
        flat_labels = [n["label"] for n in flat_nodes]
        assert flat_labels == ["a: int", "b: char"]
        layout = presenter.get_flattened_layout()
        assert layout[0].offset == 0
        assert layout[1].offset == layout[0].size

    def test_search_and_filter(self):
        content = """
        struct Sample {
            int a;
            int b;
        };
        """
        presenter = V7Presenter()
        presenter.load_struct_definition(content)
        presenter.on_search("b")
        assert presenter.context["highlighted_nodes"]
        presenter.on_filter("b")
        nodes = presenter.get_display_nodes("tree")
        assert len(nodes[0]["children"]) == 1
        assert "b" in nodes[0]["children"][0]["label"]

    def test_view_update_on_load(self):
        class DummyView:
            def __init__(self):
                self.called = False
                self.nodes = None
                self.context = None

            def update_display(self, nodes, context):
                self.called = True
                self.nodes = nodes
                self.context = context

        content = """
        struct Foo {
            int a;
        };
        """
        view = DummyView()
        presenter = V7Presenter(view=view)
        assert presenter.context["gui_version"] == "v7"
        assert presenter.load_struct_definition(content) is True
        assert view.called is True
        assert view.nodes
        assert view.context["loading"] is False

    def test_switch_display_mode_updates_context(self):
        class DummyView:
            def __init__(self):
                self.called = False
                self.context = None

            def update_display(self, nodes, context):
                self.called = True
                self.context = context

        content = """
        struct Foo {
            int a;
        };
        """
        view = DummyView()
        presenter = V7Presenter(view=view)
        presenter.load_struct_definition(content)

        prev_time = presenter.context["last_update_time"]
        presenter.switch_display_mode("flat")

        assert presenter.context["display_mode"] == "flat"
        assert view.called is True
        assert view.context["display_mode"] == "flat"
        assert presenter.context["last_update_time"] >= prev_time

