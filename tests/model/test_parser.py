"""
v7 解析器測試

測試 V7StructParser 的功能。
"""

import pytest
from src.model.parser import V7StructParser
from src.model.ast_node import ASTNode, ASTNodeFactory


class TestV7StructParser:
    """v7 解析器測試"""
    
    def setup_method(self):
        """測試前準備"""
        self.parser = V7StructParser()
        self.factory = ASTNodeFactory()
    
    def test_parse_simple_struct(self):
        """測試簡單結構解析"""
        # Arrange
        content = """
        struct Simple {
            int x;
            char y;
        };
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "Simple"
        assert result.type == "struct"
        assert result.is_struct is True
        assert len(result.children) == 2
        
        # 檢查第一個成員
        assert result.children[0].name == "x"
        assert result.children[0].type == "int"
        assert result.children[0].is_struct is False
        assert result.children[0].is_union is False
        assert result.children[0].is_array is False
        
        # 檢查第二個成員
        assert result.children[1].name == "y"
        assert result.children[1].type == "char"
    
    def test_parse_nested_struct(self):
        """測試巢狀結構解析"""
        # Arrange
        content = """
        struct Outer {
            struct Inner {
                int x;
                char y;
            } inner;
            int z;
        };
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "Outer"
        assert len(result.children) == 2
        
        # 檢查巢狀結構
        inner = result.children[0]
        assert inner.name == "inner"
        assert inner.type == "struct"
        assert inner.is_struct is True
        assert len(inner.children) == 2
        
        # 檢查巢狀結構的成員
        assert inner.children[0].name == "x"
        assert inner.children[0].type == "int"
        assert inner.children[1].name == "y"
        assert inner.children[1].type == "char"
        
        # 檢查外部結構的成員
        assert result.children[1].name == "z"
        assert result.children[1].type == "int"
    
    def test_parse_anonymous_struct(self):
        """測試匿名結構解析"""
        # Arrange
        content = """
        struct Outer {
            struct {
                int x;
                char y;
            } anonymous;
            int z;
        };
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "Outer"
        assert len(result.children) == 2
        
        # 檢查匿名結構
        anonymous = result.children[0]
        assert anonymous.name == "anonymous"
        assert anonymous.type == "struct"
        assert anonymous.is_struct is True
        assert len(anonymous.children) == 2
        
        # 匿名結構的成員應該有正確的名稱
        assert anonymous.children[0].name == "x"
        assert anonymous.children[1].name == "y"
    
    def test_parse_array_member(self):
        """測試陣列成員解析"""
        # Arrange
        content = """
        struct ArrayTest {
            int arr[2][3];
            char str[10];
        };
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "ArrayTest"
        assert len(result.children) == 2
        
        # 檢查多維陣列
        arr = result.children[0]
        assert arr.name == "arr"
        assert arr.type == "int"
        assert arr.is_array is True
        assert arr.array_dims == [2, 3]
        
        # 檢查字串陣列
        str_arr = result.children[1]
        assert str_arr.name == "str"
        assert str_arr.type == "char"
        assert str_arr.is_array is True
        assert str_arr.array_dims == [10]
    
    def test_parse_union_member(self):
        """測試 union 成員解析"""
        # Arrange
        content = """
        struct UnionTest {
            union {
                int x;
                char y;
            } u;
            int z;
        };
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "UnionTest"
        assert len(result.children) == 2
        
        # 檢查 union
        union = result.children[0]
        assert union.name == "u"
        assert union.type == "union"
        assert union.is_union is True
        assert len(union.children) == 2
        
        # 檢查 union 成員
        assert union.children[0].name == "x"
        assert union.children[0].type == "int"
        assert union.children[1].name == "y"
        assert union.children[1].type == "char"
    
    def test_parse_bitfield_member(self):
        """測試位元欄位成員解析"""
        # Arrange
        content = """
        struct BitfieldTest {
            unsigned int flags : 3;
            unsigned int : 2;
            unsigned int value : 5;
        };
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "BitfieldTest"
        assert len(result.children) == 3
        
        # 檢查有名位元欄位
        flags = result.children[0]
        assert flags.name == "flags"
        assert flags.type == "unsigned int"
        assert flags.is_bitfield is True
        assert flags.bit_size == 3
        
        # 檢查匿名位元欄位
        anonymous = result.children[1]
        assert anonymous.name == ""
        assert anonymous.type == "unsigned int"
        assert anonymous.is_bitfield is True
        assert anonymous.bit_size == 2
        assert anonymous.is_anonymous is True
        
        # 檢查第二個有名位元欄位
        value = result.children[2]
        assert value.name == "value"
        assert value.type == "unsigned int"
        assert value.is_bitfield is True
        assert value.bit_size == 5
    
    def test_parse_complex_nested_structure(self):
        """測試複雜巢狀結構解析"""
        # Arrange
        content = """
        struct Complex {
            struct {
                int x;
                char y;
            } anonymous;
            union {
                int a;
                struct {
                    unsigned int b1 : 3;
                    unsigned int : 2;
                    unsigned int b2 : 5;
                } bits;
            } u;
            int arr[2][3];
        };
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "Complex"
        assert len(result.children) == 3
        
        # 檢查匿名結構
        anonymous = result.children[0]
        assert anonymous.name == "anonymous"
        assert anonymous.is_struct is True
        assert len(anonymous.children) == 2
        
        # 檢查 union
        union = result.children[1]
        assert union.name == "u"
        assert union.is_union is True
        assert len(union.children) == 2
        
        # 檢查 union 中的巢狀結構
        bits = union.children[1]
        assert bits.name == "bits"
        assert bits.is_struct is True
        assert len(bits.children) == 3
        
        # 檢查陣列
        arr = result.children[2]
        assert arr.name == "arr"
        assert arr.is_array is True
        assert arr.array_dims == [2, 3]
    
    def test_parse_invalid_content(self):
        """測試無效內容解析"""
        # Arrange
        invalid_contents = [
            "",  # 空內容
            "not a struct",  # 不是結構
            "struct {",  # 不完整的結構
            "struct Test { int x;",  # 缺少結束大括號
        ]
        
        for content in invalid_contents:
            # Act
            result = self.parser.parse_struct_definition(content)
            
            # Assert
            assert result is None
    
    def test_parse_with_comments(self):
        """測試帶註解的解析"""
        # Arrange
        content = """
        // 這是一個測試結構
        struct CommentTest {
            int x;  // 第一個成員
            char y; /* 第二個成員 */
        };
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "CommentTest"
        assert len(result.children) == 2
        assert result.children[0].name == "x"
        assert result.children[1].name == "y"
    
    def test_parse_with_whitespace(self):
        """測試帶空白的解析"""
        # Arrange
        content = """
        struct   WhitespaceTest   {
            int    x   ;
            char   y   ;
        }   ;
        """
        
        # Act
        result = self.parser.parse_struct_definition(content)
        
        # Assert
        assert result is not None
        assert result.name == "WhitespaceTest"
        assert len(result.children) == 2
        assert result.children[0].name == "x"
        assert result.children[1].name == "y"

    def test_parse_nested_struct_array(self):
        """巢狀結構陣列解析"""
        content = """
        struct SA {
            struct { int x; } arr[2][2];
        };
        """

        result = self.parser.parse_struct_definition(content)

        assert result is not None
        arr = result.children[0]
        assert arr.name == "arr"
        assert arr.is_array is True
        assert arr.array_dims == [2, 2]
        assert arr.children[0].is_struct is True
        assert arr.children[0].children[0].name == "x"

    def test_parse_nested_union_array(self):
        """巢狀聯合陣列解析"""
        content = """
        struct UA {
            union { int a; char b; } u[3];
        };
        """

        result = self.parser.parse_struct_definition(content)

        assert result is not None
        u = result.children[0]
        assert u.name == "u"
        assert u.is_array is True
        assert u.array_dims == [3]
        assert u.children[0].is_union is True
        assert len(u.children[0].children) == 2