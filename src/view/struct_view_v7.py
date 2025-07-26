from .struct_view import StructView

class StructViewV7(StructView):
    """Backward-compatible wrapper enabling virtualization by default."""
    def __init__(self, presenter=None, page_size=100):
        super().__init__(presenter=presenter, enable_virtual=True, virtual_page_size=page_size)

    def _switch_to_v7_gui(self):
        self._switch_to_modern_gui()
