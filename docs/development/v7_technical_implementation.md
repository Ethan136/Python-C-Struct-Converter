# v7 技術實作細節（Deprecated）

> Note (V23): 本文件為歷史規劃/實作記錄。自 V23 起，系統已移除 v7/legacy 版本切換，Modern 為唯一介面。請參考：
> - V23 規劃與 TDD：`docs/development/v23_Modern_Replaces_Legacy_and_TreeFlat_Visual_Diff_TDD.md`
> - 遷移指南：`docs/development/V23_MIGRATION_GUIDE.md`
> - 目前 GUI 說明：`src/view/README.md`

## 1. AST 節點結構實作

### 1.1 核心 AST 節點定義
```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid

@dataclass
class ASTNode:
    """v7 優化的 AST 節點結構"""
    
    # 基本資訊
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = "unknown"
    
    # 結構資訊
    children: List['ASTNode'] = field(default_factory=list)
    is_struct: bool = False
    is_union: bool = False
    is_array: bool = False
    is_bitfield: bool = False
    is_anonymous: bool = False
    
    # 陣列資訊
    array_dims: List[int] = field(default_factory=list)
    
    # 位元欄位資訊
    bit_size: Optional[int] = None
    bit_offset: Optional[int] = None
    
    # 記憶體佈局資訊
    offset: int = 0
    size: int = 0
    alignment: int = 1
    
    # 展平資訊
    flattened_name: str = ""
    
    # 元資料
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.flattened_name:
            self.flattened_name = self.name
    
    def add_child(self, child: 'ASTNode'):
        """添加子節點"""
        self.children.append(child)
    
    def get_child_by_name(self, name: str) -> Optional['ASTNode']:
        """根據名稱取得子節點"""
        for child in self.children:
            if child.name == name:
                return child
        return None
    
    def get_all_children_recursive(self) -> List['ASTNode']:
        """遞迴取得所有子節點"""
        result = []
        for child in self.children:
            result.append(child)
            result.extend(child.get_all_children_recursive())
        return result
    
    def validate(self) -> bool:
        """驗證節點結構"""
        if not self.id:
            return False
        if self.is_struct and self.is_union:
            return False
        if self.is_array and not self.array_dims:
            return False
        if self.is_bitfield and self.bit_size is None:
            return False
        return True
```

### 1.2 AST 節點工廠
```python
class ASTNodeFactory:
    """AST 節點工廠類別"""
    
    @staticmethod
    def create_struct_node(name: str, is_anonymous: bool = False) -> ASTNode:
        """建立 struct 節點"""
        return ASTNode(
            name=name,
            type="struct",
            is_struct=True,
            is_anonymous=is_anonymous
        )
    
    @staticmethod
    def create_union_node(name: str, is_anonymous: bool = False) -> ASTNode:
        """建立 union 節點"""
        return ASTNode(
            name=name,
            type="union",
            is_union=True,
            is_anonymous=is_anonymous
        )
    
    @staticmethod
    def create_array_node(name: str, base_type: str, dimensions: List[int]) -> ASTNode:
        """建立陣列節點"""
        return ASTNode(
            name=name,
            type=base_type,
            is_array=True,
            array_dims=dimensions
        )
    
    @staticmethod
    def create_bitfield_node(name: str, base_type: str, bit_size: int) -> ASTNode:
        """建立位元欄位節點"""
        return ASTNode(
            name=name,
            type=base_type,
            is_bitfield=True,
            bit_size=bit_size
        )
    
    @staticmethod
    def create_basic_node(name: str, type_name: str) -> ASTNode:
        """建立基本型別節點"""
        return ASTNode(
            name=name,
            type=type_name
        )
```

## 2. 展平策略實作

### 2.1 展平策略介面
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class FlattenedNode:
    """展平後的節點"""
    
    def __init__(self, name: str, type_name: str, offset: int, size: int):
        self.name = name
        self.type = type_name
        self.offset = offset
        self.size = size
        self.bit_size = None
        self.bit_offset = None
        self.metadata = {}

class FlatteningStrategy(ABC):
    """展平策略抽象基類"""
    
    @abstractmethod
    def flatten_node(self, node: ASTNode, prefix: str = "") -> List[FlattenedNode]:
        """展平節點"""
        pass
    
    @abstractmethod
    def generate_name(self, node: ASTNode, prefix: str = "") -> str:
        """生成展平後的名稱"""
        pass
    
    @abstractmethod
    def calculate_layout(self, node: ASTNode) -> Dict[str, Any]:
        """計算佈局資訊"""
        pass
