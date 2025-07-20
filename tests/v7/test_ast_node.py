"""
v7 AST 節點測試

測試 ASTNode 和 ASTNodeFactory 的功能。
"""

import pytest
from src.v7.ast_node import ASTNode, ASTNodeFactory


class TestASTNode:
    """AST 節點測試"""
    
    def test_node_creation_with_basic_fields(self):
        """測試基本欄位的節點建立"""
        # Arrange & Act
        node = ASTNode(name="test", type="int")
        
        # Assert
        assert node.name == "test"
        assert node.type == "int"
        assert node.id is not None
        assert len(node.id) > 0
        assert node.children == []
        assert node.is_struct is False
        assert node.is_union is False
        assert node.is_array is False
        assert node.is_bitfield is False
        assert node.is_anonymous is False
    
    def test_node_creation_with_all_fields(self):
        """測試所有欄位的節點建立"""
        # Arrange
        import uuid
        test_id = str(uuid.uuid4())
        test_children = []
        test_metadata = {"key": "value"}
        
        # Act
        node = ASTNode(
            id=test_id,
            name="test_struct",
            type="struct",
            children=test_children,
            is_struct=True,
            is_union=False,
            is_array=False,
            is_bitfield=False,
            is_anonymous=False,
            array_dims=[],
            bit_size=None,
            bit_offset=None,
            offset=0,
            size=8,
            alignment=4,
            flattened_name="test_struct",
            metadata=test_metadata
        )
        
        # Assert
        assert node.id == test_id
        assert node.name == "test_struct"
        assert node.type == "struct"
        assert node.children == test_children
        assert node.is_struct is True
        assert node.is_union is False
        assert node.is_array is False
        assert node.is_bitfield is False
        assert node.is_anonymous is False
        assert node.array_dims == []
        assert node.bit_size is None
        assert node.bit_offset is None
        assert node.offset == 0
        assert node.size == 8
        assert node.alignment == 4
        assert node.flattened_name == "test_struct"
        assert node.metadata == test_metadata
    
    def test_node_validation_valid_node(self):
        """測試有效節點的驗證"""
        # Arrange
        node = ASTNode(name="test", type="int")
        
        # Act & Assert
        assert node.validate() is True
    
    def test_node_validation_invalid_struct_union_conflict(self):
        """測試 struct 和 union 衝突的驗證"""
        # Arrange
        node = ASTNode(
            name="test", 
            type="struct", 
            is_struct=True, 
            is_union=True
        )
        
        # Act & Assert
        assert node.validate() is False
    
    def test_node_validation_invalid_array_without_dims(self):
        """測試陣列節點沒有維度的驗證"""
        # Arrange
        node = ASTNode(
            name="test", 
            type="int", 
            is_array=True,
            array_dims=[]
        )
        
        # Act & Assert
        assert node.validate() is False
    
    def test_node_validation_invalid_bitfield_without_size(self):
        """測試位元欄位沒有大小的驗證"""
        # Arrange
        node = ASTNode(
            name="test", 
            type="unsigned int", 
            is_bitfield=True,
            bit_size=None
        )
        
        # Act & Assert
        assert node.validate() is False
    
    def test_node_validation_invalid_empty_id(self):
        """測試空 ID 的驗證"""
        # Arrange
        node = ASTNode(id="", name="test", type="int")
        
        # Act & Assert
        assert node.validate() is False
    
    def test_add_child(self):
        """測試添加子節點"""
        # Arrange
        parent = ASTNode(name="parent", type="struct", is_struct=True)
        child = ASTNode(name="child", type="int")
        
        # Act
        parent.add_child(child)
        
        # Assert
        assert len(parent.children) == 1
        assert parent.children[0] == child
    
    def test_get_child_by_name_existing(self):
        """測試根據名稱取得存在的子節點"""
        # Arrange
        parent = ASTNode(name="parent", type="struct", is_struct=True)
        child1 = ASTNode(name="child1", type="int")
        child2 = ASTNode(name="child2", type="char")
        
        parent.add_child(child1)
        parent.add_child(child2)
        
        # Act
        found = parent.get_child_by_name("child1")
        
        # Assert
        assert found == child1
    
    def test_get_child_by_name_nonexistent(self):
        """測試根據名稱取得不存在的子節點"""
        # Arrange
        parent = ASTNode(name="parent", type="struct", is_struct=True)
        child = ASTNode(name="child", type="int")
        parent.add_child(child)
        
        # Act
        found = parent.get_child_by_name("nonexistent")
        
        # Assert
        assert found is None
    
    def test_get_all_children_recursive(self):
        """測試遞迴取得所有子節點"""
        # Arrange
        root = ASTNode(name="root", type="struct", is_struct=True)
        child1 = ASTNode(name="child1", type="int")
        child2 = ASTNode(name="child2", type="struct", is_struct=True)
        grandchild = ASTNode(name="grandchild", type="char")
        
        root.add_child(child1)
        root.add_child(child2)
        child2.add_child(grandchild)
        
        # Act
        all_children = root.get_all_children_recursive()
        
        # Assert
        assert len(all_children) == 3
        assert child1 in all_children
        assert child2 in all_children
        assert grandchild in all_children
    
    def test_post_init_flattened_name(self):
        """測試初始化後處理 flattened_name"""
        # Arrange & Act
        node = ASTNode(name="test", type="int")
        
        # Assert
        assert node.flattened_name == "test"
    
    def test_post_init_flattened_name_already_set(self):
        """測試已設定的 flattened_name 不被覆蓋"""
        # Arrange & Act
        node = ASTNode(
            name="test", 
            type="int", 
            flattened_name="custom_name"
        )
        
        # Assert
        assert node.flattened_name == "custom_name"


