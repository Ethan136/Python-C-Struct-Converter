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
    """Parses C++ struct definition from a string."""
    struct_match = re.search(r"struct\s+(\w+)\s*\{([^}]+)\};", file_content, re.DOTALL)
    if not struct_match:
        return None, None
    struct_name = struct_match.group(1)
    struct_content = struct_match.group(2)
    # 移除 // 註解
    struct_content = re.sub(r'//.*', '', struct_content)
    member_matches = re.findall(r"\s*([\w\s\*]+?)\s+([\w\[\]]+);", struct_content)
    members = []
    for type_str, name in member_matches:
        clean_type = " ".join(type_str.strip().split())
        if "*" in clean_type:
            members.append(("pointer", name))
        elif clean_type in TYPE_INFO:
            members.append((clean_type, name))
    return struct_name, members

def calculate_layout(members):
    """Calculates the memory layout of a struct, including padding."""
    if not members:
        return [], 0, 1
    layout = []
    current_offset = 0
    max_alignment = 1
    for member_type, member_name in members:
        info = TYPE_INFO[member_type]
        size, alignment = info["size"], info["align"]

        # Update struct's max alignment
        if alignment > max_alignment:
            max_alignment = alignment

        # Add padding to align the current member
        padding = (alignment - (current_offset % alignment)) % alignment
        if padding > 0:
            layout.append({
                "name": "(padding)",
                "type": "padding",
                "size": padding,
                "offset": current_offset
            })
            current_offset += padding

        # Store member layout info
        layout.append({
            "name": member_name,
            "type": member_type,
            "size": size,
            "offset": current_offset
        })

        # Move offset to the end of the current member
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
            value = int.from_bytes(member_bytes, byte_order)
            # hex_raw 一律直接顯示記憶體內容
            hex_value = member_bytes.hex()
            display_value = str(bool(value)) if item['type'] == 'bool' else str(value)
            parsed_values.append({
                "name": name,
                "value": display_value,
                "hex_raw": hex_value
            })
        return parsed_values