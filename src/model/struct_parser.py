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
    # 先檢查匿名 bitfield（無名稱），避免把 'unsigned int   : 2' 誤判為具名形式
    match_anon = re.match(r"^(?:unsigned\s+int|int|char|unsigned\s+char)\s*:\s*(\d+)$", line)
    if match_anon:
        bits = match_anon.group(1)
        # 從開頭擷取型別字串（去除尾端 ': digits'）
        type_str = line.split(':', 1)[0]
        clean_type = " ".join(type_str.strip().split())
        if "*" in clean_type:
            return None
        if clean_type not in TYPE_INFO:
            return None
        return {
            "type": clean_type,
            "name": None,
            "is_bitfield": True,
            "bit_size": int(bits),
        }
    # 具名 bitfield: 'unsigned int b1 : 3'
    match = re.match(r"^(.+?)\s+([\w\[\]]+)\s*:\s*(\d+)$", line)
    if match:
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
    return None


def _split_member_lines(body: str):
    """Split struct/union body into member lines respecting nested braces."""
    lines = []
    current = ""
    brace = 0
    for ch in body:
        if ch == '{':
            brace += 1
        elif ch == '}':
            brace -= 1
        if ch == ';' and brace == 0:
            current += ch
            lines.append(current.strip().rstrip(';').strip())
            current = ""
            continue
        current += ch
    if current.strip():
        lines.append(current.strip())
    return lines


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
        # 將自訂簡寫型別（U8/U16/U32/U64）映射為對應無號型別，便於後續處理
        alias_map = {
            "U8": "unsigned char",
            "U16": "unsigned short",
            "U32": "unsigned int",
            "U64": "unsigned long long",
        }
        if clean_type in alias_map:
            clean_type = alias_map[clean_type]
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
        name=parsed.get("name", None),
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
    import re
    struct_body = re.sub(r"//.*", "", struct_body)  # 修正：先移除所有 // 註解
    # print("DEBUG struct_body:", repr(struct_body))
    members = []
    pos = 0
    length = len(struct_body)
    while pos < length:
        # 跳過空白與分號
        while pos < length and struct_body[pos] in ' \n\t;':
            pos += 1
        if pos >= length:
            break

        # 先嘗試解析 union/struct 宣告（含匿名與陣列）
        if struct_body.startswith('union', pos) or struct_body.startswith('struct', pos):
            kind = 'union' if struct_body.startswith('union', pos) else 'struct'
            m = re.match(rf'{kind}\s+(\w+)\s*\{{', struct_body[pos:])
            anon = False
            nested_name = None
            if not m:
                # 可能是匿名類型，如 union { ... }
                m = re.match(rf'{kind}\s*\{{', struct_body[pos:])
                anon = True
            if m:
                nested_name = m.group(1) if len(m.groups()) > 0 else None
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
                # 取得變數名稱 (含陣列)
                var_match = re.match(r'(\w+(?:\[\d+\])*)\s*;?', struct_body[j:])
                # 解析內部成員
                nested_members = []
                for line in _split_member_lines(inner_content):
                    line = line.strip()
                    if line.startswith('struct') or line.startswith('union'):
                        temp = parse_struct_definition_ast(f'struct Temp {{ {line}; }};')
                        if temp and temp.members:
                            nested_members.append(temp.members[0])
                    else:
                        parsed = parse_member_line_v2(line)
                        if parsed is not None:
                            nested_members.append(parsed)
                if var_match:
                    var_token = var_match.group(1)
                    var_name, dims = _extract_array_dims(var_token)
                    nested_def = (StructDef if kind == 'struct' else UnionDef)(
                        name=nested_name or var_name,
                        members=nested_members,
                    )
                    members.append(
                        MemberDef(
                            type=kind,
                            name=var_name,
                            array_dims=dims,
                            nested=nested_def,
                        )
                    )
                    pos = j + var_match.end(0)
                    continue
                elif j < length and struct_body[j] == ';':
                    # 匿名且無變數名稱 -> 展平成員
                    members.extend(nested_members)
                    pos = j + 1
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


def parse_union_definition_ast(file_content: str) -> Optional[UnionDef]:
    """Parse a union definition and return a :class:`UnionDef` object."""
    union_name, union_body = _extract_struct_body(file_content, "union")
    if not union_name or not union_body:
        return None

    union_body = re.sub(r"//.*", "", union_body)
    members = []
    pos = 0
    length = len(union_body)
    while pos < length:
        while pos < length and union_body[pos] in ' \n\t;':
            pos += 1
        if pos >= length:
            break

        if union_body.startswith('union', pos) or union_body.startswith('struct', pos):
            kind = 'union' if union_body.startswith('union', pos) else 'struct'
            m = re.match(rf'{kind}\s+(\w+)\s*\{{', union_body[pos:])
            anon = False
            nested_name = None
            if not m:
                m = re.match(rf'{kind}\s*\{{', union_body[pos:])
                anon = True
            if m:
                nested_name = m.group(1) if len(m.groups()) > 0 else None
                brace_start = pos + m.end(0) - 1
                brace_count = 1
                i = brace_start + 1
                while i < length and brace_count > 0:
                    if union_body[i] == '{':
                        brace_count += 1
                    elif union_body[i] == '}':
                        brace_count -= 1
                    i += 1
                if brace_count != 0:
                    break
                inner_content = union_body[brace_start + 1:i - 1]
                j = i
                while j < length and union_body[j] in ' \n\t':
                    j += 1
                var_match = re.match(r'(\w+(?:\[\d+\])*)\s*;?', union_body[j:])
                nested_members = []
                for line in _split_member_lines(inner_content):
                    line = line.strip()
                    if line.startswith('struct') or line.startswith('union'):
                        temp = parse_struct_definition_ast(f'struct Temp {{ {line}; }};')
                        if temp and temp.members:
                            nested_members.append(temp.members[0])
                    else:
                        parsed = parse_member_line_v2(line)
                        if parsed is not None:
                            nested_members.append(parsed)
                if var_match:
                    var_token = var_match.group(1)
                    var_name, dims = _extract_array_dims(var_token)
                    nested_def = (StructDef if kind == 'struct' else UnionDef)(
                        name=nested_name or var_name,
                        members=nested_members,
                    )
                    members.append(
                        MemberDef(
                            type=kind,
                            name=var_name,
                            array_dims=dims,
                            nested=nested_def,
                        )
                    )
                    pos = j + var_match.end(0)
                    continue
                elif j < length and union_body[j] == ';':
                    members.extend(nested_members)
                    pos = j + 1
                    continue

        semi = union_body.find(';', pos)
        if semi == -1:
            break
        line = union_body[pos:semi].strip()
        parsed = parse_member_line_v2(line)
        if parsed is not None:
            members.append(parsed)
        pos = semi + 1

    return UnionDef(name=union_name, members=members)


def parse_c_definition_ast(file_content: str) -> Optional[Union[StructDef, UnionDef]]:
    """Parse a C struct or union and return a definition object."""
    header = file_content.strip().split('{', 1)[0]
    if header.strip().startswith('union'):
        return parse_union_definition_ast(file_content)
    return parse_struct_definition_ast(file_content)
