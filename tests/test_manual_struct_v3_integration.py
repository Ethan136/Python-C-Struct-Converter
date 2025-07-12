import unittest
import sys
import os
import tkinter as tk

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.view.struct_view import StructView
from src.model.struct_model import StructModel

class TestManualStructV3Integration(unittest.TestCase):
    """測試 V3 版本的完整 MyStruct 工作流程"""
    
    def setUp(self):
        self.root = tk.Tk()
        self.view = StructView()
        self.model = StructModel()
        # 切換到手動 struct tab
        self.view.tab_control.select(self.view.tab_manual)
    
    def tearDown(self):
        self.root.destroy()
    
    def test_complete_workflow_v3_format(self):
        """測試完整的 V3 工作流程"""
        # 1. 設定結構體名稱和大小
        self.view.struct_name_var.set("UserInfo")
        self.view.size_var.set(16)
        
        # 2. 新增成員
        self.view._add_member()  # 第一個成員
        self.view._add_member()  # 第二個成員
        self.view._add_member()  # 第三個成員
        
        # 3. 設定成員資料
        self.view.members[0]["name"] = "user_id"
        self.view.members[0]["type"] = "unsigned long long"
        self.view.members[0]["bit_size"] = 0
        
        self.view.members[1]["name"] = "status"
        self.view.members[1]["type"] = "unsigned int"
        self.view.members[1]["bit_size"] = 4
        
        self.view.members[2]["name"] = "name"
        self.view.members[2]["type"] = "char"
        self.view.members[2]["bit_size"] = 0
        
        # 4. 取得結構體定義
        struct_data = self.view.get_manual_struct_definition()
        
        # 5. 驗證資料結構
        self.assertEqual(struct_data["struct_name"], "UserInfo")
        self.assertEqual(struct_data["total_size"], 16)
        self.assertEqual(len(struct_data["members"]), 3)
        
        # 6. 驗證成員資料
        self.assertEqual(struct_data["members"][0]["name"], "user_id")
        self.assertEqual(struct_data["members"][0]["type"], "unsigned long long")
        self.assertEqual(struct_data["members"][0]["bit_size"], 0)
        
        self.assertEqual(struct_data["members"][1]["name"], "status")
        self.assertEqual(struct_data["members"][1]["type"], "unsigned int")
        self.assertEqual(struct_data["members"][1]["bit_size"], 4)
        
        self.assertEqual(struct_data["members"][2]["name"], "name")
        self.assertEqual(struct_data["members"][2]["type"], "char")
        self.assertEqual(struct_data["members"][2]["bit_size"], 0)
        
        # 7. 驗證 Model 層處理
        errors = self.model.validate_manual_struct(struct_data["members"], struct_data["total_size"])
        self.assertEqual(len(errors), 0)  # 應該沒有錯誤
        
        # 8. 驗證使用空間計算
        used_bits = self.model.calculate_used_bits(struct_data["members"])
        expected_bits = 64 + 4 + 8  # unsigned long long + 4 bits + char
        self.assertEqual(used_bits, expected_bits)
        
        # 9. 驗證匯出功能
        self.model.set_manual_struct(struct_data["members"], struct_data["total_size"])
        h_content = self.model.export_manual_struct_to_h("UserInfo")
        
        # 檢查匯出內容
        self.assertIn("struct UserInfo", h_content)
        self.assertIn("unsigned long long user_id;", h_content)
        self.assertIn("unsigned int status : 4;", h_content)
        self.assertIn("char name;", h_content)
        self.assertIn("// total size: 16 bytes", h_content)
    
    def test_bitfield_type_restrictions(self):
        """測試 bitfield 型別限制"""
        # 設定結構體
        self.view.struct_name_var.set("TestStruct")
        self.view.size_var.set(8)
        
        # 新增成員並設定為 bitfield
        self.view._add_member()
        self.view.members[0]["name"] = "flags"
        self.view.members[0]["type"] = "unsigned int"
        self.view.members[0]["bit_size"] = 8
        
        # 驗證 bitfield 型別選項
        bitfield_options = self.view._get_type_options(is_bitfield=True)
        self.assertIn("unsigned int", bitfield_options)
        self.assertNotIn("float", bitfield_options)
        self.assertNotIn("double", bitfield_options)
        
        # 驗證 Model 層接受有效的 bitfield 型別
        struct_data = self.view.get_manual_struct_definition()
        errors = self.model.validate_manual_struct(struct_data["members"], struct_data["total_size"])
        self.assertEqual(len(errors), 0)
    
    def test_invalid_bitfield_type_rejection(self):
        """測試無效 bitfield 型別的拒絕"""
        # 設定結構體
        self.view.struct_name_var.set("TestStruct")
        self.view.size_var.set(8)
        
        # 新增成員並設定為無效的 bitfield 型別
        self.view._add_member()
        self.view.members[0]["name"] = "flags"
        self.view.members[0]["type"] = "float"  # 無效的 bitfield 型別
        self.view.members[0]["bit_size"] = 8
        
        # 驗證 Model 層拒絕無效的 bitfield 型別
        struct_data = self.view.get_manual_struct_definition()
        errors = self.model.validate_manual_struct(struct_data["members"], struct_data["total_size"])
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("bitfield 只支援" in error for error in errors))
    
    def test_backward_compatibility_legacy_format(self):
        """測試向後相容性 - 舊格式支援"""
        # 設定結構體
        self.view.struct_name_var.set("LegacyStruct")
        self.view.size_var.set(8)
        
        # 使用舊格式的成員資料（包含 byte_size）
        legacy_members = [
            {"name": "a", "byte_size": 4, "bit_size": 0},
            {"name": "b", "byte_size": 0, "bit_size": 4}
        ]
        
        # 驗證 Model 層能處理舊格式
        errors = self.model.validate_manual_struct(legacy_members, 8)
        self.assertEqual(len(errors), 0)
        
        # 驗證型別轉換
        converted_members = self.model._convert_to_cpp_members(legacy_members)
        self.assertEqual(len(converted_members), 2)
        self.assertEqual(converted_members[0]["type"], "int")
        self.assertEqual(converted_members[1]["type"], "unsigned int")
        self.assertTrue(converted_members[1]["is_bitfield"])
    
    def test_mixed_format_support(self):
        """測試混合格式支援（新舊格式混合）"""
        # 設定結構體
        self.view.struct_name_var.set("MixedStruct")
        self.view.size_var.set(12)
        
        # 混合新舊格式
        mixed_members = [
            {"name": "legacy", "byte_size": 4, "bit_size": 0},  # 舊格式
            {"name": "new", "type": "char", "bit_size": 0},     # 新格式
            {"name": "bitfield", "type": "unsigned int", "bit_size": 8}  # 新格式 bitfield
        ]
        
        # 驗證 Model 層能處理混合格式
        errors = self.model.validate_manual_struct(mixed_members, 12)
        self.assertEqual(len(errors), 0)
        
        # 驗證型別轉換
        converted_members = self.model._convert_to_cpp_members(mixed_members)
        self.assertEqual(len(converted_members), 3)
        self.assertEqual(converted_members[0]["type"], "int")
        self.assertEqual(converted_members[1]["type"], "char")
        self.assertEqual(converted_members[2]["type"], "unsigned int")
        self.assertTrue(converted_members[2]["is_bitfield"])
    
    def test_remaining_space_calculation(self):
        """測試剩餘空間計算"""
        # 設定結構體
        self.view.struct_name_var.set("SpaceTest")
        self.view.size_var.set(8)  # 64 bits
        
        # 新增成員
        self.view._add_member()
        self.view.members[0]["name"] = "a"
        self.view.members[0]["type"] = "int"  # 32 bits
        self.view.members[0]["bit_size"] = 0
        
        self.view._add_member()
        self.view.members[1]["name"] = "b"
        self.view.members[1]["type"] = "unsigned int"
        self.view.members[1]["bit_size"] = 4  # 4 bits
        
        # 驗證剩餘空間計算
        struct_data = self.view.get_manual_struct_definition()
        used_bits = self.model.calculate_used_bits(struct_data["members"])
        expected_used = 32 + 4  # int + 4 bits
        self.assertEqual(used_bits, expected_used)
        
        remaining_bits = 64 - used_bits
        self.assertEqual(remaining_bits, 28)
    
    def test_member_operations(self):
        """測試成員操作（新增、刪除、移動、複製）"""
        # 設定結構體
        self.view.struct_name_var.set("OpTest")
        self.view.size_var.set(16)
        
        # 新增成員
        self.view._add_member()
        self.view.members[0]["name"] = "first"
        self.view.members[0]["type"] = "int"
        
        self.view._add_member()
        self.view.members[1]["name"] = "second"
        self.view.members[1]["type"] = "char"
        
        # 測試複製
        self.view._copy_member(0)
        self.assertEqual(len(self.view.members), 3)
        self.assertEqual(self.view.members[1]["name"], "first_copy")
        self.assertEqual(self.view.members[1]["type"], "int")
        
        # 測試移動
        self.view._move_member_up(1)  # 上移 first_copy
        self.assertEqual(self.view.members[0]["name"], "first_copy")
        self.assertEqual(self.view.members[1]["name"], "first")
        
        # 測試刪除
        self.view._delete_member(0)  # 刪除 first_copy
        self.assertEqual(len(self.view.members), 2)
        self.assertEqual(self.view.members[0]["name"], "first")
        self.assertEqual(self.view.members[1]["name"], "second")
    
    def test_validation_error_handling(self):
        """測試驗證錯誤處理"""
        # 設定結構體
        self.view.struct_name_var.set("ErrorTest")
        self.view.size_var.set(4)
        
        # 新增無效成員
        self.view._add_member()
        self.view.members[0]["name"] = "invalid"
        self.view.members[0]["type"] = "invalid_type"
        self.view.members[0]["bit_size"] = 0
        
        # 驗證錯誤處理
        struct_data = self.view.get_manual_struct_definition()
        errors = self.model.validate_manual_struct(struct_data["members"], struct_data["total_size"])
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("不支援的型別" in error for error in errors))
        
        # 測試 View 層錯誤顯示
        self.view.show_manual_struct_validation(errors)
        label_text = self.view.validation_label.cget("text")
        self.assertIn("不支援的型別", label_text)
    
    def test_layout_calculation_integration(self):
        """測試 layout 計算整合"""
        # 設定結構體
        self.view.struct_name_var.set("LayoutTest")
        self.view.size_var.set(8)
        
        # 新增成員
        self.view._add_member()
        self.view.members[0]["name"] = "a"
        self.view.members[0]["type"] = "int"
        self.view.members[0]["bit_size"] = 0
        
        self.view._add_member()
        self.view.members[1]["name"] = "b"
        self.view.members[1]["type"] = "unsigned int"
        self.view.members[1]["bit_size"] = 4
        
        # 觸發 layout 更新
        self.view._update_manual_layout_tree()
        
        # 檢查 Treeview 是否有資料
        tree_items = self.view.manual_layout_tree.get_children()
        self.assertGreater(len(tree_items), 0)
        
        # 檢查第一個項目
        first_item = self.view.manual_layout_tree.item(tree_items[0])
        values = first_item['values']
        self.assertEqual(values[0], "a")  # name
        self.assertEqual(values[1], "int")  # type

if __name__ == "__main__":
    unittest.main() 