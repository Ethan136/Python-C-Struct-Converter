"""
struct_model.py

C/C++ struct 解析與記憶體佈局計算核心模組。
支援 struct 欄位型別：char, int, long long, unsigned, pointer, 以及 bit field (type name : bits)。
支援自動計算 padding、alignment、bitfield packing（同 storage unit 內連續 bitfield）。
主要 API:
- parse_struct_definition: 解析 struct 定義，回傳 struct 名稱與欄位 members（含 bitfield 資訊）。
- calculate_layout: 根據 members 計算記憶體佈局，回傳 layout list（含 offset, size, is_bitfield, bit_offset, bit_size）。
- StructModel: struct 解析與 hex 資料解析高階介面。

layout 內每個欄位 dict 格式：
{
  "name": 欄位名稱,
  "type": 型別,
  "size": 占用 bytes 數,
  "offset": 在 struct 內的 byte offset,
  "is_bitfield": 是否為 bitfield 欄位 (bool, optional),
  "bit_offset": 若為 bitfield，於 storage unit 內的 bit offset (int, optional),
  "bit_size": 若為 bitfield，bitfield 欄位寬度 (int, optional)
}
"""
import re
from .input_field_processor import InputFieldProcessor

# Based on a common 64-bit system (like GCC on x86-64)
TYPE_INFO = {
    "char":               {"size": 1, "align": 1},
    "signed char":        {"size": 1, "align": 1},
    "unsigned char":      {"size": 1, "align": 1},
    "bool":               {"size": 1, "align": 1},
    "short":              {"size": 2, "align": 2},
    "unsigned short":     {"size": 2, "align": 2},
    "int":                {"size": 4, "align": 4},
    "unsigned int":       {"size": 4, "align": 4},
    "long":               {"size": 8, "align": 8}, # Common on 64-bit Linux/macOS
    "unsigned long":      {"size": 8, "align": 8},
    "long long":          {"size": 8, "align": 8},
    "unsigned long long": {"size": 8, "align": 8},
    "float":              {"size": 4, "align": 4},
    "double":             {"size": 8, "align": 8},
    "pointer":            {"size": 8, "align": 8} # Generic for all pointer types
}

def parse_struct_definition(file_content):
    """Parses C++ struct definition from a string, including bit fields, preserving field order."""
    struct_match = re.search(r"struct\s+(\w+)\s*\{([^}]+)\};", file_content, re.DOTALL)
    if not struct_match:
        return None, None
    struct_name = struct_match.group(1)
    struct_content = struct_match.group(2)
    # 移除 // 註解
    struct_content = re.sub(r'//.*', '', struct_content)
    # 逐行解析，保留順序
    lines = struct_content.split(';')
    members = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # bitfield: type name : bits
        bitfield_match = re.match(r"(.+?)\s+([\w\[\]]+)\s*:\s*(\d+)$", line)
        if bitfield_match:
            type_str, name, bits = bitfield_match.groups()
            clean_type = " ".join(type_str.strip().split())
            if "*" in clean_type:
                continue  # 不支援 pointer bit field
            if clean_type in TYPE_INFO:
                members.append({
                    "type": clean_type,
                    "name": name,
                    "is_bitfield": True,
                    "bit_size": int(bits)
                })
            continue
        # 普通欄位: type name
        member_match = re.match(r"(.+?)\s+([\w\[\]]+)$", line)
        if member_match:
            type_str, name = member_match.groups()
            clean_type = " ".join(type_str.strip().split())
            if "*" in clean_type:
                members.append(("pointer", name))
            elif clean_type in TYPE_INFO:
                members.append((clean_type, name))
    return struct_name, members

def calculate_layout(members):
    """Calculates the memory layout of a struct, including padding and bit fields."""
    if not members:
        return [], 0, 1
    
    layout_calculator = LayoutCalculator()
    return layout_calculator.calculate(members)