```

### 2.2 Struct 展平策略
```python
class StructFlatteningStrategy(FlatteningStrategy):
    """Struct 展平策略"""
    
    def flatten_node(self, node: ASTNode, prefix: str = "") -> List[FlattenedNode]:
        """展平 struct 節點"""
        result = []
        current_offset = 0
        
        for child in node.children:
            # 遞迴展平子節點
            child_nodes = self._flatten_child(child, prefix, current_offset)
            result.extend(child_nodes)
            
            # 更新偏移量
            if child_nodes:
                current_offset = child_nodes[-1].offset + child_nodes[-1].size
        
        return result
    
    def _flatten_child(self, child: ASTNode, prefix: str, base_offset: int) -> List[FlattenedNode]:
        """展平子節點"""
        if child.is_array:
            return self._flatten_array(child, prefix, base_offset)
        elif child.is_struct or child.is_union:
            return self._flatten_nested(child, prefix, base_offset)
        else:
            return [self._create_flattened_node(child, prefix, base_offset)]
    
    def _flatten_array(self, node: ASTNode, prefix: str, base_offset: int) -> List[FlattenedNode]:
        """展平陣列節點"""
        result = []
        element_size = self._calculate_element_size(node)
        
        # 生成所有陣列索引組合
        indices = self._generate_indices(node.array_dims)
        
        for idx_tuple in indices:
            idx_str = ''.join(f'[{i}]' for i in idx_tuple)
            name = f"{prefix}{node.name}{idx_str}"
            offset = base_offset + self._calculate_array_offset(idx_tuple, node.array_dims, element_size)
            
            if node.children:  # 巢狀結構陣列
                for child in node.children:
                    child_prefix = f"{name}."
                    child_nodes = self._flatten_child(child, child_prefix, offset)
                    result.extend(child_nodes)
            else:  # 基本型別陣列
                result.append(FlattenedNode(name, node.type, offset, element_size))
        
        return result
    
    def _flatten_nested(self, node: ASTNode, prefix: str, base_offset: int) -> List[FlattenedNode]:
        """展平巢狀結構節點"""
        result = []
        nested_prefix = f"{prefix}{node.name}." if node.name else prefix
        
        for child in node.children:
            child_nodes = self._flatten_child(child, nested_prefix, base_offset)
            result.extend(child_nodes)
        
        return result
    
    def generate_name(self, node: ASTNode, prefix: str = "") -> str:
        """生成展平後的名稱"""
        if node.is_anonymous:
            return f"{prefix}anonymous_{node.id[:8]}"
        else:
            return f"{prefix}{node.name}"
    
    def calculate_layout(self, node: ASTNode) -> Dict[str, Any]:
        """計算 struct 佈局"""
        total_size = 0
        max_alignment = 1
        
        for child in node.children:
            child_layout = self._calculate_child_layout(child)
            total_size = self._align_offset(total_size, child_layout['alignment'])
            total_size += child_layout['size']
            max_alignment = max(max_alignment, child_layout['alignment'])
        
        # 最終對齊
        total_size = self._align_offset(total_size, max_alignment)
        
        return {
            'size': total_size,
            'alignment': max_alignment,
            'children': [self._calculate_child_layout(child) for child in node.children]
        }
    
    def _calculate_element_size(self, node: ASTNode) -> int:
        """計算陣列元素大小"""
        if node.children:  # 巢狀結構
            return self.calculate_layout(node)['size']
        else:  # 基本型別
            return self._get_basic_type_size(node.type)
    
    def _generate_indices(self, dimensions: List[int]) -> List[tuple]:
        """生成陣列索引組合"""
        from itertools import product
        ranges = [range(dim) for dim in dimensions]
        return list(product(*ranges))
    
    def _calculate_array_offset(self, indices: tuple, dimensions: List[int], element_size: int) -> int:
        """計算陣列元素偏移"""
        offset = 0
        stride = element_size
        
        for i, idx in enumerate(indices):
            if i < len(dimensions) - 1:
                for j in range(i + 1, len(dimensions)):
                    stride *= dimensions[j]
            offset += idx * stride
        
        return offset
    
    def _get_basic_type_size(self, type_name: str) -> int:
        """取得基本型別大小"""
        type_sizes = {
            'char': 1, 'unsigned char': 1,
            'short': 2, 'unsigned short': 2,
            'int': 4, 'unsigned int': 4,
            'long': 8, 'unsigned long': 8,
            'float': 4, 'double': 8
        }
        return type_sizes.get(type_name, 4)
    
    def _align_offset(self, offset: int, alignment: int) -> int:
        """對齊偏移量"""
        return (offset + alignment - 1) // alignment * alignment
