"""Utilities for parsing C/C++ struct definitions."""
import re
from .layout import TYPE_INFO


def _extract_array_dims(name_token):
    """Extract array dimensions from a name token like 'arr[3][2]'."""
    match = re.match(r"(\w+)((?:\[\d+\])+)$", name_token)
    if not match:
        return name_token, []
    base = match.group(1)
    dims = [int(n) for n in re.findall(r"\[(\d+)\]", match.group(2))]
    return base, dims


def parse_member_line(line):
    """Parse a single struct member line.

    Returns a tuple or dict representing the member or ``None`` if the line
    is not a valid member declaration.
    """
    line = line.strip()
    if not line:
        return None

    bitfield_match = re.match(r"(.+?)\s+([\w\[\]]+)\s*:\s*(\d+)$", line)
    if bitfield_match:
        type_str, name_token, bits = bitfield_match.groups()
        clean_type = " ".join(type_str.strip().split())
        if "*" in clean_type:
            return None  # pointer bitfields not supported
        if clean_type in TYPE_INFO:
            name, dims = _extract_array_dims(name_token)
            member = {
                "type": clean_type,
                "name": name,
                "is_bitfield": True,
                "bit_size": int(bits),
            }
            if dims:
                member["array_dims"] = dims
            return member
        return None

    member_match = re.match(r"(.+?)\s+([\w\[\]]+)$", line)
    if member_match:
        type_str, name_token = member_match.groups()
        clean_type = " ".join(type_str.strip().split())
        name, dims = _extract_array_dims(name_token)
        if "*" in clean_type:
            return ("pointer", name)
        if clean_type in TYPE_INFO:
            if dims:
                return {"type": clean_type, "name": name, "array_dims": dims}
            return (clean_type, name)
    return None


def parse_struct_definition(file_content):
    """Parse a C/C++ struct definition string."""
    struct_match = re.search(r"struct\s+(\w+)\s*\{([^}]+)\};", file_content, re.DOTALL)
    if not struct_match:
        return None, None
    struct_name = struct_match.group(1)
    struct_content = struct_match.group(2)
    struct_content = re.sub(r"//.*", "", struct_content)
    lines = struct_content.split(';')
    members = []
    for line in lines:
        parsed = parse_member_line(line)
        if parsed is not None:
            members.append(parsed)
    return struct_name, members
