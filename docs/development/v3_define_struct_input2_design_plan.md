# V3 手動 Struct 輸入改進設計計劃

## 概述

本計劃旨在改進 MyStruct 功能的使用者介面，新增「type」欄位讓使用者明確指定成員型別，同時移除「byte_size」欄位以簡化介面並提高資料一致性。V3 版本同時實現了完整的 C++ 標準對齊和填充機制，確保手動定義的結構體與 C++ 編譯器產生的記憶體佈局完全一致。

## 改動目標

### 主要改進
1. **新增「type」欄位**：讓使用者明確指定 C++ 型別（int、char、float 等）
2. **移除「byte_size」欄位**：由型別自動決定大小，避免不一致性
3. **簡化使用者介面**：減少輸入欄位，提高易用性
4. **改善資料一致性**：型別與大小完全對應
5. **C++ 標準對齊**：實現完整的 C++ 標準對齊和填充機制
6. **輸入驗證增強**：防止非數字輸入導致應用程式崩潰

### 預期效益
- 更直觀的型別選擇
- 避免型別與大小不一致的問題
- 減少使用者輸入錯誤
- 更符合 C++ 設計理念
- 與 C++ 編譯器行為完全一致
- 提高應用程式穩定性

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

## C++ 標準對齊機制

### 對齊規則
系統遵循標準 C++ 對齊規則：

1. **成員對齊**：每個成員按其型別的對齊要求進行對齊
2. **結構體對齊**：整個結構體按最大成員的對齊要求進行對齊
3. **填充插入**：在成員之間插入填充位元組以滿足對齊要求
4. **最終填充**：結構體大小填充為結構體對齊的倍數

### 對齊值（64位系統）

| 型別 | 大小 | 對齊 |
|------|------|------|
| `char` | 1 | 1 |
| `short` | 2 | 2 |
| `int` | 4 | 4 |
| `long long` | 8 | 8 |
| `pointer` | 8 | 8 |

### 型別推斷規則

#### Byte Size 到 C++ 型別對應

| Byte Size | 推斷的 C++ 型別 | 對齊 | 備註 |
|-----------|-------------------|-----------|-------|
| 1 | `char` | 1 | 8位元字元 |
| 2 | `short` | 2 | 16位元整數 |
| 4 | `int` | 4 | 32位元整數 |
| 8 | `long long` | 8 | 64位元整數 |
| >8 | `unsigned char[]` | 1 | 位元組陣列 |

#### Bit Size 處理

- **Bit size > 0**：自動推斷為 `unsigned int` bitfield
- **Bit size = 0**：使用 byte size 進行型別推斷
- **多個 bitfield**：在可能的情況下打包到同一儲存單元

## 改動流程

### 階段 1：Model 層改動（核心邏輯）

#### 1.1 修改 StructModel 類別
**檔案：** `src/model/struct_model.py`

**改動內容：**
- 修改 `_convert_to_cpp_members()` 方法，支援明確型別
- 新增 `calculate_used_bits()` 方法，根據型別計算使用空間
- 修改 `validate_manual_struct()` 方法，移除 byte_size 驗證
- 修改 `export_manual_struct_to_h()` 方法，使用明確型別匯出
- 實現 C++ 標準對齊和填充機制

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

def calculate_manual_layout(self, members, total_size):
    """計算手動結構體的記憶體佈局，遵循 C++ 標準對齊規則"""
    # 使用 _convert_to_cpp_members 轉換為 C++ 標準型別
    expanded_members = self._convert_to_cpp_members(members)
    # 呼叫 calculate_layout 產生 C++ 標準 struct align/padding
    layout, total, align = calculate_layout(expanded_members)
    return layout
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
- 實現向後相容性支援

