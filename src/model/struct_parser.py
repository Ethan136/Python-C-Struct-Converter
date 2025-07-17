"""Utilities for parsing C/C++ struct definitions."""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
from .layout import TYPE_INFO


@dataclass
class MemberDef:
    """Unified representation of a struct or union member.

    The ``name`` attribute is kept optional so future extensions can support
    anonymous bit fields that act as padding.
    """

    type: str
    name: Optional[str]
    is_bitfield: bool = False
    bit_size: int = 0
    array_dims: List[int] = field(default_factory=list)
    nested: Optional[Union["StructDef", "UnionDef"]] = None


@dataclass
class StructDef:
    """Representation of a C struct definition."""

    name: str
    members: List[MemberDef]


@dataclass
class UnionDef:
    """Representation of a C union definition."""

    name: str
    members: List[MemberDef]


def _extract_array_dims(name_token):
    """Extract array dimensions from a name token like 'arr[3][2]'."""
    match = re.match(r"(\w+)((?:\[\d+\])+)$", name_token)
    if not match:
        return name_token, []
    base = match.group(1)
    dims = [int(n) for n in re.findall(r"\[(\d+)\]", match.group(2))]
    return base, dims


def _parse_bitfield_declaration(line: str):
    """Parse a bit field declaration and return a member dict or ``None``."""
    match = re.match(r"(.+?)\s+([\w\[\]]+)\s*:\s*(\d+)$", line)
    if not match:
        return None
    type_str, name_token, bits = match.groups()
    clean_type = " ".join(type_str.strip().split())
    if "*" in clean_type:
        return None  # pointer bitfields not supported
    if clean_type not in TYPE_INFO:
        return None
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


def parse_member_line(line):
    """Parse a single struct member line.

    Returns a tuple or dict representing the member or ``None`` if the line
    is not a valid member declaration.
    """
    line = line.strip()
    if not line:
        return None

    bitfield = _parse_bitfield_declaration(line)
    if bitfield is not None:
        return bitfield

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


def parse_member_line_v2(line: str) -> Optional[MemberDef]:
    """Parse a struct member line and return a :class:`MemberDef`."""
    parsed = parse_member_line(line)
    if parsed is None:
        return None
    if isinstance(parsed, tuple):
        mtype, name = parsed
        return MemberDef(type=mtype, name=name)
    return MemberDef(
        type=parsed["type"],
        name=parsed["name"],
        is_bitfield=parsed.get("is_bitfield", False),
        bit_size=parsed.get("bit_size", 0),
        array_dims=parsed.get("array_dims", []),
    )


def _extract_struct_body(file_content, keyword="struct"):
    """Return structure name and body substring.

    The ``keyword`` argument allows reuse for future union support.
    """
    pattern = rf"{keyword}\s+(\w+)\s*\{{"
    match = re.search(pattern, file_content)
    if not match:
        return None, None
    struct_name = match.group(1)
    start = match.end()
    brace_count = 1
    i = start
    while i < len(file_content) and brace_count > 0:
        char = file_content[i]
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
        i += 1

    if brace_count != 0:
        return None, None

    struct_body = file_content[start:i - 1]
    return struct_name, struct_body


def parse_struct_definition(file_content):
    """Parse a C/C++ struct definition string，支援巢狀 struct/union。"""
    struct_name, struct_content = _extract_struct_body(file_content, "struct")
    if not struct_name:
        return None, None
    struct_content = re.sub(r"//.*", "", struct_content)
    members = []
    pos = 0
    length = len(struct_content)
    while pos < length:
        # 跳過空白與分號
        while pos < length and struct_content[pos] in ' \n\t;':
            pos += 1
        if pos >= length:
            break
        # 巢狀 struct
        if struct_content.startswith('struct', pos):
            m = re.match(r'struct\s+(\w+)\s*\{', struct_content[pos:])
            if m:
                nested_name = m.group(1)
                brace_start = pos + m.end(0) - 1
                brace_count = 1
                i = brace_start + 1
                while i < length and brace_count > 0:
                    if struct_content[i] == '{':
                        brace_count += 1
                    elif struct_content[i] == '}':
                        brace_count -= 1
                    i += 1
                if brace_count != 0:
                    break
                inner_content = struct_content[brace_start + 1:i - 1]
                j = i
                while j < length and struct_content[j] in ' \n\t':
                    j += 1
                var_match = re.match(r'(\w+)\s*;?', struct_content[j:])
                if var_match:
                    var_name = var_match.group(1)
                    # 遞迴解析巢狀 struct
                    members.append(("struct", var_name))
                    pos = j + var_match.end(0)
                    continue
        # 巢狀 union
        if struct_content.startswith('union', pos):
            m = re.match(r'union\s+(\w+)\s*\{', struct_content[pos:])
            if m:
                nested_name = m.group(1)
                brace_start = pos + m.end(0) - 1
                brace_count = 1
                i = brace_start + 1
                while i < length and brace_count > 0:
                    if struct_content[i] == '{':
                        brace_count += 1
                    elif struct_content[i] == '}':
                        brace_count -= 1
                    i += 1
                if brace_count != 0:
                    break
                inner_content = struct_content[brace_start + 1:i - 1]
                j = i
                while j < length and struct_content[j] in ' \n\t':
                    j += 1
                var_match = re.match(r'(\w+)\s*;?', struct_content[j:])
                if var_match:
                    var_name = var_match.group(1)
                    # 遞迴解析巢狀 union
                    members.append(("union", var_name))
                    pos = j + var_match.end(0)
                    continue
        # 處理一般欄位
        semi = struct_content.find(';', pos)
        if semi == -1:
            break
        line = struct_content[pos:semi].strip()
        parsed = parse_member_line(line)
        if parsed is not None:
            members.append(parsed)
        pos = semi + 1
    return struct_name, members


