import pytest
from src.model.ast_node import ASTNodeFactory
from src.model.flattening_strategy import ArrayFlatteningStrategy, BitfieldFlatteningStrategy


class TestArrayFlatteningStrategy:
    def setup_method(self):
        self.factory = ASTNodeFactory()

    def test_flatten_basic_array(self):
        node = self.factory.create_array_node("arr", "int", [2])
        strategy = ArrayFlatteningStrategy()
        result = strategy.flatten_node(node)
        assert [n.name for n in result] == ["arr[0]", "arr[1]"]
        assert [n.offset for n in result] == [0, 4]

    def test_array_layout_pack_alignment(self):
        struct = self.factory.create_struct_node("Inner")
        struct.add_child(self.factory.create_basic_node("a", "char"))
        struct.add_child(self.factory.create_basic_node("b", "int"))
        array = self.factory.create_array_node("data", "struct", [2])
        array.add_child(struct)
        strategy = ArrayFlatteningStrategy(pack_alignment=1)
        layout = strategy.calculate_layout(array)
        assert layout["size"] == 10
        assert layout["alignment"] == 1


class TestBitfieldFlatteningStrategy:
    def test_basic_bitfield(self):
        factory = ASTNodeFactory()
        bf = factory.create_bitfield_node("flag", "unsigned int", 3)
        strategy = BitfieldFlatteningStrategy()
        result = strategy.flatten_node(bf)
        assert result[0].bit_size == 3
        assert result[0].bit_offset == 0
        layout = strategy.calculate_layout(bf)
        assert layout["size"] == 4
        assert layout["alignment"] == 4

