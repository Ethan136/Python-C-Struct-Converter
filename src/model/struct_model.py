"""C/C++ struct 解析與記憶體佈局計算核心模組。

提供 `parse_struct_definition`、`calculate_layout` 與 `StructModel` 等 API。
佈局結果以 :class:`model.layout.LayoutItem` dataclass 表示，可同時以屬性或
字典介面存取欄位資訊。
"""
from src.model.input_field_processor import InputFieldProcessor
from .layout import LayoutCalculator, LayoutItem, TYPE_INFO
from .struct_parser import parse_struct_definition, parse_member_line
from dataclasses import asdict




# parse_struct_definition 與 parse_member_line 已移至 ``struct_parser`` 模組，
# 於此重新匯入以維持相容性。

def _flatten_legacy_members(members, prefix=""):
    flat = []
    for m in members:
        if isinstance(m, tuple) and len(m) == 2:
            type_name, name = m
            if type_name == "struct" or type_name == "union":
                # 這裡假設 struct/union 內容已在原始 members 之後（legacy parser不保留巢狀內容，只保留型別與名稱）
                # 若要支援巢狀內容，需配合 parse_struct_definition_ast
                # 這裡僅展平名稱，型別以 struct/union 處理
                # 若有 union 內容，需額外傳入 union 內部成員
                # 這裡簡化處理，僅將名稱展平
                continue  # legacy parser無法展平巢狀內容，僅保留名稱
            else:
                flat.append({"type": type_name, "name": prefix + name if name is not None else None, "is_bitfield": False})
        elif isinstance(m, dict):
            orig_name = m.get("name")
            name = prefix + orig_name if orig_name is not None else None
            m2 = dict(m)
            m2["name"] = name
            flat.append(m2)
    return flat

def calculate_layout(members, calculator_cls=None, pack_alignment=None):
    """Calculate the memory layout using the specified calculator class. 支援 legacy union 展平。"""
    if not members:
        return [], 0, 1

    # 判斷是否為 AST 物件（MemberDef/StructDef）
    def is_ast_member(m):
        return hasattr(m, '__dataclass_fields__') and hasattr(m, 'type') and hasattr(m, 'name')

    if all(is_ast_member(m) for m in members):
        # 直接傳給 layout calculator，保留 array_dims/nested 等資訊
        calculator_cls = calculator_cls or LayoutCalculator
        layout_calculator = calculator_cls(pack_alignment=pack_alignment)
        return layout_calculator.calculate(members)
    else:
        # legacy dict/tuple 格式才展平
        flat_members = _flatten_legacy_members(members)
        calculator_cls = calculator_cls or LayoutCalculator
        layout_calculator = calculator_cls(pack_alignment=pack_alignment)
        return layout_calculator.calculate(flat_members)



import uuid

def ast_to_dict(node, parent_id=None, prefix=""):
    """遞迴將 AST 物件轉為 V2P API 規範的 dict 結構，id 保證全域唯一"""
    node_type = getattr(node, "type", None)
    if node_type is None:
        cls_name = node.__class__.__name__
        if cls_name == "StructDef":
            node_type = "struct"
        elif cls_name == "UnionDef":
            node_type = "union"
    name = getattr(node, "name", None)
    # id: parent_id.name.uuid4（保證唯一）
    base_id = f"{parent_id}.{name}" if parent_id and name else (name or str(uuid.uuid4()))
    unique_id = f"{base_id}.{uuid.uuid4().hex[:8]}"
    base = {
        "id": unique_id,
        "name": name,
        "type": node_type,
        "is_struct": node_type == "struct",
        "is_union": node_type == "union",
        "is_bitfield": getattr(node, "is_bitfield", False),
        "bit_size": getattr(node, "bit_size", None),
        "bit_offset": getattr(node, "bit_offset", None),
        "value": getattr(node, "value", None),
        "offset": getattr(node, "offset", None),
        "size": getattr(node, "size", None),
        "children": [],
    }
    # 巢狀 struct/union
    if hasattr(node, "nested") and node.nested:
        base["children"] = [ast_to_dict(child, unique_id, prefix=unique_id+".") for child in getattr(node.nested, "members", [])]
    elif hasattr(node, "members"):
        base["children"] = [ast_to_dict(child, unique_id, prefix=unique_id+".") for child in node.members]
    return base

