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
    layout = []
    current_offset = 0
    max_alignment = 1
    bitfield_unit_type = None
    bitfield_unit_size = 0
    bitfield_unit_align = 0
    bitfield_bit_offset = 0
    bitfield_unit_offset = 0
    for member in members:
        # Bit field member (dict)
        if isinstance(member, dict) and member.get("is_bitfield", False):
            mtype = member["type"]
            mname = member["name"]
            mbit_size = member["bit_size"]
            info = TYPE_INFO[mtype]
            size, alignment = info["size"], info["align"]
            if bitfield_unit_type != mtype or bitfield_bit_offset + mbit_size > size * 8:
                # New storage unit needed (type changed or overflow)
                # Align to storage unit
                padding = (alignment - (current_offset % alignment)) % alignment
                if padding > 0:
                    layout.append({
                        "name": "(padding)",
                        "type": "padding",
                        "size": padding,
                        "offset": current_offset
                    })
                    current_offset += padding
                bitfield_unit_type = mtype
                bitfield_unit_size = size
                bitfield_unit_align = alignment
                bitfield_bit_offset = 0
                bitfield_unit_offset = current_offset
                # Update struct's max alignment
                if alignment > max_alignment:
                    max_alignment = alignment
                current_offset += size
            layout.append({
                "name": mname,
                "type": mtype,
                "size": bitfield_unit_size,
                "offset": bitfield_unit_offset,
                "is_bitfield": True,
                "bit_offset": bitfield_bit_offset,
                "bit_size": mbit_size
            })
            bitfield_bit_offset += mbit_size
        else:
            # End any open bitfield unit
            bitfield_unit_type = None
            bitfield_bit_offset = 0
            # Old tuple logic
            member_type, member_name = member
            info = TYPE_INFO[member_type]
            size, alignment = info["size"], info["align"]
            if alignment > max_alignment:
                max_alignment = alignment
            padding = (alignment - (current_offset % alignment)) % alignment
            if padding > 0:
                layout.append({
                    "name": "(padding)",
                    "type": "padding",
                    "size": padding,
                    "offset": current_offset
                })
                current_offset += padding
            layout.append({
                "name": member_name,
                "type": member_type,
                "size": size,
                "offset": current_offset
            })
            current_offset += size
    # Add final padding to align the whole struct
    final_padding = (max_alignment - (current_offset % max_alignment)) % max_alignment
    if final_padding > 0:
        layout.append({
            "name": "(final padding)",
            "type": "padding",
            "size": final_padding,
            "offset": current_offset
        })
        current_offset += final_padding
    total_size = current_offset
    return layout, total_size, max_alignment

class StructModel:
    def __init__(self):
        self.struct_name = None
        self.members = []
        self.layout = []
        self.total_size = 0
        self.struct_align = 1
        # Initialize the input field processor
        self.input_processor = InputFieldProcessor()

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