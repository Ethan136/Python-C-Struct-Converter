import unittest
from unittest.mock import MagicMock
import time
from src.model.struct_model import StructModel
from src.presenter.struct_presenter import StructPresenter

class MockView:
    def __init__(self):
        self.last_nodes = None
        self.last_context = None
        self.update_display_called = False
    def update_display(self, nodes, context):
        self.last_nodes = nodes
        self.last_context = context
        self.update_display_called = True

class TestPresenterMockView(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()
        self.model.struct_content = '''
        struct MockTest {
            int a;
            char b;
        };
        '''
        self.view = MockView()
        self.presenter = StructPresenter(self.model, self.view)
        # 讓 push_context 立即執行，避免 debounce 影響
        self.presenter._debounce_interval = 0
        orig_push_context = self.presenter.push_context
        def sync_push_context(*args, **kwargs):
            return orig_push_context(immediate=True)
        self.presenter.push_context = sync_push_context
        self.presenter.context = {
            "display_mode": "tree",
            "gui_version": "legacy",
            "expanded_nodes": ["root"],
            "selected_node": None,
            "error": None,
            "filter": None,
            "search": None,
            "version": "1.0",
            "extra": {},
            "loading": False,
            "history": [],
            "user_settings": {},
            "last_update_time": time.time(),
            "readonly": False,
            "pending_action": None,
            "debug_info": {"last_event": None}
        }

    def test_on_switch_display_mode_pushes_context(self):
        self.presenter.on_switch_display_mode("flat")
        self.assertTrue(self.view.update_display_called)
        self.assertEqual(self.view.last_context["display_mode"], "flat")
        self.assertIsInstance(self.view.last_nodes, list)
        self.assertIn("label", self.view.last_nodes[0])

    def test_on_delete_node_permission_denied(self):
        self.presenter.context["can_delete"] = False
        result = self.presenter.on_delete_node("a")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "PERMISSION_DENIED")
        self.assertTrue(self.view.update_display_called)
        self.assertEqual(self.view.last_context["error"], "Permission denied")

    def test_on_pointer_mode_toggle_triggers_cache_and_push(self):
        # Spy
        from unittest.mock import MagicMock
        self.presenter.invalidate_cache = MagicMock()
        self.presenter.push_context = MagicMock()
        self.presenter.on_pointer_mode_toggle(True)
        self.presenter.invalidate_cache.assert_called_once()
        self.presenter.push_context.assert_called_once()
        self.assertEqual(self.presenter.context.get("arch_mode"), "x86")

if __name__ == "__main__":
    unittest.main() 