# 展平 AST node 為 flat list（for flat mode）
def flatten_ast_nodes(ast_node):
    result = []
    def _flatten(node):
        result.append(node)
        for child in node.get("children", []):
            _flatten(child)
    _flatten(ast_node)
    return result

class StructModel:
    def __init__(self):
        self.struct_name = None
        self.members = []
        self.layout = []
        self.total_size = 0
        self.struct_align = 1
        # Initialize the input field processor
        self.input_processor = InputFieldProcessor()
        self.manual_struct = None  # 新增屬性
        self._observers = set()
        self.member_values = {}  # 新增：存放解析後的 value

    # 移除 _merge_byte_and_bit_size
    # 完全移除 _convert_legacy_member 及舊格式相容邏輯

    def add_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.discard(observer)

    def _notify_observers(self, event_type, **kwargs):
        for obs in list(self._observers):
            if hasattr(obs, "update"):
                obs.update(event_type, self, **kwargs)

    def set_manual_struct(self, members, total_size):
        # 統一格式：轉換為 C++ 標準型別格式
        self.struct_name = "MyStruct"
        self.members = self._convert_to_cpp_members(members)
        layout, self.total_size, self.struct_align = calculate_layout(self.members)
        # 將 layout 統一轉為 list of dict
        self.layout = [asdict(item) if hasattr(item, '__dataclass_fields__') else dict(item) for item in layout]
        self.manual_struct = {"members": self.members, "total_size": total_size}
        self._notify_observers("manual_struct_changed")

    def load_struct_from_file(self, file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        self.struct_content = content  # 修正：同步設置 struct_content
        struct_name, members = parse_struct_definition(content)
        if not struct_name or not members:
            raise ValueError("Could not find a valid struct definition in the file.")
        self.struct_name = struct_name
        self.members = self._convert_to_cpp_members(members)
        self.layout, self.total_size, self.struct_align = calculate_layout(self.members)
        self._notify_observers("file_struct_loaded", file_path=file_path)
        return self.struct_name, self.layout, self.total_size, self.struct_align

    def parse_hex_data(self, hex_data, byte_order, layout=None, total_size=None):
        orig_layout = self.layout
        orig_total_size = self.total_size
        if layout is not None:
            self.layout = layout
        if total_size is not None:
            self.total_size = total_size
        try:
            if not self.layout:
                raise ValueError("No struct layout loaded. Please load a struct definition first.")
            padded_hex = hex_data.zfill(self.total_size * 2)
            data_bytes = bytes.fromhex(padded_hex)
            parsed_values = []
            member_value_map = {}  # 新增
            for item in self.layout:
                if item['type'] == "padding":
                    padding_bytes = data_bytes[item['offset'] : item['offset'] + item['size']]
                    hex_value = padding_bytes.hex()
                    parsed_values.append({
                        "name": item['name'],
                        "value": "-",
                        "hex_raw": hex_value
                    })
                    continue
                offset, size, name = item['offset'], item['size'], item['name']
                member_bytes = data_bytes[offset : offset + size]
                if item.get("is_bitfield", False):
                    storage_int = int.from_bytes(member_bytes, byte_order)
                    bit_offset = item["bit_offset"]
                    bit_size = item["bit_size"]
                    mask = (1 << bit_size) - 1
                    value = (storage_int >> bit_offset) & mask
                    display_value = str(value)
                else:
                    value = int.from_bytes(member_bytes, byte_order)
                    display_value = str(bool(value)) if item['type'] == 'bool' else str(value)
                hex_value = int.from_bytes(member_bytes, 'big').to_bytes(size, 'big').hex()
                parsed_values.append({
                    "name": name,
                    "value": display_value,
                    "hex_raw": hex_value
                })
                member_value_map[name] = display_value  # 新增：存到 model
            self.member_values = member_value_map  # 新增：存到 model
            return parsed_values
        except Exception as e:
            raise
        finally:
            self.layout = orig_layout
            self.total_size = orig_total_size

    def _convert_to_cpp_members(self, members):
        """將 type/bit 欄位轉換為 C++ 標準型別（V3/V4 版本），支援 tuple 格式。"""
        new_members = []
        for m in members:
            # 支援 tuple 格式 ('type', 'name')
            if isinstance(m, tuple) and len(m) == 2 and isinstance(m[0], str) and isinstance(m[1], str):
                type_name, name = m
                m = {"type": type_name, "name": name, "bit_size": 0}
            name = m.get("name", "")
            type_name = m.get("type", "")
            bit_size = m.get("bit_size", 0)
            # 僅接受有 type 的 member
            if not type_name or type_name not in TYPE_INFO:
                continue
            if bit_size > 0:
                # bitfield
                new_members.append({
                    "type": type_name,
                    "name": name,
                    "is_bitfield": True,
                    "bit_size": bit_size
                })
            else:
                # 普通欄位
                new_members.append({
                    "type": type_name,
                    "name": name,
                    "is_bitfield": False
                })
        return new_members

    def calculate_used_bits(self, members):
        """根據 C++ 標準，bitfield 佔滿 storage unit（如 int/unsigned int 4 bytes）。"""
        used_bits = 0
        i = 0
        n = len(members)
        while i < n:
            m = members[i]
            type_name = m.get("type", "")
            bit_size = m.get("bit_size", 0)
            if type_name in TYPE_INFO:
                if bit_size > 0:
                    # 連續 bitfield group
                    storage_unit_bits = TYPE_INFO[type_name]["size"] * 8
                    group_bits = 0
                    # 收集連續同型別 bitfield
                    while i < n:
                        m2 = members[i]
                        t2 = m2.get("type", "")
                        b2 = m2.get("bit_size", 0)
                        if b2 > 0 and t2 == type_name:
                            group_bits += b2
                            i += 1
                        else:
                            break
                    # 這一組 bitfield 佔滿一個 storage unit
                    used_bits += storage_unit_bits
                    continue
                else:
                    # 普通欄位：使用 type 的 byte size * 8
                    used_bits += TYPE_INFO[type_name]["size"] * 8
            i += 1
        return used_bits

    def _validate_member_types(self, members):
        errors = []
        for m in members:
            type_name = m.get("type", "")
            bit_size = m.get("bit_size", 0)
            byte_size = m.get("byte_size", 0)
            if not type_name:
                errors.append(f"member '{m.get('name', '?')}' 必須指定型別")
            elif type_name not in TYPE_INFO:
                errors.append(f"member '{m.get('name', '?')}' 不支援的型別: {type_name}")
            if not isinstance(bit_size, int) or bit_size < 0:
                errors.append(f"member '{m.get('name', '?')}' bit_size 需為 0 或正整數")
            if bit_size > 0:
                if type_name not in ["int", "unsigned int", "char", "unsigned char"]:
                    errors.append(f"member '{m.get('name', '?')}' bitfield 只支援 int/unsigned int/char/unsigned char")
        return errors

    def _validate_member_names(self, members):
        errors = []
        names = [m["name"] for m in members if m.get("name")]
        if len(set(names)) != len(names):
            for n in set([x for x in names if names.count(x) > 1]):
                errors.append(f"成員名稱 '{n}' 重複")
        return errors

    def _validate_total_size(self, total_size):
        errors = []
        if not isinstance(total_size, int) or total_size <= 0:
            errors.append("結構體大小需為正整數")
        return errors

    def _validate_layout_size(self, members, total_size):
        errors = []
        expanded_members = self._convert_to_cpp_members(members)
        _, layout_size, _ = calculate_layout(expanded_members)
        if layout_size > total_size:
            errors.append(f"Layout 總長度 ({layout_size} bytes) 超過指定 struct 大小 ({total_size} bytes)")
        return errors

    def validate_manual_struct(self, members, total_size):
        errors = []
        errors += self._validate_member_types(members)
        errors += self._validate_member_names(members)
        errors += self._validate_total_size(total_size)
        if not errors:
            errors += self._validate_layout_size(members, total_size)
        return errors

    def calculate_manual_layout(self, members, total_size):
        # 使用 _convert_to_cpp_members 轉換為 C++ 標準型別
        expanded_members = self._convert_to_cpp_members(members)
        # 呼叫 calculate_layout 產生 C++ 標準 struct align/padding
        layout, total, align = calculate_layout(expanded_members)
        # 將 layout 統一轉為 list of dict
        layout_dicts = [asdict(item) if hasattr(item, '__dataclass_fields__') else dict(item) for item in layout]
        return layout_dicts

    def export_manual_struct_to_h(self, struct_name=None):
        """匯出手動 struct 為 C header 檔案（V4 版本）"""
        members = self.manual_struct["members"] if self.manual_struct else []
        total_size = self.manual_struct["total_size"] if self.manual_struct else 0
        struct_name = struct_name or "MyStruct"
        lines = [f"struct {struct_name} {{"]
        for m in members:
            type_name = m.get("type", "")
            name = m.get("name", None)
            bit_size = m.get("bit_size", 0)
            if bit_size > 0:
                if name is None or name == "":
                    lines.append(f"    {type_name} : {bit_size};")
                else:
                    lines.append(f"    {type_name} {name} : {bit_size};")
            else:
                if name is None or name == "":
                    lines.append(f"    {type_name};")
                else:
                    lines.append(f"    {type_name} {name};")
        lines.append("};")
        lines.append(f"// total size: {total_size} bytes")
        return "\n".join(lines)

    def get_struct_ast(self):
        """回傳符合 V2P API 的 AST dict 結構"""
        # 假設 self.ast 為 StructDef/UnionDef 物件
        if hasattr(self, 'ast') and self.ast:
            return ast_to_dict(self.ast)
        # 若無，則可用 parse_struct_definition_ast 重新解析
        if hasattr(self, 'struct_content') and self.struct_content:
            from src.model.struct_parser import parse_struct_definition_ast
            self.ast = parse_struct_definition_ast(self.struct_content)
            return ast_to_dict(self.ast)
        return None  # 修正：沒有 AST 時回傳 None

    def get_display_nodes(self, mode='tree'):
        """回傳符合 V2P API 文件的 Treeview node 結構。"""
        ast_dict = self.get_struct_ast()
        if not ast_dict:
            return []  # 修正：沒有 AST 時回傳空 list
        value_map = getattr(self, "member_values", {})  # 新增
        def to_treeview_node(node):
            label = node["name"]
            if node.get("is_struct"):
                label = f"{label} [struct]"
            elif node.get("is_union"):
                label = f"{label} [union]"
            value = value_map.get(node["name"], "")  # 新增
            # print(f"[DEBUG] to_treeview_node: name={node['name']} id={node['id']} value={value}")  # debug print
            return {
                "id": node["id"],
                "label": label,
                "type": node["type"],
                "value": value,  # 新增
                "offset": node.get("offset", ""),
                "size": node.get("size", ""),
                "children": [to_treeview_node(child) for child in node.get("children", [])],
                "icon": node.get("type"),
                "extra": {},
            }
        if mode == "tree":
            return [to_treeview_node(ast_dict)]
        elif mode == "flat":
            flat_nodes = flatten_ast_nodes(ast_dict)
            return [to_treeview_node(n) for n in flat_nodes]
        else:
            raise ValueError(f"Unknown display mode: {mode}")