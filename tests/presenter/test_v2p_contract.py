import unittest
from unittest.mock import MagicMock
import time
from src.model.struct_model import StructModel
from src.presenter.struct_presenter import StructPresenter
from src.presenter.context_schema import validate_presenter_context

class TestV2PAPIContract(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()
        # 預設 struct_content 供 AST 產生
        self.model.struct_content = '''
        struct V2PTest {
            int a;
            char b;
        };
        '''
        self.presenter = StructPresenter(self.model)
        self.presenter.view = MagicMock()
        # 預設 context 初始化
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
            "user_settings": {},
            "last_update_time": time.time(),
            "readonly": False,
            "pending_action": None,
            "debug_info": {"last_event": None}
        }

    def test_get_struct_ast_contract(self):
        # 準備一個簡單 struct
        code = '''
        struct V2PTest {
            int a;
            char b;
        };
        '''
        self.model.struct_content = code
        ast = self.presenter.model.get_struct_ast()
        # 應包含 V2P API 文件定義的欄位
        self.assertIn("id", ast)
        self.assertIn("name", ast)
        self.assertIn("type", ast)
        self.assertIn("children", ast)
        self.assertIn("is_struct", ast)
        self.assertIn("is_union", ast)
        self.assertIn("offset", ast)
        self.assertIn("size", ast)
        # children 也要驗證
        for child in ast["children"]:
            self.assertIn("id", child)
            self.assertIn("name", child)
            self.assertIn("type", child)
            self.assertIn("children", child)

    def test_get_display_nodes_contract(self):
        code = '''
        struct V2PTest {
            int a;
            char b;
        };
        '''
        self.model.struct_content = code
        nodes = self.model.get_display_nodes(mode="tree")
        self.assertIsInstance(nodes, list)
        for node in nodes:
            self.assertIn("id", node)
            self.assertIn("label", node)
            self.assertIn("type", node)
            self.assertIn("children", node)

    def test_context_schema_contract(self):
        # 驗證 context schema
        validate_presenter_context(self.presenter.context)

    def test_on_switch_display_mode_event(self):
        # 切換顯示模式事件
        self.presenter.on_switch_display_mode("flat")
        self.assertEqual(self.presenter.context["display_mode"], "flat")
        # context schema 仍應通過
        validate_presenter_context(self.presenter.context)

    def test_error_handling_contract(self):
        # 權限不足時應回傳標準錯誤格式
        self.presenter.context["can_delete"] = False
        result = self.presenter.on_delete_node("some_id")
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertFalse(result["success"])
        self.assertIn("error_code", result)
        self.assertIn("error_message", result)
        self.assertEqual(result["error_code"], "PERMISSION_DENIED")

if __name__ == "__main__":
    unittest.main() 