class TestASTNodeFactory:
    """AST 節點工廠測試"""
    
    def test_create_struct_node(self):
        """測試建立 struct 節點"""
        # Act
        node = ASTNodeFactory.create_struct_node("TestStruct")
        
        # Assert
        assert node.name == "TestStruct"
        assert node.type == "struct"
        assert node.is_struct is True
        assert node.is_union is False
        assert node.is_array is False
        assert node.is_bitfield is False
        assert node.is_anonymous is False
    
    def test_create_anonymous_struct_node(self):
        """測試建立匿名 struct 節點"""
        # Act
        node = ASTNodeFactory.create_struct_node("", is_anonymous=True)
        
        # Assert
        assert node.is_anonymous is True
        assert node.name == ""
        assert node.is_struct is True
    
    def test_create_union_node(self):
        """測試建立 union 節點"""
        # Act
        node = ASTNodeFactory.create_union_node("TestUnion")
        
        # Assert
        assert node.name == "TestUnion"
        assert node.type == "union"
        assert node.is_union is True
        assert node.is_struct is False
        assert node.is_array is False
        assert node.is_bitfield is False
    
    def test_create_anonymous_union_node(self):
        """測試建立匿名 union 節點"""
        # Act
        node = ASTNodeFactory.create_union_node("", is_anonymous=True)
        
        # Assert
        assert node.is_anonymous is True
        assert node.name == ""
        assert node.is_union is True
    
    def test_create_array_node(self):
        """測試建立陣列節點"""
        # Act
        node = ASTNodeFactory.create_array_node("arr", "int", [2, 3])
        
        # Assert
        assert node.name == "arr"
        assert node.type == "int"
        assert node.is_array is True
        assert node.array_dims == [2, 3]
        assert node.is_struct is False
        assert node.is_union is False
        assert node.is_bitfield is False
    
    def test_create_bitfield_node(self):
        """測試建立位元欄位節點"""
        # Act
        node = ASTNodeFactory.create_bitfield_node("flags", "unsigned int", 3)
        
        # Assert
        assert node.name == "flags"
        assert node.type == "unsigned int"
        assert node.is_bitfield is True
        assert node.bit_size == 3
        assert node.is_struct is False
        assert node.is_union is False
        assert node.is_array is False
    
    def test_create_basic_node(self):
        """測試建立基本型別節點"""
        # Act
        node = ASTNodeFactory.create_basic_node("value", "int")
        
        # Assert
        assert node.name == "value"
        assert node.type == "int"
        assert node.is_struct is False
        assert node.is_union is False
        assert node.is_array is False
        assert node.is_bitfield is False 