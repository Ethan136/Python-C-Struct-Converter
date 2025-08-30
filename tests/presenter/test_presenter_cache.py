import unittest
import time
from src.model.struct_model import StructModel
from src.presenter.struct_presenter import StructPresenter

class TestPresenterCacheState(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()
        self.model.struct_content = '''
        struct CacheTest {
            int a;
            char b;
        };
        '''
        self.presenter = StructPresenter(self.model)
        self.presenter.context = {
            "display_mode": "tree",
            "expanded_nodes": ["root"],
            "selected_node": None,
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
            "debug_info": {"last_event": None}
        }

    def test_layout_cache_hit_and_miss(self):
        members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0}
        ]
        total_size = 8
        # 第一次計算應為 miss
        layout1 = self.presenter.compute_member_layout(members, total_size)
        hit1, miss1 = self.presenter.get_cache_stats()
        self.assertEqual(miss1, 1)
        # 第二次相同 key 應為 hit
        layout2 = self.presenter.compute_member_layout(members, total_size)
        hit2, miss2 = self.presenter.get_cache_stats()
        self.assertEqual(hit2, 1)
        self.assertEqual(layout1, layout2)

    def test_cache_invalidate(self):
        members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0}
        ]
        total_size = 8
        self.presenter.compute_member_layout(members, total_size)
        self.presenter.invalidate_cache()
        self.assertEqual(self.presenter.get_cache_stats(), (0, 0))
        self.assertEqual(len(self.presenter.get_cache_keys()), 0)

    def test_undo_redo_state(self):
        # 模擬 history
        ctx1 = dict(self.presenter.context)
        self.presenter.context["selected_node"] = "a"
        self.presenter.context["history"] = [ctx1]
        self.presenter.on_undo()
        self.assertEqual(self.presenter.context["selected_node"], ctx1["selected_node"])

    def test_user_settings_update(self):
        self.presenter.context["user_settings"]["theme"] = "light"
        self.assertEqual(self.presenter.context["user_settings"]["theme"], "light")
        self.presenter.context["user_settings"]["column_width"] = {"name": 120}
        self.assertEqual(self.presenter.context["user_settings"]["column_width"]["name"], 120)

    def test_debug_info_update(self):
        self.presenter.on_node_click("a")
        dbg = self.presenter.context["debug_info"]
        self.assertEqual(dbg["last_event"], "on_node_click")
        self.assertEqual(dbg["last_event_args"], {"node_id": "a"})

if __name__ == "__main__":
    unittest.main() 