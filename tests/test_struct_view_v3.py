import unittest
import sys
import os
import tkinter as tk

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.view.struct_view import StructView

class TestStructViewV3(unittest.TestCase):
    """測試 V3 版本的 StructView 新功能"""
    
    def setUp(self):
        self.root = tk.Tk()
        self.view = StructView()
        # 切換到手動 struct tab
        self.view.tab_control.select(self.view.tab_manual)
    
    def tearDown(self):
        self.root.destroy()
    
    def test_new_table_columns(self):
        """測試新的表格欄位"""
        self.view.members = [{"name": "test", "type": "int", "bit_size": 0}]
        self.view._render_member_table()
        
        # 檢查表頭
        children = self.view.member_frame.winfo_children()
        header_labels = [child.cget("text") for child in children if isinstance(child, tk.Label)]
        expected_headers = ["#", "成員名稱", "型別", "bit size", "操作"]
        
        for expected in expected_headers:
            self.assertIn(expected, header_labels)
    
    def test_type_dropdown_options_regular(self):
        """測試普通型別下拉選單選項"""
        regular_options = self.view._get_type_options(is_bitfield=False)
        expected_types = [
            "char", "unsigned char", "signed char",
            "short", "unsigned short",
            "int", "unsigned int",
            "long", "unsigned long",
            "long long", "unsigned long long",
            "float", "double", "bool"
        ]
        
        for expected_type in expected_types:
            self.assertIn(expected_type, regular_options)
    
    def test_type_dropdown_options_bitfield(self):
        """測試 bitfield 型別下拉選單選項"""
        bitfield_options = self.view._get_type_options(is_bitfield=True)
        expected_types = ["int", "unsigned int", "char", "unsigned char"]
        
        for expected_type in expected_types:
            self.assertIn(expected_type, bitfield_options)
        
        # 確認不包含不支援的型別
        unsupported_types = ["float", "double", "long"]
        for unsupported_type in unsupported_types:
            self.assertNotIn(unsupported_type, bitfield_options)
    
    def test_get_manual_struct_definition_v3_format(self):
        """測試 V3 格式的資料結構取得"""
        self.view.members = [
            {"name": "user_id", "type": "unsigned long long", "bit_size": 0},
            {"name": "status", "type": "unsigned int", "bit_size": 4}
        ]
        self.view.struct_name_var.set("TestStruct")
        self.view.size_var.set(16)
        
        result = self.view.get_manual_struct_definition()
        
        self.assertEqual(result["struct_name"], "TestStruct")
        self.assertEqual(result["total_size"], 16)
        self.assertEqual(len(result["members"]), 2)
        self.assertEqual(result["members"][0]["name"], "user_id")
        self.assertEqual(result["members"][0]["type"], "unsigned long long")
        self.assertEqual(result["members"][0]["bit_size"], 0)
        self.assertEqual(result["members"][1]["name"], "status")
        self.assertEqual(result["members"][1]["type"], "unsigned int")
        self.assertEqual(result["members"][1]["bit_size"], 4)
    
    def test_add_member_v3_format(self):
        """測試新增成員（V3 格式）"""
        initial_count = len(self.view.members)
        self.view._add_member()
        
        self.assertEqual(len(self.view.members), initial_count + 1)
        new_member = self.view.members[-1]
        self.assertEqual(new_member["name"], "")
        self.assertEqual(new_member["type"], "int")  # 預設型別
        self.assertEqual(new_member["bit_size"], 0)
    
    def test_copy_member_v3_format(self):
        """測試複製成員（V3 格式）"""
        self.view.members = [
            {"name": "original", "type": "unsigned int", "bit_size": 4}
        ]
        initial_count = len(self.view.members)
        
        self.view._copy_member(0)
        
        self.assertEqual(len(self.view.members), initial_count + 1)
        copied_member = self.view.members[1]  # 插入在原始成員後面
        self.assertEqual(copied_member["name"], "original_copy")
        self.assertEqual(copied_member["type"], "unsigned int")
        self.assertEqual(copied_member["bit_size"], 4)
    
    def test_copy_member_duplicate_name_handling(self):
        """測試複製成員時重複名稱處理"""
        self.view.members = [
            {"name": "test", "type": "int", "bit_size": 0},
            {"name": "test_copy", "type": "char", "bit_size": 0}
        ]
        
        self.view._copy_member(0)
        
        # 應該產生 test_copy2，插入在原始成員後面（索引 1）
        copied_member = self.view.members[1]
        self.assertEqual(copied_member["name"], "test_copy2")
    
    def test_update_member_type(self):
        """測試更新成員型別"""
        self.view.members = [
            {"name": "test", "type": "int", "bit_size": 0}
        ]
        
        # 模擬型別變更
        self.view._update_member_type(0, tk.StringVar(value="unsigned long"))
        
        self.assertEqual(self.view.members[0]["type"], "unsigned long")
    
    def test_update_member_bit_size(self):
        """測試更新成員 bit_size"""
        self.view.members = [
            {"name": "test", "type": "unsigned int", "bit_size": 0}
        ]
        
        # 模擬 bit_size 變更
        self.view._update_member_bit(0, tk.IntVar(value=8))
        
        self.assertEqual(self.view.members[0]["bit_size"], 8)
    
    def test_update_member_name(self):
        """測試更新成員名稱"""
        self.view.members = [
            {"name": "old_name", "type": "int", "bit_size": 0}
        ]
        
        # 模擬名稱變更
        self.view._update_member_name(0, tk.StringVar(value="new_name"))
        
        self.assertEqual(self.view.members[0]["name"], "new_name")
    
    def test_show_manual_struct_validation_v3_format(self):
        """測試 V3 格式的驗證顯示"""
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},      # 4 bytes = 32 bits
            {"name": "b", "type": "unsigned int", "bit_size": 4}  # 4 bits
        ]
        self.view.size_var.set(8)  # 8 bytes = 64 bits
        
        # 模擬驗證
        self.view.show_manual_struct_validation([])
        
        # 檢查驗證標籤內容
        label_text = self.view.validation_label.cget("text")
        self.assertIn("設定正確", label_text)
        self.assertIn("剩餘可用空間", label_text)
        self.assertIn("28 bits", label_text)  # 64 - 32 - 4 = 28 bits
    
    def test_show_manual_struct_validation_with_errors(self):
        """測試有錯誤時的驗證顯示"""
        errors = ["成員名稱 'test' 重複", "不支援的型別: invalid_type"]
        
        self.view.show_manual_struct_validation(errors)
        
        label_text = self.view.validation_label.cget("text")
        self.assertIn("成員名稱 'test' 重複", label_text)
        self.assertIn("不支援的型別: invalid_type", label_text)
    
    def test_render_member_table_with_v3_data(self):
        """測試使用 V3 資料渲染表格"""
        self.view.members = [
            {"name": "user_id", "type": "unsigned long long", "bit_size": 0},
            {"name": "status", "type": "unsigned int", "bit_size": 4},
            {"name": "name", "type": "char", "bit_size": 0}
        ]
        
        self.view._render_member_table()
        
        # 檢查表格是否正確渲染
        children = self.view.member_frame.winfo_children()
        self.assertGreater(len(children), 0)
        
        # 檢查是否有正確數量的輸入欄位
        entry_widgets = [child for child in children if isinstance(child, tk.Entry)]
        self.assertGreaterEqual(len(entry_widgets), 3)  # 至少 3 個成員的輸入欄位
    
    def test_delete_member(self):
        """測試刪除成員"""
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0},
            {"name": "c", "type": "float", "bit_size": 0}
        ]
        initial_count = len(self.view.members)
        
        self.view._delete_member(1)  # 刪除第二個成員
        
        self.assertEqual(len(self.view.members), initial_count - 1)
        self.assertEqual(self.view.members[0]["name"], "a")
        self.assertEqual(self.view.members[1]["name"], "c")  # 原本的第三個成員
    
    def test_move_member_up(self):
        """測試上移成員"""
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0},
            {"name": "c", "type": "float", "bit_size": 0}
        ]
        
        self.view._move_member_up(1)  # 上移第二個成員
        
        self.assertEqual(self.view.members[0]["name"], "b")
        self.assertEqual(self.view.members[1]["name"], "a")
        self.assertEqual(self.view.members[2]["name"], "c")
    
    def test_move_member_down(self):
        """測試下移成員"""
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0},
            {"name": "c", "type": "float", "bit_size": 0}
        ]
        
        self.view._move_member_down(0)  # 下移第一個成員
        
        self.assertEqual(self.view.members[0]["name"], "b")
        self.assertEqual(self.view.members[1]["name"], "a")
        self.assertEqual(self.view.members[2]["name"], "c")
    
    def test_move_member_up_at_top(self):
        """測試在頂部上移成員（應該無效）"""
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0}
        ]
        
        self.view._move_member_up(0)  # 上移第一個成員
        
        # 應該沒有變化
        self.assertEqual(self.view.members[0]["name"], "a")
        self.assertEqual(self.view.members[1]["name"], "b")
    
    def test_move_member_down_at_bottom(self):
        """測試在底部下移成員（應該無效）"""
        self.view.members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "char", "bit_size": 0}
        ]
        
        self.view._move_member_down(1)  # 下移最後一個成員
        
        # 應該沒有變化
        self.assertEqual(self.view.members[0]["name"], "a")
        self.assertEqual(self.view.members[1]["name"], "b")

if __name__ == "__main__":
    unittest.main() 