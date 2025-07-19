import unittest
from unittest.mock import MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from src.presenter.struct_presenter import StructPresenter

class MockView:
    def __init__(self):
        self.display_calls = []
    def update_display(self, nodes, context):
        self.display_calls.append((nodes, context.copy()))

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

if __name__ == "__main__":
    unittest.main() 