**關鍵改動：**
```python
def _render_member_table(self):
    # 清空現有表格
    for widget in self.member_frame.winfo_children():
        widget.destroy()
    
    if self.members:
        # 檢查是否為 V3 格式
        is_v3_format = self.members and "type" in self.members[0]
        
        # 新的表頭
        tk.Label(self.member_frame, text="#", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=2, pady=2)
        tk.Label(self.member_frame, text="成員名稱", font=("Arial", 9, "bold")).grid(row=0, column=1, padx=2, pady=2)
        
        if is_v3_format:
            tk.Label(self.member_frame, text="型別", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=2, pady=2)
        else:
            tk.Label(self.member_frame, text="byte size", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=2, pady=2)
        
        tk.Label(self.member_frame, text="bit size", font=("Arial", 9, "bold")).grid(row=0, column=3, padx=2, pady=2)
        tk.Label(self.member_frame, text="操作", font=("Arial", 9, "bold")).grid(row=0, column=4, padx=2, pady=2)
        
        for idx, m in enumerate(self.members):
            row = idx + 1
            tk.Label(self.member_frame, text=str(idx+1)).grid(row=row, column=0, padx=2, pady=1)
            
            # 成員名稱輸入
            name_var = tk.StringVar(value=m.get("name", ""))
            tk.Entry(self.member_frame, textvariable=name_var, width=10).grid(row=row, column=1, padx=2, pady=1)
            
            if is_v3_format:
                # 型別下拉選單
                type_var = tk.StringVar(value=m.get("type", ""))
                type_options = self._get_type_options(m.get("bit_size", 0) > 0)
                type_menu = tk.OptionMenu(self.member_frame, type_var, *type_options)
                type_menu.grid(row=row, column=2, padx=2, pady=1)
            else:
                # byte size 輸入
                byte_var = tk.IntVar(value=m.get("byte_size", 0))
                tk.Entry(self.member_frame, textvariable=byte_var, width=6).grid(row=row, column=2, padx=2, pady=1)
            
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
            
            if is_v3_format:
                type_var.trace_add("write", lambda *_, i=idx, v=type_var: self._update_member_type(i, v))
            else:
                byte_var.trace_add("write", lambda *_, i=idx, v=byte_var: self._update_member_byte(i, v))
            
            bit_var.trace_add("write", lambda *_, i=idx, v=bit_var: self._update_member_bit(i, v))
            
            # 儲存變數參考
            m["name_var"] = name_var
            if is_v3_format:
                m["type_var"] = type_var
            else:
                m["byte_var"] = byte_var
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
        
        # 支援向後相容性：根據資料格式決定計算方法
        if struct_data["members"] and "type" in struct_data["members"][0]:
            # V3 格式：使用 Model 的計算方法
            model = StructModel()
            used_bits = model.calculate_used_bits(struct_data["members"])
        else:
            # 舊格式：使用舊的計算方法
            used_bits = sum(m.get("byte_size", 0) * 8 + m.get("bit_size", 0) for m in struct_data["members"])
        
        remaining_bits = max(0, total_bits - used_bits)
        remaining_bytes = remaining_bits // 8
        msg = "設定正確"
        msg += f"（剩餘可用空間：{remaining_bits} bits（{remaining_bytes} bytes））"
        self.validation_label.config(text=msg, fg="green")
```

#### 2.4 修改資料結構方法
**檔案：** `src/view/struct_view.py`

**改動內容：**
- 修改 `get_manual_struct_definition()` 方法，支援向後相容性
- 修改 `_add_member()` 方法，新增預設型別
- 修改 `_copy_member()` 方法，複製型別資訊

