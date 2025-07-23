class VirtualTreeview:
    """Simplified virtualized tree widget.

    This widget only renders a window of the provided node list. Nodes must
    be provided as pre-order flattened dictionaries with an ``id`` and
    ``label``. Children are not rendered recursively – the list should
    already contain the items in the desired visual order with appropriate
    indentation information if needed.
    """
    def __init__(self, tree, page_size=100):
        self.tree = tree
        self.page_size = page_size
        self.nodes = []
        self.start = 0
        self.tree.bind("<MouseWheel>", self._on_scroll)
        self.tree.bind("<Button-4>", self._on_scroll)
        self.tree.bind("<Button-5>", self._on_scroll)

    def set_nodes(self, nodes):
        self.nodes = list(nodes)
        self.start = 0
        self._render()

    def _on_scroll(self, event):
        if event.delta > 0 or getattr(event, "num", 0) == 4:
            self.start = max(0, self.start - 1)
        else:
            self.start = min(max(0, len(self.nodes) - self.page_size),
                             self.start + 1)
        self._render()
        return "break"

    def _render(self):
        selected = set(self.tree.selection())
        self.tree.delete(*self.tree.get_children())
        end = self.start + self.page_size
        for n in self.nodes[self.start:end]:
            values = (
                n.get("name", ""),
                n.get("value", ""),
                n.get("hex_value", ""),
                n.get("hex_raw", ""),
            )
            tags = tuple(n.get("tags", []))
            self.tree.insert(
                "",
                "end",
                iid=n["id"],
                text=n.get("label", n.get("name", "")),
                values=values,
                tags=tags,
            )
        # restore selection if possible
        keep = [i for i in selected if i in self.tree.get_children()]
        if keep:
            self.tree.selection_set(keep)
