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
        # 刪除非選取中的既有節點，保留選中的節點（即使不在當前頁面）
        existing = set(self.tree.get_children())
        for item in list(existing):
            if item not in selected:
                self.tree.delete(item)
        # 插入當前頁面節點
        end = self.start + self.page_size
        window = self.nodes[self.start:end]
        for n in window:
            iid = n["id"]
            if iid not in set(self.tree.get_children()):
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
                    iid=iid,
                    text=n.get("label", n.get("name", "")),
                    values=values,
                    tags=tags,
                )
        # 重新設置選取狀態（若選取節點仍存在）
        if selected:
            keep = [i for i in selected if i in self.tree.get_children("")]
            if keep:
                self.tree.selection_set(keep)

    def get_global_index(self, iid):
        """Return the index of ``iid`` within the full node list."""
        for idx, n in enumerate(self.nodes):
            if n.get("id") == iid:
                return idx
        return -1

    def reorder_nodes(self, parent_id, from_idx, to_idx):
        """Move node from ``from_idx`` to ``to_idx`` and re-render."""
        if from_idx < 0 or from_idx >= len(self.nodes):
            return
        if to_idx < 0 or to_idx >= len(self.nodes):
            return
        node = self.nodes.pop(from_idx)
        self.nodes.insert(to_idx, node)
        self._render()