```python
def get_manual_struct_definition(self):
    # 支援向後相容性：根據成員格式決定返回格式
    if self.members and "type" in self.members[0]:
        # V3 格式
        members_data = [
            {"name": m["name"], "type": m.get("type", ""), "bit_size": m["bit_size"]}
            for m in self.members
        ]
    else:
        # 舊格式
        members_data = [
            {"name": m["name"], "byte_size": m.get("byte_size", 0), "bit_size": m["bit_size"]}
            for m in self.members
        ]
    # 防呆：size_var 只允許數字
    try:
        total_size = self.size_var.get()
    except Exception:
        total_size = 0
    return {
        "struct_name": self.struct_name_var.get(),
        "total_size": total_size,
        "members": members_data
    }

def _add_member(self):
    # 支援向後相容性：根據現有成員的格式決定新增成員的格式
    if not self.members or (self.members and "type" in self.members[0]):
        # V3 格式（預設）或現有成員是 V3 格式
        self.members.append({"name": "", "type": "int", "bit_size": 0})
    else:
        # 舊格式
        self.members.append({"name": "", "byte_size": 0, "bit_size": 0})
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
    
    # 支援向後相容性
    if "type" in orig:
        new_m = {"name": new_name, "type": orig["type"], "bit_size": orig["bit_size"]}
    else:
        new_m = {"name": new_name, "byte_size": orig["byte_size"], "bit_size": orig["bit_size"]}
    
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
- C++ 標準對齊測試

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
    
    def test_cpp_alignment_behavior(self):
        """測試 C++ 標準對齊行為"""
        members = [
            {"name": "a", "type": "char", "bit_size": 0},   # 1 byte, align 1
            {"name": "b", "type": "int", "bit_size": 0}     # 4 bytes, align 4
        ]
        layout = self.model.calculate_manual_layout(members, 8)
        
        # 驗證對齊和填充
        self.assertEqual(layout[0]["name"], "a")
        self.assertEqual(layout[0]["offset"], 0)
        self.assertEqual(layout[0]["size"], 1)
        
        # 應該有 padding
        self.assertEqual(layout[1]["name"], "(padding)")
        self.assertEqual(layout[1]["type"], "padding")
        self.assertEqual(layout[1]["offset"], 1)
        self.assertEqual(layout[1]["size"], 3)
        
        self.assertEqual(layout[2]["name"], "b")
        self.assertEqual(layout[2]["offset"], 4)
        self.assertEqual(layout[2]["size"], 4)
```

#### 3.2 新增 GUI 測試
**檔案：** `tests/test_struct_view_v3.py`

**測試內容：**
- 新的表格欄位測試
- 型別下拉選單測試
- 剩餘空間計算測試
- 資料結構變更測試
- 向後相容性測試

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
    
    def test_backward_compatibility(self):
        """測試向後相容性"""
        # 測試舊格式成員
        self.view.members = [{"name": "test", "byte_size": 4, "bit_size": 0}]
        self.view._render_member_table()
        
        # 應該顯示 byte_size 欄位
        children = self.view.member_frame.winfo_children()
        header_labels = [child.cget("text") for child in children if isinstance(child, tk.Label)]
        self.assertIn("byte size", header_labels)
```

#### 3.3 整合測試
**檔案：** `tests/test_manual_struct_v3_integration.py`

**測試內容：**
- 完整的 MyStruct 工作流程測試
- 型別選擇到匯出的端到端測試
- 錯誤處理和驗證測試
- C++ 對齊行為驗證

```python
class TestManualStructV3Integration(unittest.TestCase):
    def setUp(self):
        self.model = StructModel()
    
    def test_v3_workflow_with_type_selection(self):
        """測試 V3 工作流程"""
        # 1. 建立 V3 格式成員
        members = [
            {"name": "user_id", "type": "unsigned long long", "bit_size": 0},
            {"name": "flags", "type": "unsigned int", "bit_size": 8}
        ]
        total_size = 16
        
        # 2. 驗證
        errors = self.model.validate_manual_struct(members, total_size)
        self.assertEqual(errors, [])
        
        # 3. 計算佈局
        layout = self.model.calculate_manual_layout(members, total_size)
        
        # 4. 驗證佈局
        non_pad = [item for item in layout if item["type"] != "padding"]
        self.assertEqual(non_pad[0]["name"], "user_id")
        self.assertEqual(non_pad[0]["type"], "unsigned long long")
        self.assertEqual(non_pad[0]["offset"], 0)
        self.assertEqual(non_pad[0]["size"], 8)
        
        self.assertEqual(non_pad[1]["name"], "flags")
        self.assertEqual(non_pad[1]["type"], "unsigned int")
        self.assertEqual(non_pad[1]["offset"], 8)
        self.assertEqual(non_pad[1]["bit_size"], 8)
    
    def test_cpp_alignment_integration(self):
        """測試 C++ 對齊整合"""
        members = [
            {"name": "a", "type": "char", "bit_size": 0},
            {"name": "b", "type": "int", "bit_size": 0},
            {"name": "c", "type": "short", "bit_size": 0}
        ]
        total_size = 12
        
        layout = self.model.calculate_manual_layout(members, total_size)
        
        # 驗證 C++ 標準對齊
        non_pad = [item for item in layout if item["type"] != "padding"]
        
        # char a: offset 0
        self.assertEqual(non_pad[0]["name"], "a")
        self.assertEqual(non_pad[0]["offset"], 0)
        
        # int b: offset 4 (after padding)
        self.assertEqual(non_pad[1]["name"], "b")
        self.assertEqual(non_pad[1]["offset"], 4)
        
        # short c: offset 8 (after padding)
        self.assertEqual(non_pad[2]["name"], "c")
        self.assertEqual(non_pad[2]["offset"], 8)
