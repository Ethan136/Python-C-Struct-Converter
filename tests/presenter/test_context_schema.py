import unittest
from src.presenter.context_schema import validate_presenter_context
import time

class TestPresenterContextSchema(unittest.TestCase):
    def test_valid_context(self):
        context = {
            "display_mode": "tree",
            "gui_version": "legacy",
            "expanded_nodes": ["root", "nested"],
            "selected_node": "nested.x",
            "error": None,
            "filter": None,
            "search": None,
            "version": "1.0",
            "extra": {},
            "loading": False,
            "history": [],
            "user_settings": {"theme": "dark"},
            "last_update_time": time.time(),
            "readonly": False,
            "pending_action": None,
            "debug_info": {"last_event": "on_node_click"}
        }
        # 不應拋出例外
        validate_presenter_context(context)

    def test_missing_required_field(self):
        context = {
            "display_mode": "tree",
            "gui_version": "legacy",
            # 缺少 expanded_nodes
            "selected_node": "nested.x",
            "error": None,
            "version": "1.0",
            "extra": {},
            "loading": False,
            "history": [],
            "user_settings": {},
            "last_update_time": time.time(),
            "readonly": False,
            "debug_info": {}
        }
        with self.assertRaises(Exception):
            validate_presenter_context(context)

    def test_v7_gui_version_allowed(self):
        context = {
            "display_mode": "tree",
            "gui_version": "v7",
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
            "debug_info": {}
        }
        try:
            validate_presenter_context(context)
        except Exception as e:
            self.fail(f"v7 gui_version should be allowed: {e}")

    def test_wrong_type(self):
        context = {
            "display_mode": "tree",
            "gui_version": "legacy",
            "expanded_nodes": "not_a_list",  # 應為 list
            "selected_node": "nested.x",
            "error": None,
            "version": "1.0",
            "extra": {},
            "loading": False,
            "history": [],
            "user_settings": {},
            "last_update_time": time.time(),
            "readonly": False,
            "debug_info": {}
        }
        with self.assertRaises(Exception):
            validate_presenter_context(context) 
