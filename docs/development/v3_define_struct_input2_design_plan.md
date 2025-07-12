# V3 手動 Struct 輸入改進設計計劃

## 概述

本計劃旨在改進 MyStruct 功能的使用者介面，新增「type」欄位讓使用者明確指定成員型別，同時移除「byte_size」欄位以簡化介面並提高資料一致性。

## 改動目標

### 主要改進
1. **新增「type」欄位**：讓使用者明確指定 C++ 型別（int、char、float 等）
2. **移除「byte_size」欄位**：由型別自動決定大小，避免不一致性
3. **簡化使用者介面**：減少輸入欄位，提高易用性
4. **改善資料一致性**：型別與大小完全對應

### 預期效益
- 更直觀的型別選擇
- 避免型別與大小不一致的問題
- 減少使用者輸入錯誤
- 更符合 C++ 設計理念

## 目前架構分析

### 現有資料結構
```python
# 目前 member 格式
{
    "name": "user_id",
    "byte_size": 8,      # 將被移除
    "bit_size": 0
}
```

### 現有型別推斷邏輯
```python
def infer_type(byte_size, bit_size):
    if bit_size > 0:
        return {"type": "unsigned int", "is_bitfield": True}
    if byte_size == 1: return {"type": "char"}
    elif byte_size == 2: return {"type": "short"}
    elif byte_size == 4: return {"type": "int"}
    elif byte_size == 8: return {"type": "long long"}
```

### 支援的型別（TYPE_INFO）
```python
TYPE_INFO = {
    "char": {"size": 1, "align": 1},
    "signed char": {"size": 1, "align": 1},
    "unsigned char": {"size": 1, "align": 1},
    "bool": {"size": 1, "align": 1},
    "short": {"size": 2, "align": 2},
    "unsigned short": {"size": 2, "align": 2},
    "int": {"size": 4, "align": 4},
    "unsigned int": {"size": 4, "align": 4},
    "long": {"size": 8, "align": 8},
    "unsigned long": {"size": 8, "align": 8},
    "long long": {"size": 8, "align": 8},
    "unsigned long long": {"size": 8, "align": 8},
    "float": {"size": 4, "align": 4},
    "double": {"size": 8, "align": 8},
    "pointer": {"size": 8, "align": 8}
}
```

## 新架構設計

### 新的資料結構
```python
# 新的 member 格式
{
    "name": "user_id",
    "type": "unsigned long long",  # 明確指定型別
    "bit_size": 0                  # 只用於 bitfield
}
```

### 新的 GUI 表格設計
```
# | 成員名稱 | 型別 | bit size | 操作
```

### 型別選項分類
```python
# 普通型別選項
REGULAR_TYPE_OPTIONS = [
    "char", "unsigned char", "signed char",
    "short", "unsigned short",
    "int", "unsigned int",
    "long", "unsigned long",
    "long long", "unsigned long long",
    "float", "double", "bool"
]

# Bitfield 型別選項（限制）
BITFIELD_TYPE_OPTIONS = [
    "int", "unsigned int", "char", "unsigned char"
]
```

## 改動流程

### 階段 1：Model 層改動（核心邏輯）

#### 1.1 修改 StructModel 類別
**檔案：** `src/model/struct_model.py`

**改動內容：**
- 修改 `_convert_to_cpp_members()` 方法，支援明確型別
- 新增 `calculate_used_bits()` 方法，根據型別計算使用空間
- 修改 `validate_manual_struct()` 方法，移除 byte_size 驗證
- 修改 `export_manual_struct_to_h()` 方法，使用明確型別匯出

**關鍵方法：**
```python
def _convert_to_cpp_members(self, members):
    """將 type/bit 欄位轉換為 C++ 標準型別"""
    new_members = []
    for m in members:
        name = m.get("name", "")
        type_name = m.get("type", "")
        bit_size = m.get("bit_size", 0)
        
        if not type_name or type_name not in TYPE_INFO:
            continue
            
        if bit_size > 0:
            # bitfield
            new_members.append({
                "type": type_name,
                "name": name,
                "is_bitfield": True,
                "bit_size": bit_size
            })
        else:
            # 普通欄位
            new_members.append({
                "type": type_name,
                "name": name,
                "is_bitfield": False
            })
    
    return new_members

def calculate_used_bits(self, members):
    """根據 type 計算已使用的 bits"""
    used_bits = 0
    for m in members:
        type_name = m.get("type", "")
        bit_size = m.get("bit_size", 0)
        
        if type_name in TYPE_INFO:
            if bit_size > 0:
                # bitfield：使用實際 bit 數
                used_bits += bit_size
            else:
                # 普通欄位：使用 type 的 byte size * 8
                used_bits += TYPE_INFO[type_name]["size"] * 8
    
    return used_bits
```

