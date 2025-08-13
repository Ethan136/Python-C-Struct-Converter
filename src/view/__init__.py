# View Layer - User Interface
# Contains UI components and display logic

from src.view.struct_view import StructView

# Backwards compatibility: StructViewV7 maps to wrapper class
from .struct_view_v7 import StructViewV7

__all__ = ['StructView', 'StructViewV7']