def parse_struct_definition_v2(file_content: str) -> Tuple[Optional[str], Optional[List[MemberDef]]]:
    """Parse a C/C++ struct definition string and return ``MemberDef`` objects."""
    struct_name, struct_content = _extract_struct_body(file_content, "struct")
    if not struct_name:
        return None, None
    struct_content = re.sub(r"//.*", "", struct_content)
    lines = struct_content.split(';')
    members: List[MemberDef] = []
    for line in lines:
        parsed = parse_member_line_v2(line)
        if parsed is not None:
            members.append(parsed)
    return struct_name, members


def parse_struct_definition_ast(file_content: str) -> Optional[StructDef]:
    """Parse a struct definition and return a :class:`StructDef` object (遞迴支援巢狀 struct/union)."""
    struct_name, struct_body = _extract_struct_body(file_content, "struct")
    if not struct_name or not struct_body:
        return None
    members = []
    pos = 0
    length = len(struct_body)
    while pos < length:
        # 跳過空白與分號
        while pos < length and struct_body[pos] in ' \n\t;':
            pos += 1
        if pos >= length:
            break
        # 嘗試解析巢狀 struct
        if struct_body.startswith('struct', pos):
            m = re.match(r'struct\s+(\w+)\s*\{', struct_body[pos:])
            if m:
                nested_name = m.group(1)
                brace_start = pos + m.end(0) - 1
                brace_count = 1
                i = brace_start + 1
                while i < length and brace_count > 0:
                    if struct_body[i] == '{':
                        brace_count += 1
                    elif struct_body[i] == '}':
                        brace_count -= 1
                    i += 1
                if brace_count != 0:
                    break
                inner_content = struct_body[brace_start + 1:i - 1]
                j = i
                while j < length and struct_body[j] in ' \n\t':
                    j += 1
                var_match = re.match(r'(\w+)\s*;?', struct_body[j:])
                if var_match:
                    var_name = var_match.group(1)
                    nested_struct = parse_struct_definition_ast(f"struct {nested_name} {{{inner_content}}};")
                    members.append(MemberDef(type="struct", name=var_name, nested=nested_struct))
                    pos = j + var_match.end(0)
                    continue
        # 嘗試解析巢狀 union
        if struct_body.startswith('union', pos):
            m = re.match(r'union\s+(\w+)\s*\{', struct_body[pos:])
            if m:
                nested_name = m.group(1)
                brace_start = pos + m.end(0) - 1
                brace_count = 1
                i = brace_start + 1
                while i < length and brace_count > 0:
                    if struct_body[i] == '{':
                        brace_count += 1
                    elif struct_body[i] == '}':
                        brace_count -= 1
                    i += 1
                if brace_count != 0:
                    break
                inner_content = struct_body[brace_start + 1:i - 1]
                j = i
                while j < length and struct_body[j] in ' \n\t':
                    j += 1
                var_match = re.match(r'(\w+)\s*;?', struct_body[j:])
                if var_match:
                    var_name = var_match.group(1)
                    # 遞迴解析 union 內容
                    union_members = []
                    union_lines = inner_content.split(';')
                    for line in union_lines:
                        parsed = parse_member_line_v2(line)
                        if parsed is not None:
                            union_members.append(parsed)
                    nested_union = UnionDef(name=nested_name, members=union_members)
                    members.append(MemberDef(type="union", name=var_name, nested=nested_union))
                    pos = j + var_match.end(0)
                    continue
        # 處理一般欄位
        semi = struct_body.find(';', pos)
        if semi == -1:
            break
        line = struct_body[pos:semi].strip()
        parsed = parse_member_line_v2(line)
        if parsed is not None:
            members.append(parsed)
        pos = semi + 1
    return StructDef(name=struct_name, members=members)


def parse_c_definition(file_content: str) -> Tuple[Optional[str], Optional[str], Optional[List[dict]]]:
    """Parse a C structure or union definition.

    Union parsing is not yet implemented, so this function currently
    only recognizes ``struct`` definitions.
    """
    name, members = parse_struct_definition(file_content)
    if name is None:
        return None, None, None
    return "struct", name, members


def parse_c_definition_ast(file_content: str) -> Optional[Union[StructDef, UnionDef]]:
    """Parse a C struct or union and return a definition object.

    Union support is not yet implemented and will return ``None`` if a union
    definition is encountered.
    """
    return parse_struct_definition_ast(file_content)
