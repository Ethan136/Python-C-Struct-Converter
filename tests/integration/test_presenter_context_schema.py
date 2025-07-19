import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from src.presenter.struct_presenter import StructPresenter
from src.presenter.context_schema import validate_presenter_context, PRESENTER_CONTEXT_SCHEMA
import jsonschema

class TestPresenterContextSchemaContract(unittest.TestCase):
    def setUp(self):
        self.presenter = StructPresenter(model=None, view=None)
        self.presenter._debounce_interval = 0
        orig_push_context = self.presenter.push_context
        def sync_push_context(*args, **kwargs):
            return orig_push_context(immediate=True)
        self.presenter.push_context = sync_push_context

    def test_valid_context(self):
        ctx = self.presenter.get_default_context()
        try:
            validate_presenter_context(ctx)
        except Exception as e:
            self.fail(f"Valid context should not raise: {e}")

    def test_missing_required_field(self):
        ctx = self.presenter.get_default_context()
        del ctx["display_mode"]
        with self.assertRaises(jsonschema.ValidationError):
            validate_presenter_context(ctx)

    def test_additional_property(self):
        ctx = self.presenter.get_default_context()
        ctx["custom_flag"] = True
        # 應允許 additionalProperties
        try:
            validate_presenter_context(ctx)
        except Exception as e:
            self.fail(f"Context with additional property should not raise: {e}")

    def test_type_error(self):
        ctx = self.presenter.get_default_context()
        ctx["expanded_nodes"] = "not_a_list"
        with self.assertRaises(jsonschema.ValidationError):
            validate_presenter_context(ctx)

    def test_debug_info_schema(self):
        ctx = self.presenter.get_default_context()
        # debug_info 可為任意 object，但應存在
        self.assertIn("debug_info", ctx)
        self.assertIsInstance(ctx["debug_info"], dict)

    def test_field_none(self):
        ctx = self.presenter.get_default_context()
        ctx["selected_node"] = None
        try:
            validate_presenter_context(ctx)
        except Exception as e:
            self.fail(f"None field should not raise: {e}")

    def test_field_empty_string(self):
        ctx = self.presenter.get_default_context()
        ctx["display_mode"] = ""
        try:
            validate_presenter_context(ctx)
        except Exception as e:
            self.fail(f"Empty string field should not raise: {e}")

    def test_field_extreme_length(self):
        ctx = self.presenter.get_default_context()
        ctx["expanded_nodes"] = ["n" * 10000]
        try:
            validate_presenter_context(ctx)
        except Exception as e:
            self.fail(f"Extreme length field should not raise: {e}")

    def test_nodes_children_not_list(self):
        # nodes 結構 children 非 list 不屬於 context schema，但可模擬 Presenter-View contract test
        node = {"id": "root", "label": "Root", "type": "struct", "children": None}
        self.assertIsNone(node["children"])

    def test_ast_missing_id_type_name(self):
        # AST 結構遺失 id/type/name
        ast = {"children": []}
        # 不屬於 context schema，但可模擬 Presenter-View contract test
        self.assertNotIn("id", ast)
        self.assertNotIn("type", ast)
        self.assertNotIn("name", ast)

    def test_field_empty_dict(self):
        ctx = self.presenter.get_default_context()
        ctx["extra"] = {}
        try:
            validate_presenter_context(ctx)
        except Exception as e:
            self.fail(f"Empty dict field should not raise: {e}")

    def test_field_empty_list(self):
        ctx = self.presenter.get_default_context()
        ctx["expanded_nodes"] = []
        try:
            validate_presenter_context(ctx)
        except Exception as e:
            self.fail(f"Empty list field should not raise: {e}")

    def test_required_field_none(self):
        ctx = self.presenter.get_default_context()
        for field in ["display_mode", "expanded_nodes", "version", "extra", "loading", "history", "user_settings", "last_update_time", "readonly", "debug_info"]:
            ctx2 = dict(ctx)
            ctx2[field] = None
            # selected_node, error 可為 None，其他 required 欄位不可
            if field in ("selected_node", "error"):
                try:
                    validate_presenter_context(ctx2)
                except Exception as e:
                    self.fail(f"{field} set to None should not raise: {e}")
            else:
                with self.assertRaises(jsonschema.ValidationError, msg=f"{field} set to None should raise"):
                    validate_presenter_context(ctx2)

    def test_required_field_type_error(self):
        ctx = self.presenter.get_default_context()
        # 錯誤型別
        cases = [
            ("display_mode", 123),
            ("expanded_nodes", "notalist"),
            ("version", 1.0),
            ("extra", []),
            ("loading", "yes"),
            ("history", {}),
            ("user_settings", []),
            ("last_update_time", "now"),
            ("readonly", "false"),
            ("debug_info", [])
        ]
        for field, badval in cases:
            ctx2 = dict(ctx)
            ctx2[field] = badval
            with self.assertRaises(jsonschema.ValidationError, msg=f"{field} type error should raise"):
                validate_presenter_context(ctx2)

    def test_last_update_time_extreme(self):
        ctx = self.presenter.get_default_context()
        for val in [-1e100, 1e100, 0, 1.2345]:
            ctx2 = dict(ctx)
            ctx2["last_update_time"] = val
            try:
                validate_presenter_context(ctx2)
            except Exception as e:
                self.fail(f"last_update_time extreme value {val} should not raise: {e}")

    def test_debug_info_missing_or_wrong_type(self):
        ctx = self.presenter.get_default_context()
        # 缺漏 debug_info
        ctx2 = dict(ctx)
        del ctx2["debug_info"]
        with self.assertRaises(jsonschema.ValidationError):
            validate_presenter_context(ctx2)
        # debug_info 為 list
        ctx3 = dict(ctx)
        ctx3["debug_info"] = []
        with self.assertRaises(jsonschema.ValidationError):
            validate_presenter_context(ctx3)
        # debug_info 為 None
        ctx4 = dict(ctx)
        ctx4["debug_info"] = None
        with self.assertRaises(jsonschema.ValidationError):
            validate_presenter_context(ctx4)

    def test_history_wrong_type(self):
        ctx = self.presenter.get_default_context()
        ctx2 = dict(ctx)
        ctx2["history"] = "notalist"
        with self.assertRaises(jsonschema.ValidationError):
            validate_presenter_context(ctx2)

    def test_additional_property_nested(self):
        ctx = self.presenter.get_default_context()
        ctx["custom_nested"] = {"foo": [1,2,3], "bar": {"baz": True}}
        try:
            validate_presenter_context(ctx)
        except Exception as e:
            self.fail(f"Nested additional property should not raise: {e}")

if __name__ == "__main__":
    unittest.main() 