import time
from typing import Any, Dict, List, Optional

from src.model.v7_init import (
    ASTNode,
    FlattenedNode,
    V7StructParser,
    StructFlatteningStrategy,
    FlatteningStrategy,
)


class V7Presenter:
    """Simplified presenter for the v7 AST/flattening pipeline."""

    def __init__(self, view=None):
        self.view = view
        self.ast_root: Optional[ASTNode] = None
        self.flattened_nodes: List[FlattenedNode] = []
        self.parser = V7StructParser()
        self.flattening_strategy: FlatteningStrategy = self._create_flattening_strategy()
        self.context: Dict[str, Any] = self._init_context()

    def _init_context(self) -> Dict[str, Any]:
        return {
            "display_mode": "tree",
            "expanded_nodes": ["root"],
            "selected_node": None,
            "error": None,
            "loading": False,
            "search": "",
            "filter": "",
            "highlighted_nodes": [],
            "gui_version": "v7",
            "version": "1.0",
            "extra": {},
            "last_update_time": time.time(),
        }

    def _create_flattening_strategy(self) -> FlatteningStrategy:
        return StructFlatteningStrategy()

    def load_struct_definition(self, content: str) -> bool:
        try:
            self.context["loading"] = True
            self._update_context()

            self.ast_root = self.parser.parse_struct_definition(content)
            if not self.ast_root:
                self.context["error"] = "解析失敗"
                self.context["loading"] = False
                self._update_context()
                return False

            self.flattened_nodes = self.flattening_strategy.flatten_node(self.ast_root)
            self.context["loading"] = False
            self.context["error"] = None
            self.context["last_update_time"] = time.time()
            self._update_context()
            return True
        except Exception as e:  # pragma: no cover - defensive
            self.context["error"] = str(e)
            self.context["loading"] = False
            self._update_context()
            return False

    def get_ast_tree(self) -> Optional[ASTNode]:
        return self.ast_root

    def get_flattened_layout(self) -> List[FlattenedNode]:
        return self.flattened_nodes

    def switch_display_mode(self, mode: str):
        self.context["display_mode"] = mode
        self.context["expanded_nodes"] = ["root"]
        self.context["selected_node"] = None
        self._update_context()

    def on_switch_gui_version(self, version: str):
        """Update context when the view switches GUI version."""
        self.context["gui_version"] = version
        self.context["expanded_nodes"] = ["root"]
        self.context["selected_node"] = None
        self._update_context()

    def get_display_nodes(self, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        if mode is None:
            mode = self.context.get("display_mode", "tree")
        if mode == "tree":
            nodes = self._convert_ast_to_tree_nodes()
        else:
            nodes = self._convert_flattened_to_tree_nodes()
        if self.context.get("filter"):
            nodes = self._filter_nodes(nodes, self.context["filter"])
        return nodes

    def on_search(self, term: str):
        self.context["search"] = term
        highlights: List[str] = []
        if term:
            lower = term.lower()
            def collect(n: Dict[str, Any]):
                label = n.get("label", "")
                if lower in label.lower():
                    highlights.append(n.get("id"))
                for c in n.get("children", []):
                    collect(c)
            for n in self.get_display_nodes(self.context.get("display_mode", "tree")):
                collect(n)
        self.context["highlighted_nodes"] = highlights
        self._update_context()

    def on_filter(self, term: str):
        self.context["filter"] = term
        self._update_context()

    def _filter_nodes(self, nodes: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        if not text:
            return nodes
        lower = text.lower()
        result = []
        for n in nodes:
            children = self._filter_nodes(n.get("children", []), text)
            if lower in n.get("label", "").lower() or children:
                n2 = n.copy()
                n2["children"] = children
                result.append(n2)
        return result

    # --- internal helpers -------------------------------------------------
    def _convert_ast_to_tree_nodes(self) -> List[Dict[str, Any]]:
        if not self.ast_root:
            return []
        return [self._ast_node_to_dict(self.ast_root)]

    def _ast_node_to_dict(self, node: ASTNode) -> Dict[str, Any]:
        return {
            "id": node.id,
            "label": self._generate_node_label(node),
            "type": node.type,
            "children": [self._ast_node_to_dict(c) for c in node.children],
            "icon": self._get_node_icon(node),
            "extra": self._get_node_extra(node),
        }

    def _generate_node_label(self, node: ASTNode) -> str:
        if node.is_anonymous:
            return f"(anonymous {node.type})"
        if node.is_array:
            dims = "".join(f"[{d}]" for d in node.array_dims)
            return f"{node.name}{dims}: {node.type}"
        if node.is_bitfield:
            return f"{node.name}: {node.type} : {node.bit_size}"
        return f"{node.name}: {node.type}"

    def _get_node_icon(self, node: ASTNode) -> str:
        if node.is_struct:
            return "struct"
        if node.is_union:
            return "union"
        if node.is_array:
            return "array"
        if node.is_bitfield:
            return "bitfield"
        return "field"

    def _get_node_extra(self, node: ASTNode) -> Dict[str, Any]:
        return {
            "offset": node.offset,
            "size": node.size,
            "alignment": node.alignment,
            "is_anonymous": node.is_anonymous,
        }

    def _convert_flattened_to_tree_nodes(self) -> List[Dict[str, Any]]:
        result = []
        for idx, n in enumerate(self.flattened_nodes):
            result.append({
                "id": f"flat.{idx}",
                "label": f"{n.name}: {n.type}",
                "type": n.type,
                "children": [],
                "icon": "field",
                "extra": {
                    "offset": n.offset,
                    "size": n.size,
                    "bit_size": n.bit_size,
                    "bit_offset": n.bit_offset,
                },
            })
        return result

    def _update_context(self):
        if self.view and hasattr(self.view, "update_display"):
            nodes = self.get_display_nodes(self.context.get("display_mode", "tree"))
            self.view.update_display(nodes, self.context.copy())

