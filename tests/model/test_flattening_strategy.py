"""
v7 展平策略測試

測試 FlatteningStrategy 和相關實作。
"""

import pytest
from src.model.ast_node import ASTNode, ASTNodeFactory
from src.model.flattening_strategy import (
    FlatteningStrategy, 
    StructFlatteningStrategy, 
    UnionFlatteningStrategy,
    FlattenedNode
)


class TestFlattenedNode:
    """展平節點測試"""
    
    def test_flattened_node_creation(self):
        """測試展平節點建立"""
        # Act
        node = FlattenedNode("test", "int", 0, 4)
        
        # Assert
        assert node.name == "test"
        assert node.type == "int"
        assert node.offset == 0
        assert node.size == 4
        assert node.bit_size is None
        assert node.bit_offset is None
        assert node.metadata == {}
    
    def test_flattened_node_with_bitfield(self):
        """測試位元欄位展平節點建立"""
        # Act
        node = FlattenedNode("flags", "unsigned int", 0, 4, bit_size=3, bit_offset=0)
        
        # Assert
        assert node.name == "flags"
        assert node.type == "unsigned int"
        assert node.offset == 0
        assert node.size == 4
        assert node.bit_size == 3
        assert node.bit_offset == 0


class TestStructFlatteningStrategy:
    """Struct 展平策略測試"""
    
    def setup_method(self):
        """測試前準備"""
        self.strategy = StructFlatteningStrategy()
        self.factory = ASTNodeFactory()
    
    def test_flatten_simple_struct(self):
        """測試簡單結構展平"""
        # Arrange
        struct_node = self.factory.create_struct_node("Test")
        int_node = self.factory.create_basic_node("x", "int")
        char_node = self.factory.create_basic_node("y", "char")
        
        struct_node.add_child(int_node)
        struct_node.add_child(char_node)
        
        # Act
        flattened = self.strategy.flatten_node(struct_node)
        
        # Assert
        assert len(flattened) == 2
        assert flattened[0].name == "x"
        assert flattened[0].type == "int"
        assert flattened[0].offset == 0
        assert flattened[0].size == 4
        assert flattened[1].name == "y"
        assert flattened[1].type == "char"
        assert flattened[1].offset == 4
        assert flattened[1].size == 1
    
    def test_flatten_nested_struct(self):
        """測試巢狀結構展平"""
        # Arrange
        outer = self.factory.create_struct_node("Outer")
        inner = self.factory.create_struct_node("Inner")
        inner.add_child(self.factory.create_basic_node("x", "int"))
        inner.add_child(self.factory.create_basic_node("y", "char"))
        
        outer.add_child(inner)
        outer.add_child(self.factory.create_basic_node("z", "int"))
        
        # Act
        flattened = self.strategy.flatten_node(outer)
        
        # Assert
        assert len(flattened) == 3
        assert flattened[0].name == "Inner.x"
        assert flattened[0].type == "int"
        assert flattened[1].name == "Inner.y"
        assert flattened[1].type == "char"
        assert flattened[2].name == "z"
        assert flattened[2].type == "int"
    
    def test_flatten_anonymous_struct(self):
        """測試匿名結構展平"""
        # Arrange
        outer = self.factory.create_struct_node("Outer")
        inner = self.factory.create_struct_node("", is_anonymous=True)
        inner.add_child(self.factory.create_basic_node("x", "int"))
        
        outer.add_child(inner)
        
        # Act
        flattened = self.strategy.flatten_node(outer)
        
        # Assert
        assert len(flattened) == 1
        # 匿名結構應該有自動生成的名稱
        assert "anonymous" in flattened[0].name
        assert flattened[0].type == "int"
    
    def test_flatten_array(self):
        """測試陣列展平"""
        # Arrange
        struct_node = self.factory.create_struct_node("ArrayTest")
        array_node = self.factory.create_array_node("arr", "int", [2, 3])
        struct_node.add_child(array_node)
        
        # Act
        flattened = self.strategy.flatten_node(struct_node)
        
        # Assert
        assert len(flattened) == 6  # 2 * 3 = 6
        assert flattened[0].name == "arr[0][0]"
        assert flattened[0].type == "int"
        assert flattened[5].name == "arr[1][2]"
        assert flattened[5].type == "int"
    
    def test_flatten_nested_array(self):
        """測試巢狀陣列展平"""
        # Arrange
        struct_node = self.factory.create_struct_node("NestedArrayTest")
        
        # 建立巢狀結構陣列
        inner_struct = self.factory.create_struct_node("Inner")
        inner_struct.add_child(self.factory.create_basic_node("x", "int"))
        inner_struct.add_child(self.factory.create_basic_node("y", "char"))
        
        array_node = self.factory.create_array_node("arr", "struct", [2])
        array_node.add_child(inner_struct)
        
        struct_node.add_child(array_node)
        
        # Act
        flattened = self.strategy.flatten_node(struct_node)
        
        # Assert
        assert len(flattened) == 4  # 2 * (1 + 1) = 4
        assert flattened[0].name == "arr[0].x"
        assert flattened[1].name == "arr[0].y"
        assert flattened[2].name == "arr[1].x"
        assert flattened[3].name == "arr[1].y"
    
    def test_calculate_layout_simple(self):
        """測試簡單佈局計算"""
        # Arrange
        struct_node = self.factory.create_struct_node("LayoutTest")
        struct_node.add_child(self.factory.create_basic_node("a", "char"))
        struct_node.add_child(self.factory.create_basic_node("b", "int"))
        
        # Act
        layout = self.strategy.calculate_layout(struct_node)
        
        # Assert
        assert layout['size'] == 8  # char(1) + padding(3) + int(4)
        assert layout['alignment'] == 4
        assert len(layout['children']) == 2
    
    def test_calculate_layout_with_alignment(self):
        """測試對齊佈局計算"""
        # Arrange
        struct_node = self.factory.create_struct_node("AlignmentTest")
        struct_node.add_child(self.factory.create_basic_node("a", "char"))
        struct_node.add_child(self.factory.create_basic_node("b", "double"))
        
        # Act
        layout = self.strategy.calculate_layout(struct_node)
        
        # Assert
        assert layout['size'] == 16  # char(1) + padding(7) + double(8)
        assert layout['alignment'] == 8
    
    def test_generate_name_simple(self):
        """測試簡單名稱生成"""
        # Arrange
        node = self.factory.create_basic_node("test", "int")
        
        # Act
        name = self.strategy.generate_name(node, "prefix.")
        
        # Assert
        assert name == "prefix.test"
    
    def test_generate_name_anonymous(self):
        """測試匿名結構名稱生成"""
        # Arrange
        node = self.factory.create_struct_node("", is_anonymous=True)
        
        # Act
        name = self.strategy.generate_name(node, "prefix.")
        
        # Assert
        assert "anonymous" in name
        assert name.startswith("prefix.")


