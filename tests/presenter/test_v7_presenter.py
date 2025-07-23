"""Tests for the V7Presenter class."""

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