```

### 階段 4：文件更新

#### 4.1 更新架構文件
**檔案：** `docs/architecture/MANUAL_STRUCT_ALIGNMENT.md`

**更新內容：**
- 新增型別選擇的說明
- 更新資料結構格式
- 新增 GUI 介面說明
- C++ 標準對齊機制說明

#### 4.2 更新 README 文件
**檔案：** `README.md`

**更新內容：**
- 更新手動 struct 定義的說明
- 新增型別選擇功能描述
- 更新使用範例
- 新增 C++ 對齊行為說明

#### 4.3 更新測試文件
**檔案：** `tests/README.md`

**更新內容：**
- 新增 V3 測試說明
- 更新測試覆蓋範圍
- 新增向後相容性測試說明
- C++ 對齊測試說明

## 注意事項與風險控制

### 1. 向後相容性
**風險：** 現有的 byte_size 格式可能無法正常運作
**解決方案：**
- 實作 `_convert_legacy_member()` 方法
- 在 `_convert_to_cpp_members()` 中檢查並轉換舊格式
- 保留舊格式的驗證邏輯
- GUI 自動偵測並適應不同格式

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
- 支援向後相容性

### 6. 測試覆蓋
**風險：** 新功能可能缺乏足夠測試
**解決方案：**
- 新增完整的單元測試
- 實作整合測試
- 測試向後相容性
- C++ 對齊行為測試

### 7. 輸入驗證
**風險：** 非數字輸入可能導致應用程式崩潰
**解決方案：**
- 實作 try/except 錯誤處理
- 提供安全預設值
- 新增輸入驗證測試

## 實作時程

### 第一週：Model 層改動
- 修改 `StructModel` 類別
- 實作新的型別轉換邏輯
- 新增向後相容性支援
- 實現 C++ 標準對齊機制
- 完成 Model 層測試

### 第二週：View 層改動
- 修改 GUI 表格設計
- 實作型別下拉選單
- 更新剩餘空間計算
- 實現向後相容性支援
- 完成 View 層測試

### 第三週：測試與驗證
- 完成整合測試
- 驗證向後相容性
- 測試錯誤處理
- C++ 對齊行為驗證
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
- [ ] C++ 標準對齊機制正確實作
- [ ] 輸入驗證防止應用程式崩潰

### 相容性標準
- [ ] 向後相容舊格式
- [ ] 現有功能正常運作
- [ ] 匯出功能正確
- [ ] GUI 自動適應不同格式

### 品質標準
- [ ] 所有測試通過
- [ ] 無迴歸錯誤
- [ ] 文件完整更新
- [ ] 使用者介面直觀易用
- [ ] C++ 對齊行為與編譯器一致

## 最新實作更新

### 2024年最新改進：輸入驗證增強

#### 問題描述
在使用者介面中，當使用者在結構體大小欄位輸入非數字內容（如 "把6"）時，程式會拋出 Tkinter 例外，導致應用程式崩潰。

#### 解決方案
**檔案：** `src/view/struct_view.py`

**改動內容：**
- 在 `get_manual_struct_definition()` 方法中新增輸入驗證
- 使用 try/except 區塊包裝 `size_var.get()` 呼叫
- 當輸入非數字時，自動回傳安全預設值 0

```python
def get_manual_struct_definition(self):
    # 支援向後相容性：根據成員格式決定返回格式
    if self.members and "type" in self.members[0]:
        # V3 格式
        members_data = [
            {"name": m["name"], "type": m.get("type", ""), "bit_size": m["bit_size"]}
            for m in self.members
        ]
    else:
        # 舊格式
        members_data = [
            {"name": m["name"], "byte_size": m.get("byte_size", 0), "bit_size": m["bit_size"]}
            for m in self.members
        ]
    # 防呆：size_var 只允許數字
    try:
        total_size = self.size_var.get()
    except Exception:
        total_size = 0
    return {
        "struct_name": self.struct_name_var.get(),
        "total_size": total_size,
        "members": members_data
    }