#### 1.2 向後相容性處理
**檔案：** `src/model/struct_model.py`

**改動內容：**
- 新增 `_convert_legacy_member()` 方法，支援舊格式
- 在 `_convert_to_cpp_members()` 中檢查並轉換舊格式

```python
def _convert_legacy_member(self, member):
    """支援舊格式的 member（包含 byte_size）"""
    if "byte_size" in member and "type" not in member:
        # 舊格式：根據 byte_size 推斷型別
        byte_size = member.get("byte_size", 0)
        bit_size = member.get("bit_size", 0)
        
        if bit_size > 0:
            return "unsigned int"  # bitfield 預設型別
        elif byte_size == 1:
            return "char"
        elif byte_size == 2:
            return "short"
        elif byte_size == 4:
            return "int"
        elif byte_size == 8:
            return "long long"
        else:
            return "unsigned char"  # 其他大小
    
    return member.get("type", "")
```

### 階段 2：View 層改動（使用者介面）

#### 2.1 修改 GUI 表格設計
**檔案：** `src/view/struct_view.py`

**改動內容：**
- 修改 `_render_member_table()` 方法，移除 byte_size 欄位
- 新增型別下拉選單
- 修改表頭：`# | 成員名稱 | 型別 | bit size | 操作`

**關鍵改動：**
```python
def _render_member_table(self):
    # 清空現有表格
    for widget in self.member_frame.winfo_children():
        widget.destroy()
    
    if self.members:
        # 新的表頭
        tk.Label(self.member_frame, text="#", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=2, pady=2)
        tk.Label(self.member_frame, text="成員名稱", font=("Arial", 9, "bold")).grid(row=0, column=1, padx=2, pady=2)
        tk.Label(self.member_frame, text="型別", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=2, pady=2)
        tk.Label(self.member_frame, text="bit size", font=("Arial", 9, "bold")).grid(row=0, column=3, padx=2, pady=2)
        tk.Label(self.member_frame, text="操作", font=("Arial", 9, "bold")).grid(row=0, column=4, padx=2, pady=2)
        
        for idx, m in enumerate(self.members):
            row = idx + 1
            tk.Label(self.member_frame, text=str(idx+1)).grid(row=row, column=0, padx=2, pady=1)
            
            # 成員名稱輸入
            name_var = tk.StringVar(value=m.get("name", ""))
            tk.Entry(self.member_frame, textvariable=name_var, width=10).grid(row=row, column=1, padx=2, pady=1)
            
            # 型別下拉選單
            type_var = tk.StringVar(value=m.get("type", ""))
            type_options = self._get_type_options(m.get("bit_size", 0) > 0)
            type_menu = tk.OptionMenu(self.member_frame, type_var, *type_options)
            type_menu.grid(row=row, column=2, padx=2, pady=1)
            
            # bit size 輸入
            bit_var = tk.IntVar(value=m.get("bit_size", 0))
            tk.Entry(self.member_frame, textvariable=bit_var, width=6).grid(row=row, column=3, padx=2, pady=1)
            
            # 操作按鈕
            op_frame = tk.Frame(self.member_frame)
            op_frame.grid(row=row, column=4, padx=2, pady=1)
            tk.Button(op_frame, text="刪除", command=lambda i=idx: self._delete_member(i), width=4).pack(side=tk.LEFT, padx=1)
            tk.Button(op_frame, text="上移", command=lambda i=idx: self._move_member_up(i), width=4).pack(side=tk.LEFT, padx=1)
            tk.Button(op_frame, text="下移", command=lambda i=idx: self._move_member_down(i), width=4).pack(side=tk.LEFT, padx=1)
            tk.Button(op_frame, text="複製", command=lambda i=idx: self._copy_member(i), width=4).pack(side=tk.LEFT, padx=1)
            
            # 綁定變更事件
            name_var.trace_add("write", lambda *_, i=idx, v=name_var: self._update_member_name(i, v))
            type_var.trace_add("write", lambda *_, i=idx, v=type_var: self._update_member_type(i, v))
            bit_var.trace_add("write", lambda *_, i=idx, v=bit_var: self._update_member_bit(i, v))
            
            # 儲存變數參考
            m["name_var"] = name_var
            m["type_var"] = type_var
            m["bit_var"] = bit_var
```

#### 2.2 新增型別選項方法
**檔案：** `src/view/struct_view.py`

