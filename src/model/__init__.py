# Model Layer - Core Business Logic
# Contains data structures and business logic independent of UI

from .struct_model import StructModel, parse_struct_definition, calculate_layout

__all__ = ['StructModel', 'parse_struct_definition', 'calculate_layout'] 