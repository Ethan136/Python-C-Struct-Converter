"""
v7 展平策略實作

提供各種結構的展平策略實作。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from itertools import product
from .ast_node import ASTNode


class FlattenedNode:
    """展平後的節點"""
    
    def __init__(self, name: str, type_name: str, offset: int, size: int, 
                 bit_size: Optional[int] = None, bit_offset: Optional[int] = None,
                 metadata: Dict[str, Any] = None):
        self.name = name
        self.type = type_name
        self.offset = offset
        self.size = size
        self.bit_size = bit_size
        self.bit_offset = bit_offset
        self.metadata = metadata or {}


class FlatteningStrategy(ABC):
    """展平策略抽象基類"""

    def __init__(self, pack_alignment: Optional[int] = None):
        self.pack_alignment = pack_alignment

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

    def _get_basic_type_alignment(self, type_name: str) -> int:
        """取得基本型別對齊值"""
        type_align = {
            'char': 1, 'unsigned char': 1,
            'short': 2, 'unsigned short': 2,
            'int': 4, 'unsigned int': 4,
            'long': 8, 'unsigned long': 8,
            'float': 4, 'double': 8
        }
        return type_align.get(type_name, 4)


class StructFlatteningStrategy(FlatteningStrategy):
    """Struct 展平策略"""

    def __init__(self, pack_alignment: Optional[int] = None):
        super().__init__(pack_alignment)
    
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
            nodes = ArrayFlatteningStrategy(self.pack_alignment).flatten_node(child, prefix)
            for n in nodes:
                n.offset += base_offset
            return nodes
        elif child.is_struct or child.is_union:
            return self._flatten_nested(child, prefix, base_offset)
        elif child.is_bitfield:
            nodes = BitfieldFlatteningStrategy(self.pack_alignment).flatten_node(child, prefix)
            for n in nodes:
                n.offset = base_offset
            return nodes
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
                    # 陣列中的結構應該被視為匿名結構，直接使用陣列索引作為前綴
                    child_prefix = f"{name}."
                    child_nodes = self._flatten_child(child, child_prefix, offset)
                    result.extend(child_nodes)
            else:  # 基本型別陣列
                result.append(FlattenedNode(name, node.type, offset, element_size))
        
        return result
    
    def _flatten_nested(self, node: ASTNode, prefix: str, base_offset: int) -> List[FlattenedNode]:
        """展平巢狀結構節點"""
        result = []
        
        # 修正：匿名結構不應該在名稱中加入結構名稱
        if node.is_anonymous:
            # 為匿名結構生成一個臨時名稱
            anonymous_name = f"anonymous_{node.id[:8]}"
            nested_prefix = f"{prefix}{anonymous_name}."
        else:
            # 檢查是否在陣列上下文中（前綴包含陣列索引）
            if '[' in prefix and ']' in prefix:
                # 在陣列上下文中，結構應該被視為匿名結構
                nested_prefix = prefix
            else:
                nested_prefix = f"{prefix}{node.name}."
        
        for child in node.children:
            child_nodes = self._flatten_child(child, nested_prefix, base_offset)
            result.extend(child_nodes)
        
        return result
    
    def _create_flattened_node(self, node: ASTNode, prefix: str, base_offset: int) -> FlattenedNode:
        """建立展平節點"""
        name = f"{prefix}{node.name}"
        size = self._get_basic_type_size(node.type)
        return FlattenedNode(name, node.type, base_offset, size)
    
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
        ranges = [range(dim) for dim in dimensions]
        return list(product(*ranges))
    
    def _calculate_array_offset(self, indices: tuple, dimensions: List[int], element_size: int) -> int:
        """計算陣列元素偏移"""
        offset = 0
        stride = element_size
        for idx, dim in zip(reversed(indices), reversed(dimensions)):
            offset += idx * stride
            stride *= dim
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
        effective = min(alignment, self.pack_alignment) if self.pack_alignment else alignment
        return (offset + effective - 1) // effective * effective
    
    def _calculate_child_layout(self, child: ASTNode) -> Dict[str, Any]:
        """計算子節點佈局"""
        if child.is_struct:
            return self.calculate_layout(child)
        elif child.is_union:
            return UnionFlatteningStrategy(self.pack_alignment).calculate_layout(child)
        elif child.is_array:
            return ArrayFlatteningStrategy(self.pack_alignment).calculate_layout(child)
        else:
            size = self._get_basic_type_size(child.type)
            alignment = self._get_basic_type_alignment(child.type)
            return {'size': size, 'alignment': alignment}


class UnionFlatteningStrategy(FlatteningStrategy):
    """Union 展平策略"""

    def __init__(self, pack_alignment: Optional[int] = None):
        super().__init__(pack_alignment)
    
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
            nodes = ArrayFlatteningStrategy(self.pack_alignment).flatten_node(child, prefix)
            for n in nodes:
                n.offset = base_offset
            return nodes
        elif child.is_struct or child.is_union:
            return self._flatten_nested(child, prefix, base_offset)
        elif child.is_bitfield:
            nodes = BitfieldFlatteningStrategy(self.pack_alignment).flatten_node(child, prefix)
            for n in nodes:
                n.offset = base_offset
            return nodes
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
            offset = base_offset  # union 中所有成員偏移都是 0
            
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
        
        # 修正：匿名結構不應該在名稱中加入結構名稱
        if node.is_anonymous:
            # 為匿名結構生成一個臨時名稱
            anonymous_name = f"anonymous_{node.id[:8]}"
            nested_prefix = f"{prefix}{anonymous_name}."
        else:
            # 檢查是否在陣列上下文中（前綴包含陣列索引）
            if '[' in prefix and ']' in prefix:
                # 在陣列上下文中，結構應該被視為匿名結構
                nested_prefix = prefix
            else:
                nested_prefix = f"{prefix}{node.name}."
        
        for child in node.children:
            child_nodes = self._flatten_child(child, nested_prefix, base_offset)
            result.extend(child_nodes)
        
        return result
    
    def _create_flattened_node(self, node: ASTNode, prefix: str, base_offset: int) -> FlattenedNode:
        """建立展平節點"""
        name = f"{prefix}{node.name}"
        size = self._get_basic_type_size(node.type)
        return FlattenedNode(name, node.type, base_offset, size)
    
    def generate_name(self, node: ASTNode, prefix: str = "") -> str:
        """生成展平後的名稱"""
        if node.is_anonymous:
            return f"{prefix}anonymous_{node.id[:8]}"
        else:
            return f"{prefix}{node.name}"
    
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
    
    def _calculate_element_size(self, node: ASTNode) -> int:
        """計算陣列元素大小"""
        if node.children:  # 巢狀結構
            return self.calculate_layout(node)['size']
        else:  # 基本型別
            return self._get_basic_type_size(node.type)
    
    def _generate_indices(self, dimensions: List[int]) -> List[tuple]:
        """生成陣列索引組合"""
        ranges = [range(dim) for dim in dimensions]
        return list(product(*ranges))
    
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
    
    def _calculate_child_layout(self, child: ASTNode) -> Dict[str, Any]:
        """計算子節點佈局"""
        if child.is_struct:
            return StructFlatteningStrategy(self.pack_alignment).calculate_layout(child)
        elif child.is_union:
            return UnionFlatteningStrategy(self.pack_alignment).calculate_layout(child)
        elif child.is_array:
            return ArrayFlatteningStrategy(self.pack_alignment).calculate_layout(child)
        else:
            size = self._get_basic_type_size(child.type)
            alignment = self._get_basic_type_alignment(child.type)
            return {'size': size, 'alignment': alignment}


class ArrayFlatteningStrategy(StructFlatteningStrategy):
    """Array 展平策略"""

    def __init__(self, pack_alignment: Optional[int] = None):
        super().__init__(pack_alignment)

    def flatten_node(self, node: ASTNode, prefix: str = "") -> List[FlattenedNode]:
        result = []
        element_size = self._calculate_element_size(node)
        indices = self._generate_indices(node.array_dims)
        for idx in indices:
            idx_str = ''.join(f'[{i}]' for i in idx)
            elem_prefix = f"{prefix}{node.name}{idx_str}"
            offset = self._calculate_array_offset(idx, node.array_dims, element_size)
            if node.children:
                for child in node.children:
                    child_nodes = StructFlatteningStrategy(self.pack_alignment)._flatten_child(child, f"{elem_prefix}.", offset)
                    result.extend(child_nodes)
            else:
                result.append(FlattenedNode(elem_prefix, node.type, offset, element_size))
        return result

    def generate_name(self, node: ASTNode, prefix: str = "") -> str:
        return f"{prefix}{node.name}"

    def calculate_layout(self, node: ASTNode) -> Dict[str, Any]:
        elem_layout = self._calculate_element_layout(node)
        total_elements = 1
        for dim in node.array_dims:
            total_elements *= dim
        return {
            'size': elem_layout['size'] * total_elements,
            'alignment': elem_layout['alignment'],
            'children': []
        }

    def _calculate_element_size(self, node: ASTNode) -> int:
        return self._calculate_element_layout(node)['size']

    def _calculate_element_layout(self, node: ASTNode) -> Dict[str, Any]:
        if node.children:
            child = node.children[0]
            if child.is_struct:
                layout = StructFlatteningStrategy(self.pack_alignment).calculate_layout(child)
            elif child.is_union:
                layout = UnionFlatteningStrategy(self.pack_alignment).calculate_layout(child)
            else:
                size = self._get_basic_type_size(child.type)
                align = self._get_basic_type_alignment(child.type)
                layout = {'size': size, 'alignment': align}
        else:
            size = self._get_basic_type_size(node.type)
            align = self._get_basic_type_alignment(node.type)
            layout = {'size': size, 'alignment': align}
        return layout


class BitfieldFlatteningStrategy(FlatteningStrategy):
    """Bitfield 展平策略"""

    def __init__(self, pack_alignment: Optional[int] = None):
        super().__init__(pack_alignment)

    def flatten_node(self, node: ASTNode, prefix: str = "") -> List[FlattenedNode]:
        name = self.generate_name(node, prefix)
        size = self._get_basic_type_size(node.type)
        bit_offset = node.bit_offset or 0
        return [FlattenedNode(name, node.type, 0, size, bit_size=node.bit_size, bit_offset=bit_offset)]

    def generate_name(self, node: ASTNode, prefix: str = "") -> str:
        if node.is_anonymous or not node.name:
            return f"{prefix}anonymous_{node.id[:8]}"
        return f"{prefix}{node.name}"

    def calculate_layout(self, node: ASTNode) -> Dict[str, Any]:
        size = self._get_basic_type_size(node.type)
        alignment = self._get_basic_type_alignment(node.type)
        return {
            'size': size,
            'alignment': alignment,
            'bit_size': node.bit_size,
            'bit_offset': node.bit_offset or 0
        }