**改動內容：**
- 新增 `_get_type_options()` 方法，根據是否為 bitfield 提供不同選項
- 新增 `_update_member_type()` 方法，處理型別變更

```python
def _get_type_options(self, is_bitfield=False):
    """根據是否為 bitfield 返回型別選項"""
    if is_bitfield:
        return ["int", "unsigned int", "char", "unsigned char"]
    else:
        return [
            "char", "unsigned char", "signed char",
            "short", "unsigned short",
            "int", "unsigned int",
            "long", "unsigned long",
            "long long", "unsigned long long",
            "float", "double", "bool"
        ]

def _update_member_type(self, idx, var):
    """處理型別變更"""
    self.members[idx]["type"] = var.get()
    self._on_manual_struct_change()
```

#### 2.3 修改剩餘空間計算
**檔案：** `src/view/struct_view.py`

**改動內容：**
- 修改 `show_manual_struct_validation()` 方法，使用 Model 的新計算方法
- 移除 byte_size 相關的計算邏輯

```python
def show_manual_struct_validation(self, errors):
    if errors:
        self.validation_label.config(text="; ".join(errors), fg="red")
    else:
        # 根據 type 計算剩餘空間
        struct_data = self.get_manual_struct_definition()
        total_bits = struct_data["total_size"] * 8
        
        # 使用 Model 的計算方法
        model = StructModel()
        used_bits = model.calculate_used_bits(struct_data["members"])
        
        remaining_bits = max(0, total_bits - used_bits)
        remaining_bytes = remaining_bits // 8
        msg = "設定正確"
        msg += f"（剩餘可用空間：{remaining_bits} bits（{remaining_bytes} bytes））"
        self.validation_label.config(text=msg, fg="green")
```

#### 2.4 修改資料結構方法
**檔案：** `src/view/struct_view.py`

**改動內容：**
- 修改 `get_manual_struct_definition()` 方法，移除 byte_size
- 修改 `_add_member()` 方法，新增預設型別
- 修改 `_copy_member()` 方法，複製型別資訊

```python
def get_manual_struct_definition(self):
    return {
        "struct_name": self.struct_name_var.get(),
        "total_size": self.size_var.get(),
        "members": [
            {"name": m["name"], "type": m["type"], "bit_size": m["bit_size"]}
            for m in self.members
        ]
    }

def _add_member(self):
    self.members.append({"name": "", "type": "int", "bit_size": 0})
    self._render_member_table()
    self._on_manual_struct_change()

def _copy_member(self, idx):
    orig = self.members[idx]
    base_name = orig["name"]
    new_name = base_name + "_copy"
    existing_names = {m["name"] for m in self.members}
    count = 2
    while new_name in existing_names:
        new_name = f"{base_name}_copy{count}"
        count += 1
    new_m = {"name": new_name, "type": orig["type"], "bit_size": orig["bit_size"]}
    self.members.insert(idx+1, new_m)
    self._render_member_table()
    self._on_manual_struct_change()
```

### 階段 3：測試與驗證

#### 3.1 新增 Model 測試
**檔案：** `tests/test_struct_model_v3.py`

**測試內容：**
- 新的 `_convert_to_cpp_members()` 方法測試
- `calculate_used_bits()` 方法測試
- 型別驗證測試
- 向後相容性測試

```python
class TestStructModelV3(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()
    
    def test_convert_to_cpp_members_with_type(self):
        """測試新的型別轉換方法"""
        members = [
            {"name": "a", "type": "int", "bit_size": 0},
            {"name": "b", "type": "unsigned int", "bit_size": 4}
        ]
        result = self.model._convert_to_cpp_members(members)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "int")
        self.assertEqual(result[1]["type"], "unsigned int")
        self.assertTrue(result[1]["is_bitfield"])
    
    def test_calculate_used_bits(self):
        """測試使用空間計算"""
        members = [
            {"name": "a", "type": "int", "bit_size": 0},      # 4 bytes = 32 bits
            {"name": "b", "type": "unsigned int", "bit_size": 4}  # 4 bits
        ]
        used_bits = self.model.calculate_used_bits(members)
        self.assertEqual(used_bits, 36)  # 32 + 4
    
    def test_backward_compatibility(self):
        """測試向後相容性"""
        members = [
            {"name": "a", "byte_size": 4, "bit_size": 0},  # 舊格式
            {"name": "b", "type": "int", "bit_size": 0}    # 新格式
        ]
        result = self.model._convert_to_cpp_members(members)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "int")
        self.assertEqual(result[1]["type"], "int")
```

#### 3.2 新增 GUI 測試
**檔案：** `tests/test_struct_view_v3.py`

