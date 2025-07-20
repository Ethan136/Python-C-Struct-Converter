"""
v7 AST 節點實作

提供優化的 AST 節點結構和工廠類別。
"""

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