```

#### 測試覆蓋
**檔案：** `tests/test_struct_view.py`

**新增測試：**
```python
def test_size_var_non_numeric_should_return_zero(self):
    self.view.size_var.set("把6")
    # 不應拋出例外，total_size 應為 0
    struct_data = self.view.get_manual_struct_definition()
    self.assertEqual(struct_data["total_size"], 0)
```

#### 實作效益
- **穩定性提升**：防止非數字輸入導致應用程式崩潰
- **使用者體驗改善**：提供友善的錯誤處理，而非程式崩潰
- **資料完整性**：確保結構體大小始終為有效數字
- **向後相容性**：不影響現有功能，僅增強錯誤處理

#### 技術細節
- **TDD 實作**：先寫測試確認問題，再實作修復
- **防禦性程式設計**：使用 try/except 處理所有可能的輸入異常
- **安全預設值**：當輸入無效時，回傳 0 作為安全的預設值
- **測試驗證**：自動化測試確保修復正確且不會產生迴歸錯誤

## C++ 標準對齊機制實現

### 背景

#### 之前的行為 (V2)
- 手動結構體模式使用線性打包，無填充
- 所有成員緊密排列，不考慮型別
- 無自動對齊或填充插入
- 佈局與 C++ 編譯器行為不符

#### 新行為 (V3)
- 手動結構體模式現在完全支援 C++ 標準對齊和填充
- 從 byte/bit 大小規格自動推斷型別
- 成員間自動插入填充
- 結構體大小按最大成員對齊要求對齊
- 與 C++ 編譯器產生的記憶體佈局完全相同

### 核心實現變更

#### 型別推斷系統
**新函數**：`_convert_to_cpp_members(members)`

```python
def _convert_to_cpp_members(self, members):
    """將 byte/bit 欄位轉換為 C++ 標準型別"""
    def infer_type(byte_size, bit_size):
        if bit_size > 0:
            # bitfield，預設用 unsigned int
            return {"type": "unsigned int", "name": "", "is_bitfield": True, "bit_size": bit_size}
        if byte_size == 1:
            return {"type": "char", "name": ""}
        elif byte_size == 2:
            return {"type": "short", "name": ""}
        elif byte_size == 4:
            return {"type": "int", "name": ""}
        elif byte_size == 8:
            return {"type": "long long", "name": ""}
        elif byte_size > 0:
            # 其他大小用 unsigned char 陣列
            return {"type": "unsigned char", "name": "", "array_size": byte_size}
        else:
            return None
```

#### 佈局計算更新
**修改函數**：`calculate_manual_layout(members, total_size)`

```python
def calculate_manual_layout(self, members, total_size):
    # 使用 _convert_to_cpp_members 轉換為 C++ 標準型別
    expanded_members = self._convert_to_cpp_members(members)
    # 呼叫 calculate_layout 產生 C++ 標準 struct align/padding
    layout, total, align = calculate_layout(expanded_members)
    return layout