**測試內容：**
- 新的表格欄位測試
- 型別下拉選單測試
- 剩餘空間計算測試
- 資料結構變更測試

```python
class TestStructViewV3(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.view = StructView()
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
    
    def test_type_dropdown_options(self):
        """測試型別下拉選單選項"""
        # 測試普通型別選項
        regular_options = self.view._get_type_options(is_bitfield=False)
        self.assertIn("int", regular_options)
        self.assertIn("float", regular_options)
        
        # 測試 bitfield 型別選項
        bitfield_options = self.view._get_type_options(is_bitfield=True)
        self.assertIn("int", bitfield_options)
        self.assertNotIn("float", bitfield_options)
```

#### 3.3 整合測試
**檔案：** `tests/test_manual_struct_v3_integration.py`

**測試內容：**
- 完整的 MyStruct 工作流程測試
- 型別選擇到匯出的端到端測試
- 錯誤處理和驗證測試

### 階段 4：文件更新

#### 4.1 更新架構文件
**檔案：** `docs/architecture/MANUAL_STRUCT_ALIGNMENT.md`

**更新內容：**
- 新增型別選擇的說明
- 更新資料結構格式
- 新增 GUI 介面說明

#### 4.2 更新 README 文件
**檔案：** `README.md`

**更新內容：**
- 更新手動 struct 定義的說明
- 新增型別選擇功能描述
- 更新使用範例

#### 4.3 更新測試文件
**檔案：** `tests/README.md`

**更新內容：**
- 新增 V3 測試說明
- 更新測試覆蓋範圍
- 新增向後相容性測試說明

## 注意事項與風險控制

### 1. 向後相容性
**風險：** 現有的 byte_size 格式可能無法正常運作
**解決方案：**
- 實作 `_convert_legacy_member()` 方法
- 在 `_convert_to_cpp_members()` 中檢查並轉換舊格式
- 保留舊格式的驗證邏輯

### 2. 型別驗證
**風險：** 使用者可能選擇不支援的型別
**解決方案：**
- 限制下拉選單選項
- 實作型別驗證邏輯
- 提供清晰的錯誤訊息

### 3. Bitfield 型別限制
**風險：** Bitfield 只能使用特定型別
**解決方案：**
- 根據 bit_size 動態調整型別選項
- 實作 bitfield 型別驗證
- 提供型別建議功能

### 4. 剩餘空間計算
**風險：** 新的計算方法可能與舊邏輯不一致
**解決方案：**
- 實作新的 `calculate_used_bits()` 方法
- 確保計算結果與舊方法一致
- 新增計算方法的測試

### 5. GUI 變更
**風險：** 使用者介面變更可能影響使用習慣
**解決方案：**
- 保持操作邏輯一致
- 提供清晰的視覺回饋
- 實作型別建議功能

### 6. 測試覆蓋
**風險：** 新功能可能缺乏足夠測試
**解決方案：**
- 新增完整的單元測試
- 實作整合測試
- 測試向後相容性

## 實作時程

### 第一週：Model 層改動
- 修改 `StructModel` 類別
- 實作新的型別轉換邏輯
- 新增向後相容性支援
- 完成 Model 層測試

### 第二週：View 層改動
- 修改 GUI 表格設計
- 實作型別下拉選單
- 更新剩餘空間計算
- 完成 View 層測試

### 第三週：測試與驗證
- 完成整合測試
- 驗證向後相容性
- 測試錯誤處理
- 效能測試

### 第四週：文件更新與發布
- 更新所有相關文件
- 更新使用範例
- 準備發布說明
- 最終驗證

## 成功標準

### 功能標準
- [ ] 使用者可以明確選擇 C++ 型別
- [ ] 型別與大小完全對應
- [ ] 支援所有 TYPE_INFO 中的型別
- [ ] Bitfield 型別限制正確實作

### 相容性標準
- [ ] 向後相容舊格式
- [ ] 現有功能正常運作
- [ ] 匯出功能正確

### 品質標準
- [ ] 所有測試通過
- [ ] 無迴歸錯誤
- [ ] 文件完整更新
- [ ] 使用者介面直觀易用

## 結論

V3 手動 Struct 輸入改進將大幅提升 MyStruct 功能的易用性和準確性。透過新增型別選擇和移除 byte_size 欄位，我們將提供更直觀、更一致的介面，同時保持向後相容性。

這個改進將讓使用者能夠：
- 明確指定 C++ 型別，避免自動推斷的侷限
- 享受更簡潔的使用者介面
- 獲得更好的型別控制和驗證
- 保持與現有功能的相容性 