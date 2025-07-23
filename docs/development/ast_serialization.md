# ASTNode Serialization API

This document describes the serialization helpers available for `ASTNode`.

## JSON serialization

`ASTNode` now provides two methods:

- `to_dict()`: convert the node (and all children) into a plain Python `dict`.
- `from_dict(data)`: class method which rebuilds an `ASTNode` tree from the
  dictionary produced by `to_dict()`.

These methods are useful when persisting AST structures in JSON format or
sending them over the network. All fields of the dataclass are preserved.

Example:

```python
node = ASTNodeFactory.create_struct_node("MyStruct")
json_data = json.dumps(node.to_dict())
restored = ASTNode.from_dict(json.loads(json_data))
```

## Binary serialization

For quick binary persistence the module exposes two helper functions:

- `dumps(node)` → `bytes`
- `loads(data)` → `ASTNode`

These wrap Python's `pickle` module and perform a simple binary round‑trip of
an `ASTNode` instance.