class LayoutCalculator:
    """Helper class for calculating struct memory layout."""
    
    def __init__(self):
        self.layout = []
        self.current_offset = 0
        self.max_alignment = 1
        self.bitfield_unit_type = None
        self.bitfield_unit_size = 0
        self.bitfield_unit_align = 0
        self.bitfield_bit_offset = 0
        self.bitfield_unit_offset = 0
    
    def calculate(self, members):
        """Calculate the complete memory layout for the struct."""
        for member in members:
            if isinstance(member, dict) and member.get("is_bitfield", False):
                self._process_bitfield_member(member)
            else:
                self._process_regular_member(member)
        
        self._add_final_padding()
        return self.layout, self.current_offset, self.max_alignment
    
    def _process_bitfield_member(self, member):
        """Process a bitfield member."""
        mtype = member["type"]
        mname = member["name"]
        mbit_size = member["bit_size"]
        info = TYPE_INFO[mtype]
        size, alignment = info["size"], info["align"]
        
        if self._needs_new_bitfield_unit(mtype, mbit_size):
            self._start_new_bitfield_unit(mtype, size, alignment)
        
        self._add_bitfield_to_layout(mname, mtype, mbit_size)
        self.bitfield_bit_offset += mbit_size
    
    def _process_regular_member(self, member):
        """Process a regular (non-bitfield) member."""
        # End any open bitfield unit
        self.bitfield_unit_type = None
        self.bitfield_bit_offset = 0
        
        # Handle both tuple and dict formats for backward compatibility
        if isinstance(member, tuple):
            member_type, member_name = member
        elif isinstance(member, dict):
            member_type = member["type"]
            member_name = member["name"]
        else:
            raise ValueError(f"Invalid member format: {member}")
        
        info = TYPE_INFO[member_type]
        size, alignment = info["size"], info["align"]
        
        if alignment > self.max_alignment:
            self.max_alignment = alignment
        
        self._add_padding_if_needed(alignment)
        self._add_member_to_layout(member_name, member_type, size)
        self.current_offset += size
    
    def _needs_new_bitfield_unit(self, mtype, mbit_size):
        """Check if a new bitfield storage unit is needed."""
        return (self.bitfield_unit_type != mtype or 
                self.bitfield_bit_offset + mbit_size > self.bitfield_unit_size * 8)
    
    def _start_new_bitfield_unit(self, mtype, size, alignment):
        """Start a new bitfield storage unit."""
        self._add_padding_if_needed(alignment)
        self.bitfield_unit_type = mtype
        self.bitfield_unit_size = size
        self.bitfield_unit_align = alignment
        self.bitfield_bit_offset = 0
        self.bitfield_unit_offset = self.current_offset
        
        if alignment > self.max_alignment:
            self.max_alignment = alignment
        
        self.current_offset += size
    
    def _add_bitfield_to_layout(self, name, mtype, bit_size):
        """Add a bitfield member to the layout."""
        self.layout.append({
            "name": name,
            "type": mtype,
            "size": self.bitfield_unit_size,
            "offset": self.bitfield_unit_offset,
            "is_bitfield": True,
            "bit_offset": self.bitfield_bit_offset,
            "bit_size": bit_size
        })
    
    def _add_member_to_layout(self, name, member_type, size):
        """Add a regular member to the layout."""
        self.layout.append({
            "name": name,
            "type": member_type,
            "size": size,
            "offset": self.current_offset,
            "is_bitfield": False,
            "bit_offset": 0,
            "bit_size": size * 8
        })
    
    def _add_padding_if_needed(self, alignment):
        """Add padding if needed to meet alignment requirements."""
        padding = (alignment - (self.current_offset % alignment)) % alignment
        if padding > 0:
            self.layout.append({
                "name": "(padding)",
                "type": "padding",
                "size": padding,
                "offset": self.current_offset,
                "is_bitfield": False,
                "bit_offset": 0,
                "bit_size": padding * 8
            })
            self.current_offset += padding
    
    def _add_final_padding(self):
        """Add final padding to align the whole struct."""
        final_padding = (self.max_alignment - (self.current_offset % self.max_alignment)) % self.max_alignment
        if final_padding > 0:
            self.layout.append({
                "name": "(final padding)",
                "type": "padding",
                "size": final_padding,
                "offset": self.current_offset,
                "is_bitfield": False,
                "bit_offset": 0,
                "bit_size": final_padding * 8
            })
            self.current_offset += final_padding

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

    def _merge_byte_and_bit_size(self, members):
        """
        將所有 member 做合併：只要 bit_size > 0，則 new_bit_size = byte_size*8 + bit_size，byte_size=0。
        """
        merged = []
        for m in members:
            # 兼容舊格式: 若只有 length，轉為 bit_size
            if "length" in m and "bit_size" not in m and "byte_size" not in m:
                merged.append({
                    "name": m["name"],
                    "byte_size": 0,
                    "bit_size": m["length"]
                })
                continue
            byte_size = m.get("byte_size", 0)
            bit_size = m.get("bit_size", 0)
            if bit_size > 0:
                merged.append({
                    "name": m["name"],
                    "byte_size": 0,
                    "bit_size": byte_size * 8 + bit_size
                })
            elif byte_size > 0:
                merged.append({
                    "name": m["name"],
                    "byte_size": byte_size,
                    "bit_size": 0
                })
            # byte_size=0 且 bit_size=0 的 member 直接略過
        return merged

    def set_manual_struct(self, members, total_size):
        # 先合併 byte/bit size
        new_members = self._merge_byte_and_bit_size(members)
        self.manual_struct = {"members": new_members, "total_size": total_size}

    def load_struct_from_file(self, file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        struct_name, members = parse_struct_definition(content)
        if not struct_name or not members:
            raise ValueError("Could not find a valid struct definition in the file.")
        
        self.struct_name = struct_name
        self.members = members
        self.layout, self.total_size, self.struct_align = calculate_layout(members)
        return self.struct_name, self.layout, self.total_size, self.struct_align

    def parse_hex_data(self, hex_data, byte_order):
        if not self.layout:
            raise ValueError("No struct layout loaded. Please load a struct definition first.")

        # Use the input field processor to handle the complete hex data
        # For the entire struct, we need to pad to the total size
        padded_hex = self.input_processor.pad_hex_input(hex_data, self.total_size)
        data_bytes = bytes.fromhex(padded_hex)
        
        parsed_values = []
        for item in self.layout:
            # Only parse actual members, skip padding entries
            if item['type'] == "padding":
                # For padding, hex_raw should reflect the actual memory layout without endianness
                padding_bytes = data_bytes[item['offset'] : item['offset'] + item['size']]
                hex_value = padding_bytes.hex()
                parsed_values.append({
                    "name": item['name'],
                    "value": "-", # No value for padding
                    "hex_raw": hex_value
                })
                continue

            offset, size, name = item['offset'], item['size'], item['name']
            member_bytes = data_bytes[offset : offset + size]
            if item.get("is_bitfield", False):
                # Extract the storage unit as int
                storage_int = int.from_bytes(member_bytes, byte_order)
                bit_offset = item["bit_offset"]
                bit_size = item["bit_size"]
                mask = (1 << bit_size) - 1
                value = (storage_int >> bit_offset) & mask
                display_value = str(value)
            else:
                value = int.from_bytes(member_bytes, byte_order)
                display_value = str(bool(value)) if item['type'] == 'bool' else str(value)
            # hex_raw 一律用 big endian 顯示
            hex_value = int.from_bytes(member_bytes, 'big').to_bytes(size, 'big').hex()
            parsed_values.append({
                "name": name,
                "value": display_value,
                "hex_raw": hex_value
            })
        return parsed_values

    def validate_manual_struct(self, members, total_size):
        # 先對原始 members 做型別與正整數驗證
        errors = []
        for m in members:
            if not isinstance(m.get("byte_size", 0), int) or m.get("byte_size", 0) < 0:
                errors.append(f"member '{m.get('name', '?')}' byte_size 需為 0 或正整數")
            if not isinstance(m.get("bit_size", 0), int) or m.get("bit_size", 0) < 0:
                errors.append(f"member '{m.get('name', '?')}' bit_size 需為 0 或正整數")
        # 其餘驗證仍用合併後的 members
        new_members = self._merge_byte_and_bit_size(members)
        names = [m["name"] for m in new_members]
        if len(set(names)) != len(names):
            for n in set([x for x in names if names.count(x) > 1]):
                errors.append(f"成員名稱 '{n}' 重複")
        if not isinstance(total_size, int) or total_size <= 0:
            errors.append("結構體大小需為正整數")
        # layout 驗證
        if not errors:
            layout = self.calculate_manual_layout(members, total_size)
            # 取得 layout 計算出來的 struct 大小
            from src.model.struct_model import calculate_layout
            expanded_members = self._convert_to_cpp_members(members)
            _, layout_size, _ = calculate_layout(expanded_members)
            if layout_size > total_size:
                errors.append(f"Layout 總長度 ({layout_size} bytes) 超過指定 struct 大小 ({total_size} bytes)")
        return errors

    def _convert_to_cpp_members(self, members):
        """將 byte/bit 欄位轉換為 C++ 標準型別"""
        def infer_type(byte_size, bit_size):
            if bit_size > 0:
                # bitfield，預設用 unsigned int
                return {"type": "unsigned int", "name": "", "is_bitfield": True, "bit_size": bit_size}
            if byte_size == 1:
                return {"type": "char", "name": ""}
            elif byte_size == 2:
                return {"type": "short", "name": ""}
            elif byte_size == 4:
                return {"type": "int", "name": ""}
            elif byte_size == 8:
                return {"type": "long long", "name": ""}
            elif byte_size > 0:
                # 其他大小用 unsigned char 陣列
                return {"type": "unsigned char", "name": "", "array_size": byte_size}
            else:
                return None

        new_members = []
        for m in members:
            name = m.get("name", "")
            byte_size = m.get("byte_size", 0)
            bit_size = m.get("bit_size", 0)
            t = infer_type(byte_size, bit_size)
            if t is None:
                continue
            t["name"] = name
            if t.get("is_bitfield"):
                t["bit_size"] = bit_size
            if "array_size" in t:
                t["array_size"] = t["array_size"]
            new_members.append(t)

        # 將 array_size 轉成多個 char 欄位
        expanded_members = []
        for m in new_members:
            if m.get("type") == "unsigned char" and m.get("array_size", 0) > 0:
                for i in range(m["array_size"]):
                    expanded_members.append({"type": "unsigned char", "name": f"{m['name']}_{i}"})
            else:
                expanded_members.append(m)

        return expanded_members

    def calculate_manual_layout(self, members, total_size):
        # 使用 _convert_to_cpp_members 轉換為 C++ 標準型別
        expanded_members = self._convert_to_cpp_members(members)
        # 呼叫 calculate_layout 產生 C++ 標準 struct align/padding
        layout, total, align = calculate_layout(expanded_members)
        return layout

    def export_manual_struct_to_h(self, struct_name=None):
        members = self.manual_struct["members"] if self.manual_struct else []
        total_size = self.manual_struct["total_size"] if self.manual_struct else 0
        struct_name = struct_name or "MyStruct"
        lines = [f"struct {struct_name} {{"]
        for m in members:
            if m["bit_size"] > 0:
                lines.append(f"    unsigned int {m['name']} : {m['bit_size']};")
            elif m["byte_size"] > 0:
                lines.append(f"    unsigned char {m['name']}[%d];" % m['byte_size'])
        lines.append("};")
        lines.append(f"// total size: {total_size} bytes")
        return "\n".join(lines)