```

### 2.3 Union 展平策略
```python
class UnionFlatteningStrategy(FlatteningStrategy):
    """Union 展平策略"""
    
    def flatten_node(self, node: ASTNode, prefix: str = "") -> List[FlattenedNode]:
        """展平 union 節點"""
        result = []
        union_size = self.calculate_layout(node)['size']
        
        for child in node.children:
            # union 中所有成員的偏移都是 0
            child_nodes = self._flatten_child(child, prefix, 0)
            result.extend(child_nodes)
        
        return result
    
    def _flatten_child(self, child: ASTNode, prefix: str, base_offset: int) -> List[FlattenedNode]:
        """展平 union 子節點"""
        if child.is_array:
            return self._flatten_array(child, prefix, base_offset)
        elif child.is_struct or child.is_union:
            return self._flatten_nested(child, prefix, base_offset)
        else:
            return [self._create_flattened_node(child, prefix, base_offset)]
    
    def calculate_layout(self, node: ASTNode) -> Dict[str, Any]:
        """計算 union 佈局"""
        max_size = 0
        max_alignment = 1
        
        for child in node.children:
            child_layout = self._calculate_child_layout(child)
            max_size = max(max_size, child_layout['size'])
            max_alignment = max(max_alignment, child_layout['alignment'])
        
        return {
            'size': max_size,
            'alignment': max_alignment,
            'children': [self._calculate_child_layout(child) for child in node.children]
        }
