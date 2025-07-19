import unittest
from unittest.mock import MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from src.presenter.struct_presenter import StructPresenter
from src.model.struct_model import StructModel

class MockView:
    def __init__(self):
        self.display_calls = []
        self.set_selected_node_calls = []
        self.get_selected_node_calls = []
        self.update_display_called = False
        self.last_context = None

    def update_display(self, nodes, context):
        self.display_calls.append((nodes, context.copy()))
        self.update_display_called = True
        self.last_context = context.copy()

    def set_selected_node(self, node_id):
        self.set_selected_node_calls.append(node_id)

    def get_selected_node(self):
        self.get_selected_node_calls.append(None) # No argument for now
        return "n3" # Mock a node ID

class IntegrationPresenterViewContractTest(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.view = MockView()
        self.presenter = StructPresenter(self.model, self.view)
        self.presenter._debounce_interval = 0  # 測試時立即推送
        orig_push_context = self.presenter.push_context
        def sync_push_context(*args, **kwargs):
            return orig_push_context(immediate=True)
        self.presenter.push_context = sync_push_context
        # 預設 model.get_display_nodes 回傳簡單 tree
        self.model.get_display_nodes.side_effect = lambda mode: [{"id": "root", "label": "Root", "type": "struct", "children": []}]

    def test_on_node_click_contract(self):
        self.presenter.on_node_click("root")
        nodes, context = self.view.display_calls[-1]
        self.assertEqual(context["selected_node"], "root")
        self.assertEqual(context["debug_info"]["last_event"], "on_node_click")
        self.assertIsInstance(nodes, list)
        self.assertEqual(nodes[0]["id"], "root")

    def test_on_expand_contract(self):
        self.presenter.on_expand("root")
        nodes, context = self.view.display_calls[-1]
        self.assertIn("root", context["expanded_nodes"])
        self.assertEqual(context["debug_info"]["last_event"], "on_expand")

    def test_on_switch_display_mode_contract(self):
        self.presenter.on_switch_display_mode("flat")
        nodes, context = self.view.display_calls[-1]
        self.assertEqual(context["display_mode"], "flat")
        self.assertEqual(context["expanded_nodes"], ["root"])
        self.assertIsNone(context["selected_node"])
        self.assertEqual(context["debug_info"]["last_event"], "on_switch_display_mode")

    def test_on_undo_contract(self):
        self.presenter.context["history"] = [self.presenter.get_default_context()]
        self.presenter.context["selected_node"] = "A"
        self.presenter.on_undo()
        nodes, context = self.view.display_calls[-1]
        self.assertEqual(context["debug_info"]["last_event"], "on_undo")

    def test_on_load_file_contract(self):
        import asyncio
        async def fake_parse_file(file_path):
            return {"id": "root", "name": "Root", "type": "struct", "children": []}
        self.presenter.parse_file = fake_parse_file
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.presenter.on_load_file("test.h"))
        nodes, context = self.view.display_calls[-1]
        self.assertIn("ast", context)
        self.assertFalse(context["loading"])
        self.assertEqual(context["debug_info"]["last_event"], "on_load_file")

    def test_permission_denied_contract(self):
        self.presenter.context["can_delete"] = False
        result = self.presenter.on_delete_node("root")
        nodes, context = self.view.display_calls[-1]
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "PERMISSION_DENIED")
        self.assertEqual(context["error"], "Permission denied")
        self.assertEqual(context["debug_info"]["last_error"], "PERMISSION_DENIED")

    def test_multi_event_chain_and_context_sync(self):
        # 初始化 Presenter, View, Model
        from unittest.mock import MagicMock
        model = MagicMock()
        view = MockView()
        presenter = StructPresenter(model, view)
        presenter._debounce_interval = 0
        orig_push_context = presenter.push_context
        def sync_push_context(*args, **kwargs):
            return orig_push_context(immediate=True)
        presenter.push_context = sync_push_context
        # 明確 mock
        model.get_struct_ast.return_value = {"id": "root", "children": []}
        model.get_display_nodes.side_effect = lambda mode: [{"id": "root", "label": "Root", "type": "struct", "children": []}]
        # 初始 context
        ctx = presenter.get_default_context()
        ctx["user_settings"] = {"theme": "dark"}
        ctx["readonly"] = False
        presenter.context = ctx.copy()
        # 1. 連續事件觸發
        presenter.on_node_click("n1")
        presenter.on_expand("n2")
        presenter.on_switch_display_mode("flat")
        presenter.on_collapse("n2")
        presenter.set_readonly(True)
        # 2. View 狀態回饋
        view.set_selected_node("n3")
        presenter.on_node_click(view.get_selected_node())
        # 3. Model 資料異動
        model.struct_content = "struct X { int a; }"  # 模擬 model 變動
        presenter.update("manual_struct_changed", model)
        # 4. 驗證 context 欄位同步
        self.assertEqual(presenter.context["selected_node"], "n3")
        self.assertTrue(presenter.context["readonly"])
        self.assertEqual(presenter.context["display_mode"], "flat")
        self.assertEqual(presenter.context["expanded_nodes"], ["root"])
        self.assertEqual(presenter.context["user_settings"], {"theme": "dark"})
        # 5. 驗證 View 有收到 context 推送
        self.assertTrue(view.update_display_called)
        self.assertIsInstance(view.last_context, dict)
        self.assertEqual(view.last_context["selected_node"], "n3")

if __name__ == "__main__":
    unittest.main() 