import warnings
from .struct_view import StructView

class StructViewV7(StructView):
    """Deprecated compatibility wrapper enabling virtualization by default."""
    def __init__(self, presenter=None, page_size=100):
        warnings.warn(
            "StructViewV7 is deprecated; use StructView with enable_virtual=True",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(presenter=presenter, enable_virtual=True, virtual_page_size=page_size)

    def _switch_to_v7_gui(self):
        self._switch_to_modern_gui()