```

## 3. 解析器優化

### 3.1 v7 解析器
```python
class V7StructParser:
    """v7 優化的結構解析器"""
    
    def __init__(self):
        self.node_factory = ASTNodeFactory()
        self.current_id = 0
    
    def parse_struct_definition(self, content: str) -> Optional[ASTNode]:
        """解析結構定義"""
        try:
            # 清理輸入內容
            content = self._clean_content(content)
            
            # 解析結構名稱
            struct_match = re.match(r'struct\s+(\w+)\s*\{', content)
            if not struct_match:
                return None
            
            struct_name = struct_match.group(1)
            root_node = self.node_factory.create_struct_node(struct_name)
            
            # 解析結構體內容
            body_start = content.find('{') + 1
            body_end = self._find_matching_brace(content, body_start - 1)
            struct_body = content[body_start:body_end]
            
            # 解析成員
            self._parse_members(struct_body, root_node)
            
            return root_node
            
        except Exception as e:
            print(f"解析錯誤: {e}")
            return None
    
    def _parse_members(self, body: str, parent_node: ASTNode):
        """解析結構成員"""
        lines = self._split_member_lines(body)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            member_node = self._parse_member_line(line)
            if member_node:
                parent_node.add_child(member_node)
    
    def _parse_member_line(self, line: str) -> Optional[ASTNode]:
        """解析單一成員行"""
        # 處理巢狀結構
        if line.startswith('struct'):
            return self._parse_nested_struct(line)
        elif line.startswith('union'):
            return self._parse_nested_union(line)
        
        # 處理陣列
        if '[' in line and ']' in line:
            return self._parse_array_member(line)
        
        # 處理位元欄位
        if ':' in line:
            return self._parse_bitfield_member(line)
        
        # 處理基本型別
        return self._parse_basic_member(line)
    
    def _parse_nested_struct(self, line: str) -> Optional[ASTNode]:
        """解析巢狀結構"""
        # 實作巢狀結構解析邏輯
        pass
    
    def _parse_nested_union(self, line: str) -> Optional[ASTNode]:
        """解析巢狀聯合"""
        # 實作巢狀聯合解析邏輯
        pass
    
    def _parse_array_member(self, line: str) -> Optional[ASTNode]:
        """解析陣列成員"""
        # 實作陣列解析邏輯
        pass
    
    def _parse_bitfield_member(self, line: str) -> Optional[ASTNode]:
        """解析位元欄位成員"""
        # 實作位元欄位解析邏輯
        pass
    
    def _parse_basic_member(self, line: str) -> Optional[ASTNode]:
        """解析基本型別成員"""
        # 實作基本型別解析邏輯
        pass
    
    def _clean_content(self, content: str) -> str:
        """清理輸入內容"""
        # 移除註解
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # 移除多餘空白
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def _find_matching_brace(self, content: str, start: int) -> int:
        """尋找匹配的大括號"""
        brace_count = 0
        for i in range(start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return i
        return -1
    
    def _split_member_lines(self, body: str) -> List[str]:
        """分割成員行"""
        lines = []
        current_line = ""
        brace_count = 0
        
        for char in body:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == ';' and brace_count == 0:
                current_line += char
                lines.append(current_line.strip())
                current_line = ""
                continue
            
            current_line += char
        
        return lines
```

## AST Parser 切分成員的語意判斷設計（v7 新增）

### 設計原則
- 在解析 C struct/union 成員時，**切分階段就要語意判斷是否為匿名 bitfield**，而不是單純以分號 `;` 為界。
- 這樣能確保每一個成員（無論有名、匿名、bitfield、陣列）都能被 parser 邏輯正確地還原為語意單位。

### 實作策略
- 採用「語意切分」：
    - 掃描 struct body，每遇到分號 `;`，就判斷這一段是否為：
        - 一般成員（如 `int x;`）
        - 有名 bitfield（如 `unsigned int flags : 3;`）
        - 匿名 bitfield（如 `unsigned int : 2;`）
        - 陣列成員（如 `char str[10];`）
    - 若為匿名 bitfield，**必須保證型別與 bit 數在同一行**，不可被拆開。
- 可用正則或狀態機判斷每一段內容。

### 範例
```c
struct BitfieldTest {
    unsigned int flags : 3;
    unsigned int : 2;
    unsigned int value : 5;
};
```
- 切分後應得到：
    - `unsigned int flags : 3;`
    - `unsigned int : 2;`（匿名 bitfield）
    - `unsigned int value : 5;`

### Python 實作片段
```python
def split_members_semantic(body: str) -> List[str]:
    import re
    members = []
    buf = ''
    brace_count = 0
    for c in body:
        buf += c
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
        elif c == ';' and brace_count == 0:
            # 語意判斷：bitfield/一般成員/陣列
            if re.match(r'^\s*(?:\w+\s+)*\w+(\s+[a-zA-Z_]\w*)?\s*(:\s*\d+)?\s*;\s*$', buf.strip()):
                members.append(buf.strip())
            else:
                members.append(buf.strip())
            buf = ''
    if buf.strip():
        members.append(buf.strip())
    return members
```

### 效益
- **正確還原 C 語法語意**，避免匿名 bitfield 被拆開，提升 AST 準確度。
- **後續 AST 處理、展平、GUI 呈現都更簡單**。
- **TDD 測試更容易通過**，減少 parser bug。

### v7 相關模組需配合
- `parser.py`：必須採用語意切分，並在單元測試中驗證匿名 bitfield、陣列、巢狀結構等情境。
- `test_parser.py`：需有匿名 bitfield、複雜巢狀 struct 測試案例。

## AST Parser Bitfield 語意切分與解析的最穩健 TDD 重構方案（v7 建議）

### 設計原則
- **切分階段**（_split_member_lines）：
    - 只負責將每個 struct/union 成員語意完整地切成一行，不做語法判斷。
    - 例如：`unsigned int : 2;`、`unsigned int flags : 3;`、`int x;` 都是獨立一行。
- **解析階段**（_parse_member_line / _parse_bitfield_member）：
    - 先判斷有名 bitfield（有變數名稱），再判斷匿名 bitfield（無變數名稱）。
    - 型別用非貪婪 `(.+?)`，名稱用合法識別字 `[a-zA-Z_]\w*`。
    - 這樣能正確支援多單字型別、bitfield padding、C 語法 edge case。

### Python 實作範例
```python
def _parse_bitfield_member(self, line: str) -> Optional[ASTNode]:
    # 有名 bitfield
    named_pattern = r'^(.+?)\s+([a-zA-Z_]\w*)\s*:\s*(\d+)\s*;$'
    match = re.match(named_pattern, line.strip())
    if match:
        type_name = match.group(1).strip()
        var_name = match.group(2).strip()
        bit_size = int(match.group(3))
        return self.node_factory.create_bitfield_node(var_name, type_name, bit_size)
    # 匿名 bitfield
    anonymous_pattern = r'^(.+?)\s*:\s*(\d+)\s*;$'
    match = re.match(anonymous_pattern, line.strip())
    if match:
        type_name = match.group(1).strip()
        bit_size = int(match.group(2))
        node = self.node_factory.create_bitfield_node("", type_name, bit_size)
        node.is_anonymous = True
        return node
    return None
```

### 測試建議（TDD）
- 測試 `_split_member_lines` 能將 struct/union 內容正確切分為一行一語意。
- 測試 `_parse_bitfield_member` 能正確解析：
    - 有名 bitfield：`unsigned int flags : 3;` → type=`unsigned int`，name=`flags`，bit_size=3
    - 匿名 bitfield：`unsigned int : 2;` → type=`unsigned int`，name=`""`，bit_size=2
    - 多單字型別、padding、巢狀 struct/union 等 edge case。
- 測試複雜 struct/union，確保所有成員都能正確還原。

### 長期效益
- **可維護性高**：未來 C 語法 edge case 只需擴充解析階段，不會讓切分邏輯變複雜。
- **可擴充性強**：支援 typedef、macro、巢狀 struct/union、bitfield padding 等都容易。
- **TDD 友善**：每個階段職責單一，測試覆蓋容易，debug 容易。

---

## 4. GUI 整合實作

### 4.1 V7 Presenter
```python
class V7Presenter:
    """v7 Presenter，基於 v6 架構擴充"""
    
    def __init__(self):
        self.ast_root: Optional[ASTNode] = None
        self.flattened_nodes: List[FlattenedNode] = []
        self.context: Dict[str, Any] = self._init_context()
        self.parser = V7StructParser()
        self.flattening_strategy = self._create_flattening_strategy()
    
    def _init_context(self) -> Dict[str, Any]:
        """初始化 context"""
        return {
            'display_mode': 'tree',
            'expanded_nodes': ['root'],
            'selected_node': None,
            'error': None,
            'loading': False,
            'version': '1.0',
            'extra': {},
            'last_update_time': time.time()
        }
    
    def _create_flattening_strategy(self) -> FlatteningStrategy:
        """建立展平策略"""
        return StructFlatteningStrategy()
    
    def load_struct_definition(self, content: str) -> bool:
        """載入結構定義"""
        try:
            self.context['loading'] = True
            self._update_context()
            
            # 解析 AST
            self.ast_root = self.parser.parse_struct_definition(content)
            if not self.ast_root:
                self.context['error'] = "解析失敗"
                return False
            
            # 展平結構
            self.flattened_nodes = self.flattening_strategy.flatten_node(self.ast_root)
            
            # 更新 context
            self.context['loading'] = False
            self.context['error'] = None
            self.context['last_update_time'] = time.time()
            self._update_context()
            
            return True
            
        except Exception as e:
            self.context['error'] = str(e)
            self.context['loading'] = False
            self._update_context()
            return False
    
    def get_ast_tree(self) -> Optional[ASTNode]:
        """取得 AST 樹狀結構"""
        return self.ast_root
    
    def get_flattened_layout(self) -> List[FlattenedNode]:
        """取得展平後的佈局"""
        return self.flattened_nodes
    
    def switch_display_mode(self, mode: str):
        """切換顯示模式"""
        self.context['display_mode'] = mode
        self.context['expanded_nodes'] = ['root']
        self.context['selected_node'] = None
        self._update_context()
    
    def get_display_nodes(self, mode: str = None) -> List[Dict[str, Any]]:
        """取得顯示節點"""
        if mode is None:
            mode = self.context['display_mode']
        
        if mode == 'tree':
            return self._convert_ast_to_tree_nodes()
        else:
            return self._convert_flattened_to_tree_nodes()
    
    def _convert_ast_to_tree_nodes(self) -> List[Dict[str, Any]]:
        """將 AST 轉換為樹狀節點"""
        if not self.ast_root:
            return []
        
        return [self._ast_node_to_dict(self.ast_root)]
    
    def _ast_node_to_dict(self, node: ASTNode) -> Dict[str, Any]:
        """將 AST 節點轉換為字典"""
        result = {
            'id': node.id,
            'label': self._generate_node_label(node),
            'type': node.type,
            'children': [self._ast_node_to_dict(child) for child in node.children],
            'icon': self._get_node_icon(node),
            'extra': self._get_node_extra(node)
        }
        return result
    
    def _generate_node_label(self, node: ASTNode) -> str:
        """生成節點標籤"""
        if node.is_anonymous:
            return f"(anonymous {node.type})"
        elif node.is_array:
            dims_str = ''.join(f'[{dim}]' for dim in node.array_dims)
            return f"{node.name}{dims_str}: {node.type}"
        elif node.is_bitfield:
            return f"{node.name}: {node.type} : {node.bit_size}"
        else:
            return f"{node.name}: {node.type}"
    
    def _get_node_icon(self, node: ASTNode) -> str:
        """取得節點圖示"""
        if node.is_struct:
            return "struct"
        elif node.is_union:
            return "union"
        elif node.is_array:
            return "array"
        elif node.is_bitfield:
            return "bitfield"
        else:
            return "field"
    
    def _get_node_extra(self, node: ASTNode) -> Dict[str, Any]:
        """取得節點額外資訊"""
        return {
            'offset': node.offset,
            'size': node.size,
            'alignment': node.alignment,
            'is_anonymous': node.is_anonymous
        }
    
    def _update_context(self):
        """更新 context"""
        # 這裡會通知 View 更新顯示
        pass
```

## 5. 測試實作

### 5.1 AST 節點測試
```python
import pytest
from src.v7.ast_node import ASTNode, ASTNodeFactory

class TestASTNode:
    """AST 節點測試"""
    
    def test_node_creation(self):
        """測試節點建立"""
        node = ASTNode(name="test", type="int")
        assert node.name == "test"
        assert node.type == "int"
        assert node.id is not None
    
    def test_node_validation(self):
        """測試節點驗證"""
        # 有效節點
        valid_node = ASTNode(name="test", type="int")
        assert valid_node.validate() is True
        
        # 無效節點：struct 和 union 同時為 True
        invalid_node = ASTNode(name="test", type="struct", is_struct=True, is_union=True)
        assert invalid_node.validate() is False
    
    def test_add_child(self):
        """測試添加子節點"""
        parent = ASTNode(name="parent", type="struct", is_struct=True)
        child = ASTNode(name="child", type="int")
        
        parent.add_child(child)
        assert len(parent.children) == 1
        assert parent.children[0] == child
    
    def test_get_child_by_name(self):
        """測試根據名稱取得子節點"""
        parent = ASTNode(name="parent", type="struct", is_struct=True)
        child1 = ASTNode(name="child1", type="int")
        child2 = ASTNode(name="child2", type="char")
        
        parent.add_child(child1)
        parent.add_child(child2)
        
        found = parent.get_child_by_name("child1")
        assert found == child1
        
        not_found = parent.get_child_by_name("nonexistent")
        assert not_found is None

class TestASTNodeFactory:
    """AST 節點工廠測試"""
    
    def test_create_struct_node(self):
        """測試建立 struct 節點"""
        node = ASTNodeFactory.create_struct_node("TestStruct")
        assert node.name == "TestStruct"
        assert node.type == "struct"
        assert node.is_struct is True
        assert node.is_union is False
    
    def test_create_anonymous_struct_node(self):
        """測試建立匿名 struct 節點"""
        node = ASTNodeFactory.create_struct_node("", is_anonymous=True)
        assert node.is_anonymous is True
        assert node.name == ""
    
    def test_create_array_node(self):
        """測試建立陣列節點"""
        node = ASTNodeFactory.create_array_node("arr", "int", [2, 3])
        assert node.name == "arr"
        assert node.type == "int"
        assert node.is_array is True
        assert node.array_dims == [2, 3]
    
    def test_create_bitfield_node(self):
        """測試建立位元欄位節點"""
        node = ASTNodeFactory.create_bitfield_node("flags", "unsigned int", 3)
        assert node.name == "flags"
        assert node.type == "unsigned int"
        assert node.is_bitfield is True
        assert node.bit_size == 3
```

### 5.2 展平策略測試
```python
class TestStructFlatteningStrategy:
    """Struct 展平策略測試"""
    
    def setup_method(self):
        """測試前準備"""
        self.strategy = StructFlatteningStrategy()
        self.factory = ASTNodeFactory()
    
    def test_flatten_simple_struct(self):
        """測試簡單結構展平"""
        # 建立測試結構
        struct_node = self.factory.create_struct_node("Test")
        int_node = self.factory.create_basic_node("x", "int")
        char_node = self.factory.create_basic_node("y", "char")
        
        struct_node.add_child(int_node)
        struct_node.add_child(char_node)
        
        # 展平
        flattened = self.strategy.flatten_node(struct_node)
        
        # 驗證結果
        assert len(flattened) == 2
        assert flattened[0].name == "x"
        assert flattened[0].type == "int"
        assert flattened[1].name == "y"
        assert flattened[1].type == "char"
    
    def test_flatten_nested_struct(self):
        """測試巢狀結構展平"""
        # 建立巢狀結構
        outer = self.factory.create_struct_node("Outer")
        inner = self.factory.create_struct_node("Inner")
        inner.add_child(self.factory.create_basic_node("x", "int"))
        inner.add_child(self.factory.create_basic_node("y", "char"))
        
        outer.add_child(inner)
        outer.add_child(self.factory.create_basic_node("z", "int"))
        
        # 展平
        flattened = self.strategy.flatten_node(outer)
        
        # 驗證結果
        assert len(flattened) == 3
        assert flattened[0].name == "Inner.x"
        assert flattened[1].name == "Inner.y"
        assert flattened[2].name == "z"
    
    def test_flatten_array(self):
        """測試陣列展平"""
        # 建立陣列結構
        struct_node = self.factory.create_struct_node("ArrayTest")
        array_node = self.factory.create_array_node("arr", "int", [2, 3])
        struct_node.add_child(array_node)
        
        # 展平
        flattened = self.strategy.flatten_node(struct_node)
        
        # 驗證結果
        assert len(flattened) == 6  # 2 * 3 = 6
        assert flattened[0].name == "arr[0][0]"
        assert flattened[5].name == "arr[1][2]"
    
    def test_calculate_layout(self):
        """測試佈局計算"""
        struct_node = self.factory.create_struct_node("LayoutTest")
        struct_node.add_child(self.factory.create_basic_node("a", "char"))
        struct_node.add_child(self.factory.create_basic_node("b", "int"))
        
        layout = self.strategy.calculate_layout(struct_node)
        
        assert layout['size'] == 8  # char(1) + padding(3) + int(4)
        assert layout['alignment'] == 4
```

## 6. 效能優化建議

### 6.1 AST 解析優化
```python
class OptimizedV7Parser(V7StructParser):
    """效能優化的 v7 解析器"""
    
    def __init__(self):
        super().__init__()
        self._cache = {}  # 解析快取
        self._regex_cache = {}  # 正則表達式快取
    
    def parse_struct_definition(self, content: str) -> Optional[ASTNode]:
        """快取優化的解析"""
        content_hash = hash(content)
        if content_hash in self._cache:
            return self._cache[content_hash]
        
        result = super().parse_struct_definition(content)
        if result:
            self._cache[content_hash] = result
        
        return result
    
    def _compile_regex(self, pattern: str):
        """編譯正則表達式快取"""
        if pattern not in self._regex_cache:
            self._regex_cache[pattern] = re.compile(pattern)
        return self._regex_cache[pattern]
```

### 6.2 展平算法優化
```python
class OptimizedFlatteningStrategy(FlatteningStrategy):
    """效能優化的展平策略"""
    
    def __init__(self):
        self._layout_cache = {}  # 佈局計算快取
    
    def calculate_layout(self, node: ASTNode) -> Dict[str, Any]:
        """快取優化的佈局計算"""
        node_hash = self._get_node_hash(node)
        if node_hash in self._layout_cache:
            return self._layout_cache[node_hash]
        
        result = self._calculate_layout_impl(node)
        self._layout_cache[node_hash] = result
        
        return result
    
    def _get_node_hash(self, node: ASTNode) -> int:
        """計算節點雜湊值"""
        # 實作節點雜湊計算
        pass
```

---

> 本文件提供 v7 開發的詳細技術實作指南，包含完整的程式碼範例和測試實作。
> 開發時請參考此文件進行實作，並根據實際需求調整和擴充。 