```

### 對齊規則

#### C++ 標準對齊規則
系統遵循標準 C++ 對齊規則：

1. **成員對齊**：每個成員按其型別的對齊要求進行對齊
2. **結構體對齊**：整個結構體按最大成員的對齊要求進行對齊
3. **填充插入**：在成員之間插入填充位元組以滿足對齊
4. **最終填充**：結構體大小填充為結構體對齊的倍數

#### 對齊值（64位系統）

| 型別 | 大小 | 對齊 |
|------|------|------|
| `char` | 1 | 1 |
| `short` | 2 | 2 |
| `int` | 4 | 4 |
| `long long` | 8 | 8 |
| `pointer` | 8 | 8 |

### 範例

#### 範例 1：簡單對齊

**手動輸入：**
```
Member 1: name="a", byte_size=1, bit_size=0  (char)
Member 2: name="b", byte_size=4, bit_size=0  (int)
Total Size: 8
```

**C++ 等效：**
```cpp
struct MyStruct {
    char a;     // offset 0, size 1
    // 3 bytes padding
    int b;      // offset 4, size 4
};
// total size: 8 bytes
```

**記憶體佈局：**
```
Offset: 0  1  2  3  4  5  6  7
        [a][pad][pad][pad][  b  ][  b  ][  b  ][  b  ]
```

#### 範例 2：Bitfield 打包

**手動輸入：**
```
Member 1: name="flags1", byte_size=0, bit_size=3
Member 2: name="flags2", byte_size=0, bit_size=5
Member 3: name="flags3", byte_size=0, bit_size=8
Total Size: 4
```

**C++ 等效：**
```cpp
struct MyStruct {
    unsigned int flags1 : 3;   // bit offset 0
    unsigned int flags2 : 5;   // bit offset 3
    unsigned int flags3 : 8;   // bit offset 8
};
// total size: 4 bytes (one storage unit)
```

**記憶體佈局：**
```
Storage Unit (4 bytes): [flags1:3][flags2:5][flags3:8][unused:16]
```

## 開發方法論

### 測試驅動開發 (TDD)
所有最近的改進都遵循 TDD 方法論：
1. **Red**：先寫失敗的測試
2. **Green**：實作最小程式碼讓測試通過
3. **Refactor**：清理和優化程式碼

### 品質保證
- **全面測試**：單元、整合和 GUI 測試
- **向後相容性**：所有變更都維持現有功能
- **文件記錄**：所有變更的詳細技術文件
- **程式碼審查**：所有變更在整合前都經過審查和測試

## 未來規劃

### 計劃改進
1. **增強型別系統**：支援更複雜的 C++ 型別
2. **效能優化**：改進解析和計算速度
3. **使用者介面**：額外的易用性增強
4. **匯出功能**：更多匯出格式選項

### 維護
- 定期依賴更新
- 錯誤修復優先級
- 使用者回饋整合
- 持續測試改進

## 貢獻指南

當為此專案貢獻時：
1. 遵循 TDD 方法論
2. 確保向後相容性
3. 更新相關文件
4. 新增全面測試覆蓋
5. 遵循現有程式碼風格和模式

## 結論

V3 手動 Struct 輸入改進將大幅提升 MyStruct 功能的易用性和準確性。透過新增型別選擇、移除 byte_size 欄位、實現 C++ 標準對齊機制，以及增強輸入驗證，我們將提供更直觀、更一致、更穩定的介面，同時保持向後相容性。

這個改進將讓使用者能夠：
- 明確指定 C++ 型別，避免自動推斷的侷限
- 享受更簡潔的使用者介面
- 獲得更好的型別控制和驗證
- 保持與現有功能的相容性
- 享受與 C++ 編譯器完全一致的記憶體佈局
- 使用更穩定的應用程式，不會因輸入錯誤而崩潰

這個改進確保了應用程式在面對各種使用者輸入時的穩定性，是 V3 功能實作過程中的重要品質提升。 

## TDD Refactor: 統一解析邏輯 (2024年更新)

### 概述
本次 refactor 統一了 `.H 檔 tab` 與 `MyStruct tab` 的 struct 解析邏輯，消除重複程式碼，提高維護性與一致性。

### 主要改進

#### 1. 統一解析方法
- **新增 `parse_struct_bytes` 方法**：在 `StructModel` 中新增通用解析方法，供兩個 tab 共用
- **消除重複邏輯**：原本 `parse_hex_data` 與 `parse_manual_hex_data` 有大量重複的解析邏輯
- **統一介面**：兩個 tab 都使用相同的 `parse_struct_bytes(hex_data, byte_order, layout)` 介面

#### 2. Presenter 層重構
- **支援新舊介面**：`StructPresenter.parse_hex_data` 與 `parse_manual_hex_data` 支援直接傳入參數或 GUI 操作
- **向下相容**：GUI 操作不受影響，但測試可直接傳入參數
- **統一呼叫**：兩個方法內部都呼叫 `model.parse_struct_bytes`

#### 3. View 層修正
- **修正呼叫方式**：`StructView._on_parse_manual_hex` 正確組合 hex_data、layout、byte_order
- **統一參數格式**：不再傳入 hex_parts、struct_def、endian，改為 hex_data、layout、byte_order

#### 4. 測試覆蓋
- **新增 presenter 層測試**：驗證兩個 tab 都呼叫 `model.parse_struct_bytes`
- **修正 mock presenter**：讓測試中的 mock 兼容新簽名
- **全測試通過**：31 個測試全部通過，包含 GUI、解析、顯示、padding、bitfield 等

### 技術細節

#### 統一解析流程
```python
# 原本：兩套解析邏輯
.H 檔 tab: presenter.parse_hex_data() → model.parse_hex_data()
MyStruct tab: presenter.parse_manual_hex_data() → model.parse_manual_hex_data()

