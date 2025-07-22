# Model Layer - Core Business Logic
# Contains data structures and business logic independent of UI

from src.model.struct_model import StructModel, parse_struct_definition, calculate_layout
from src.model.struct_parser import (
    MemberDef,
    StructDef,
    UnionDef,
    parse_member_line_v2,
    parse_struct_definition_v2,
    parse_struct_definition_ast,
    parse_c_definition,
    parse_c_definition_ast,
)
from src.model.layout import (
    LayoutCalculator,
    LayoutItem,
    BaseLayoutCalculator,
    StructLayoutCalculator,
    UnionLayoutCalculator,
)
from src.model.flattening_strategy import (
    ArrayFlatteningStrategy,
    BitfieldFlatteningStrategy,
    StructFlatteningStrategy,
    UnionFlatteningStrategy,
    FlatteningStrategy,
    FlattenedNode,
)

__all__ = [
    'StructModel',
    'parse_struct_definition',
    'calculate_layout',
    'LayoutCalculator',
    'BaseLayoutCalculator',
    'StructLayoutCalculator',
    'UnionLayoutCalculator',
    'ArrayFlatteningStrategy',
    'BitfieldFlatteningStrategy',
    'StructFlatteningStrategy',
    'UnionFlatteningStrategy',
    'FlatteningStrategy',
    'FlattenedNode',
    'LayoutItem',
    'MemberDef',
    'StructDef',
    'UnionDef',
    'parse_member_line_v2',
    'parse_struct_definition_v2',
    'parse_struct_definition_ast',
    'parse_c_definition',
    'parse_c_definition_ast',
]

