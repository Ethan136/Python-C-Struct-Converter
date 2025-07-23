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