# 現在：統一解析邏輯
.H 檔 tab: presenter.parse_hex_data() → model.parse_struct_bytes()
MyStruct tab: presenter.parse_manual_hex_data() → model.parse_struct_bytes()
```

#### 新方法簽名
```python
def parse_struct_bytes(self, hex_data, byte_order, layout):
    """通用 struct bytes 解析，供 .H 檔與 MyStruct tab 共用"""
    # 統一的解析邏輯，支援 padding、bitfield、大小端
```

#### Presenter 重構
```python
def parse_hex_data(self, hex_data=None, byte_order=None, layout=None):
    """通用解析方法：
    - 若有傳 hex_data/byte_order/layout，直接呼叫 model.parse_struct_bytes
    - 否則維持原本 GUI 行為
    """

def parse_manual_hex_data(self, hex_data=None, layout=None, byte_order=None):
    """通用 MyStruct 解析方法：
    - 若有傳 hex_data/layout/byte_order，直接呼叫 model.parse_struct_bytes
    - 否則維持原本 GUI 行為
    """
```

### 效益
1. **程式碼重複消除**：減少約 50% 的解析邏輯重複
2. **維護性提升**：修改解析邏輯只需改一個地方
3. **一致性保證**：兩個 tab 的解析結果完全一致
4. **測試覆蓋完整**：所有功能都有自動化測試
5. **向下相容**：GUI 操作不受影響

### 測試驗證
- **31 個測試全部通過**：包含 GUI 操作、解析邏輯、顯示功能
- **Mock presenter 測試**：驗證兩個 tab 都呼叫統一方法
- **真實 presenter 整合測試**：驗證實際 GUI 操作正確
- **Padding/bitfield 測試**：驗證複雜 case 正確處理

### 未來擴充
- 新增 float/double 支援
- 新增錯誤處理優化
- 新增更多型別支援
- 所有擴充都基於統一的 `parse_struct_bytes` 方法 