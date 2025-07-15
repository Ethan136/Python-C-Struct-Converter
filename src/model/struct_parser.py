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
    if parsed is not None:
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

    line = line.strip()
    if line.startswith("struct") and "{" in line and "}" in line:
        struct_def = parse_struct_definition_ast(line + ";")
        if struct_def:
            after = line[line.rfind("}") + 1 :].strip()
            member_name = after.split()[0] if after else None
            return MemberDef(type="struct", name=member_name, nested=struct_def)
    return None


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
    """Parse a C/C++ struct definition string."""
    struct_name, struct_content = _extract_struct_body(file_content, "struct")
    if not struct_name:
        return None, None
    struct_content = re.sub(r"//.*", "", struct_content)
    lines = struct_content.split(';')
    members = []
    for line in lines:
        parsed = parse_member_line(line)
        if parsed is not None:
            members.append(parsed)
    return struct_name, members


def parse_struct_definition_v2(file_content: str) -> Tuple[Optional[str], Optional[List[MemberDef]]]:
    """Parse a C/C++ struct definition string and return ``MemberDef`` objects."""
    struct_name, struct_content = _extract_struct_body(file_content, "struct")
    if not struct_name:
        return None, None
    struct_content = re.sub(r"//.*", "", struct_content)
    members: List[MemberDef] = []
    current = ""
    brace = 0
    for ch in struct_content:
        if ch == '{':
            brace += 1
            current += ch
        elif ch == '}':
            brace -= 1
            current += ch
        elif ch == ';' and brace == 0:
            parsed = parse_member_line_v2(current)
            if parsed is not None:
                members.append(parsed)
            current = ""
        else:
            current += ch
    if current.strip():
        parsed = parse_member_line_v2(current)
        if parsed is not None:
            members.append(parsed)
    return struct_name, members


def parse_struct_definition_ast(file_content: str) -> Optional[StructDef]:
    """Parse a struct definition and return a :class:`StructDef` object."""
    name, members = parse_struct_definition_v2(file_content)
    if not name:
        return None
    return StructDef(name=name, members=members)


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
