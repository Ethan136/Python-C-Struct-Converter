import json
import sys
import types

# Provide a stub for jsonschema to avoid dependency issues when importing the src package
sys.modules.setdefault("jsonschema", types.ModuleType("jsonschema"))

from src.model.ast_node import ASTNode, ASTNodeFactory, dumps, loads


def _build_sample() -> ASTNode:
    root = ASTNodeFactory.create_struct_node("Root")
    child = ASTNodeFactory.create_basic_node("value", "int")
    root.add_child(child)
    return root


def test_dict_round_trip():
    node = _build_sample()
    data = node.to_dict()
    restored = ASTNode.from_dict(data)
    assert restored.to_dict() == data


def test_binary_round_trip():
    node = _build_sample()
    b = dumps(node)
    restored = loads(b)
    assert isinstance(restored, ASTNode)
    assert restored.to_dict() == node.to_dict()
