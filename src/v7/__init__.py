"""
v7 模組 - 巢狀結構 AST 重構與展平優化

本模組提供 v7 版本的結構解析和展平功能，基於 v6 GUI 架構進行優化。
"""

__version__ = "7.0.0"
__author__ = "Python C Struct Converter Team"

from .ast_node import ASTNode, ASTNodeFactory
from .flattening_strategy import FlatteningStrategy, StructFlatteningStrategy, UnionFlatteningStrategy, FlattenedNode
from .parser import V7StructParser

__all__ = [
    'ASTNode',
    'ASTNodeFactory',
    'FlatteningStrategy',
    'StructFlatteningStrategy',
    'UnionFlatteningStrategy',
    'FlattenedNode',
    'V7StructParser'
] 