class TestUnionFlatteningStrategy:
    """Union 展平策略測試"""
    
    def setup_method(self):
        """測試前準備"""
        self.strategy = UnionFlatteningStrategy()
        self.factory = ASTNodeFactory()
    
    def test_flatten_simple_union(self):
        """測試簡單 union 展平"""
        # Arrange
        union_node = self.factory.create_union_node("Test")
        int_node = self.factory.create_basic_node("x", "int")
        char_node = self.factory.create_basic_node("y", "char")
        
        union_node.add_child(int_node)
        union_node.add_child(char_node)
        
        # Act
        flattened = self.strategy.flatten_node(union_node)
        
        # Assert
        assert len(flattened) == 2
        assert flattened[0].name == "x"
        assert flattened[0].type == "int"
        assert flattened[0].offset == 0  # union 中所有成員偏移都是 0
        assert flattened[1].name == "y"
        assert flattened[1].type == "char"
        assert flattened[1].offset == 0  # union 中所有成員偏移都是 0
    
    def test_calculate_layout_union(self):
        """測試 union 佈局計算"""
        # Arrange
        union_node = self.factory.create_union_node("UnionTest")
        union_node.add_child(self.factory.create_basic_node("a", "char"))
        union_node.add_child(self.factory.create_basic_node("b", "double"))
        
        # Act
        layout = self.strategy.calculate_layout(union_node)
        
        # Assert
        assert layout['size'] == 8  # union 大小是最大成員的大小
        assert layout['alignment'] == 8  # union 對齊是最大成員的對齊
    
    def test_flatten_nested_union(self):
        """測試巢狀 union 展平"""
        # Arrange
        outer = self.factory.create_union_node("Outer")
        inner = self.factory.create_union_node("Inner")
        inner.add_child(self.factory.create_basic_node("x", "int"))
        inner.add_child(self.factory.create_basic_node("y", "char"))
        
        outer.add_child(inner)
        outer.add_child(self.factory.create_basic_node("z", "double"))
        
        # Act
        flattened = self.strategy.flatten_node(outer)
        
        # Assert
        assert len(flattened) == 3
        assert flattened[0].name == "Inner.x"
        assert flattened[1].name == "Inner.y"
        assert flattened[2].name == "z"
        # 所有成員的偏移都應該是 0
        assert all(node.offset == 0 for node in flattened)


class TestFlatteningStrategyIntegration:
    """展平策略整合測試"""
    
    def setup_method(self):
        """測試前準備"""
        self.factory = ASTNodeFactory()
    
    def test_complex_nested_structure(self):
        """測試複雜巢狀結構展平"""
        # Arrange
        # 建立複雜的巢狀結構
        root = self.factory.create_struct_node("Complex")
        
        # 匿名結構
        anonymous = self.factory.create_struct_node("", is_anonymous=True)
        anonymous.add_child(self.factory.create_basic_node("x", "int"))
        anonymous.add_child(self.factory.create_basic_node("y", "char"))
        
        # 陣列
        array = self.factory.create_array_node("arr", "int", [2])
        
        # 巢狀結構陣列
        nested_array = self.factory.create_array_node("nested", "struct", [2])
        inner = self.factory.create_struct_node("Inner")
        inner.add_child(self.factory.create_basic_node("a", "int"))
        nested_array.add_child(inner)
        
        root.add_child(anonymous)
        root.add_child(array)
        root.add_child(nested_array)
        
        # Act
        struct_strategy = StructFlatteningStrategy()
        flattened = struct_strategy.flatten_node(root)
        
        # Assert
        assert len(flattened) == 6  # 2 + 2 + 2 = 6
        # 檢查匿名結構成員
        assert any("anonymous" in node.name and "x" in node.name for node in flattened)
        assert any("anonymous" in node.name and "y" in node.name for node in flattened)
        # 檢查陣列成員
        assert any("arr[0]" in node.name for node in flattened)
        assert any("arr[1]" in node.name for node in flattened)
        # 檢查巢狀陣列成員
        assert any("nested[0].a" in node.name for node in flattened)
        assert any("nested[1].a" in node.name for node in flattened) 