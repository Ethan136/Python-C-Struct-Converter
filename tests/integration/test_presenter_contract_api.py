import unittest
from unittest.mock import MagicMock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from src.presenter.struct_presenter import StructPresenter

class ContractPresenterAPITest(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.view = MagicMock()
        self.presenter = StructPresenter(self.model, self.view)
        self.presenter._debounce_interval = 0
        orig_push_context = self.presenter.push_context
        def sync_push_context(*args, **kwargs):
            return orig_push_context(immediate=True)
        self.presenter.push_context = sync_push_context
        self.model.get_struct_ast.return_value = {"id": "root", "children": []}
        self.model.get_display_nodes.side_effect = lambda mode: [{"id": "root", "label": "Root", "type": "struct", "children": []}]

    def test_get_struct_ast_contract(self):
        ast = self.presenter.get_struct_ast()
        self.assertIsInstance(ast, dict)
        self.assertIn("id", ast)

    def test_get_display_nodes_contract(self):
        nodes = self.presenter.get_display_nodes("tree")
        self.assertIsInstance(nodes, list)
        self.assertIn("id", nodes[0])

    def test_on_node_click_and_context(self):
        self.presenter.on_node_click("n1")
        self.assertEqual(self.presenter.context["selected_node"], "n1")
        self.assertEqual(self.presenter.context["debug_info"]["last_event"], "on_node_click")
        self.assertEqual(self.presenter.context["debug_info"]["last_event_args"], {"node_id": "n1"})

    def test_on_expand_and_context(self):
        self.presenter.on_expand("n2")
        self.assertIn("n2", self.presenter.context["expanded_nodes"])
        self.assertEqual(self.presenter.context["debug_info"]["last_event"], "on_expand")

    def test_on_switch_display_mode_and_context(self):
        self.presenter.on_switch_display_mode("flat")
        self.assertEqual(self.presenter.context["display_mode"], "flat")
        self.assertEqual(self.presenter.context["expanded_nodes"], ["root"])
        self.assertIsNone(self.presenter.context["selected_node"])
        self.assertEqual(self.presenter.context["debug_info"]["last_event"], "on_switch_display_mode")

    def test_on_undo_redo_contract(self):
        ctx0 = self.presenter.get_default_context()
        ctx1 = self.presenter.get_default_context()
        ctx1["selected_node"] = "A"
        self.presenter.context = ctx0.copy()
        self.presenter.context["history"] = [ctx1.copy()]
        self.presenter.on_undo()
        self.assertEqual(self.presenter.context["debug_info"]["last_event"], "on_undo")
        self.presenter.context["redo_history"] = [ctx1.copy()]
        self.presenter.on_redo()
        self.assertEqual(self.presenter.context["debug_info"]["last_event"], "on_redo")

    def test_permission_denied_contract(self):
        self.presenter.context["can_delete"] = False
        result = self.presenter.on_delete_node("n1")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "PERMISSION_DENIED")
        self.assertEqual(self.presenter.context["error"], "Permission denied")
        self.assertEqual(self.presenter.context["debug_info"]["last_error"], "PERMISSION_DENIED")

    def test_context_schema_fields(self):
        ctx = self.presenter.context
        required_fields = [
            "display_mode", "expanded_nodes", "selected_node", "error", "version", "extra", "loading", "history", "user_settings", "last_update_time", "readonly", "debug_info"
        ]
        for f in required_fields:
            self.assertIn(f, ctx)
        self.assertIsInstance(ctx["debug_info"], dict)
        self.assertIn("last_event", ctx["debug_info"])
        self.assertIn("context_history", ctx["debug_info"])

    def test_error_handling_and_reset(self):
        self.presenter.context["error"] = "Some error"
        self.presenter.push_context()
        self.presenter.context["error"] = None
        self.presenter.push_context()
        self.assertIsNone(self.presenter.context["error"])

    def test_context_version_backward_compatibility(self):
        # 舊版 context 不含新欄位，Presenter 應能兼容
        ctx = self.presenter.get_default_context()
        ctx.pop("pending_action", None)
        ctx["version"] = "1.0"
        self.presenter.context = ctx
        try:
            self.presenter.push_context()
        except Exception as e:
            self.fail(f"push_context failed on old version context: {e}")

    def test_context_missing_required_field(self):
        # 缺少 required 欄位應拋出 schema 驗證錯誤
        ctx = self.presenter.get_default_context()
        ctx.pop("debug_info", None)
        self.presenter.context = ctx
        with self.assertRaises(Exception):
            self.presenter.push_context()

    def test_context_field_type_error(self):
        # 欄位型別錯誤應拋出 schema 驗證錯誤
        ctx = self.presenter.get_default_context()
        ctx["expanded_nodes"] = "not_a_list"
        self.presenter.context = ctx
        with self.assertRaises(Exception):
            self.presenter.push_context()

    def test_extreme_history_redo_stack(self):
        # 超大 history/redo stack
        ctx = self.presenter.get_default_context()
        ctx["history"] = [ctx.copy() for _ in range(500)]
        ctx["redo_history"] = [ctx.copy() for _ in range(500)]
        self.presenter.context = ctx
        try:
            self.presenter.on_undo()
            self.presenter.on_redo()
        except Exception as e:
            self.fail(f"undo/redo failed on large stack: {e}")

    def test_context_reset_and_fallback(self):
        # context reset/fallback 行為
        self.presenter.context["selected_node"] = "n999"
        self.presenter.reset_context()
        ctx = self.presenter.context
        self.assertEqual(ctx["display_mode"], "tree")
        self.assertEqual(ctx["expanded_nodes"], ["root"])
        self.assertIsNone(ctx["selected_node"])

if __name__ == "__main__":
    unittest.main() 