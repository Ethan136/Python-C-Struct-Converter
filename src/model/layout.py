"""Data structures and helpers for struct layout calculations."""

from dataclasses import dataclass
from typing import List, Tuple, Union, Optional
from abc import ABC, abstractmethod


# Based on a common 64-bit system (like GCC on x86-64)
TYPE_INFO = {
    "char":               {"size": 1, "align": 1},
    "signed char":        {"size": 1, "align": 1},
    "unsigned char":      {"size": 1, "align": 1},
    "U8":                 {"size": 1, "align": 1},
    "bool":               {"size": 1, "align": 1},
    "short":              {"size": 2, "align": 2},
    "unsigned short":     {"size": 2, "align": 2},
    "U16":                {"size": 2, "align": 2},
    "int":                {"size": 4, "align": 4},
    "unsigned int":       {"size": 4, "align": 4},
    "U32":                {"size": 4, "align": 4},
    "long":               {"size": 8, "align": 8},
    "unsigned long":      {"size": 8, "align": 8},
    "long long":          {"size": 8, "align": 8},
    "unsigned long long": {"size": 8, "align": 8},
    "U64":                {"size": 8, "align": 8},
    "float":              {"size": 4, "align": 4},
    "double":             {"size": 8, "align": 8},
    "pointer":            {"size": 8, "align": 8},  # Generic for all pointer types
}


@dataclass
class LayoutItem:
    """Represents a single entry in a struct layout.

    ``name`` is optional so that future versions can represent anonymous
    bit fields as padding entries.
    """

    name: Optional[str]
    type: str
    size: int
    offset: int
    is_bitfield: bool
    bit_offset: int
    bit_size: int

    def __getitem__(self, key: str):
        return getattr(self, key)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class BaseLayoutCalculator(ABC):
    """Abstract base class for layout calculators."""

    def __init__(self, pack_alignment: Optional[int] = None):
        """Initialize the layout calculator.

        ``pack_alignment`` allows future support for ``#pragma pack`` style
        alignment control. The parameter is accepted but currently ignored so
        that existing behaviour remains unchanged.
        """
        self.pack_alignment = pack_alignment
        self.layout: List[LayoutItem] = []
        self.current_offset = 0
        self.max_alignment = 1
        self.bitfield_unit_type = None
        self.bitfield_unit_size = 0
        self.bitfield_unit_align = 0
        self.bitfield_bit_offset = 0
        self.bitfield_unit_offset = 0

    def _effective_alignment(self, alignment: int) -> int:
        """Return the effective alignment.

        This method applies pack_alignment if set, mimicking #pragma pack behavior.
        """
        if self.pack_alignment is not None:
            return min(alignment, self.pack_alignment)
        return alignment

    def _get_attr(
        self, member: Union[Tuple[str, str], dict, object], attr: str, default=None
    ):
        """Retrieve attribute from ``member`` supporting multiple formats, including AST objects."""
        if isinstance(member, tuple):
            if attr == "type":
                return member[0]
            if attr == "name":
                return member[1]
            return default
        if isinstance(member, dict):
            return member.get(attr, default)
        # 支援 AST dataclass 物件
        if hasattr(member, attr):
            return getattr(member, attr)
        return default

    @abstractmethod
    def calculate(self, members: List[Union[Tuple[str, str], dict]]):
        """Calculate layout for given members."""
        raise NotImplementedError


class StructLayoutCalculator(BaseLayoutCalculator):
    """Helper class for calculating struct memory layout."""

    def __init__(self, pack_alignment: Optional[int] = None):
        super().__init__(pack_alignment=pack_alignment)

    def _get_type_size_and_align(self, mtype: str, nested=None) -> Tuple[int, int]:
        """Return (size, alignment) for a given C type or struct/union (AST)。"""
        if mtype in TYPE_INFO:
            info = TYPE_INFO[mtype]
            return info["size"], info["align"]
        # 若是 struct/union 型別，遞迴計算 nested
        if nested is not None:
            nested_members = None
            if hasattr(nested, "members"):
                nested_members = nested.members
            elif isinstance(nested, dict):
                nested_members = nested.get("members", [])
            if nested_members is not None:
                _, size, align = StructLayoutCalculator(pack_alignment=self.pack_alignment).calculate(nested_members)
                return size, align
        raise KeyError(f"Unknown type: {mtype}")

    # Array processing -------------------------------------------------
    def _process_array_member(self, name: str, mtype: str, array_dims: list, nested=None):
        """展開多維陣列，支援巢狀 struct/array。"""
        # 若是 struct array，需遞迴展開 nested members
        def expand_indices(dims):
            if not dims:
                yield []
            else:
                for i in range(dims[0]):
                    for rest in expand_indices(dims[1:]):
                        yield [i] + rest

        # 巢狀 struct/union/array: 只要 nested 不為 None 就遞迴展開
        nested_members = None
        if nested is not None:
            if hasattr(nested, "members"):
                nested_members = nested.members
            elif isinstance(nested, dict):
                nested_members = nested.get("members", [])
        if nested_members is not None:
            struct_layout, struct_size, struct_align = StructLayoutCalculator(pack_alignment=self.pack_alignment).calculate(nested_members)
            if struct_align > self.max_alignment:
                self.max_alignment = struct_align
            self._add_padding_if_needed(struct_align)
            for idx_tuple in expand_indices(array_dims):
                idx_str = ''.join(f'[{i}]' for i in idx_tuple)
                prefix = f"{name}{idx_str}"
                base_offset = self.current_offset
                for member in nested_members:
                    self._process_regular_member(self._clone_member_with_prefix(member, prefix, base_offset))
                self.current_offset += struct_size
        else:
            # 基本型別 array
            size, alignment = self._get_type_size_and_align(mtype, nested)
            effective_align = self._effective_alignment(alignment)
            if effective_align > self.max_alignment:
                self.max_alignment = effective_align
            self._add_padding_if_needed(alignment)
            for idx_tuple in expand_indices(array_dims):
                idx_str = ''.join(f'[{i}]' for i in idx_tuple)
                elem_name = f"{name}{idx_str}"
                self._add_member_to_layout(elem_name, mtype, size)
                self.current_offset += size

    def _clone_member_with_prefix(self, member, prefix, base_offset):
        import copy
        m = copy.deepcopy(member)
        if hasattr(m, 'name') and m.name:
            m.name = f"{prefix}.{m.name}" if not prefix.endswith('.') else f"{prefix}{m.name}"
        if hasattr(m, 'offset'):
            m.offset = base_offset + getattr(m, 'offset', 0)
        return m

    def calculate(self, members: List[Union[Tuple[str, str], dict]]):
        """Calculate the complete memory layout for the struct."""
        for member in members:
            if hasattr(member, "is_bitfield") and hasattr(member, "type"):
                if member.is_bitfield:
                    self._process_bitfield_member(member)
                else:
                    self._process_regular_member(member)
            elif isinstance(member, dict) and member.get("is_bitfield", False):
                self._process_bitfield_member(member)
            else:
                self._process_regular_member(member)

        self._add_final_padding()
        return (
            self.layout,
            self.current_offset,
            self._effective_alignment(self.max_alignment),
        )

    # Internal helpers -------------------------------------------------
    def _process_bitfield_member(self, member):
        mtype = self._get_attr(member, "type")
        mname = self._get_attr(member, "name")
        mbit_size = self._get_attr(member, "bit_size")
        info = TYPE_INFO[mtype]
        size, alignment = info["size"], info["align"]

        if self._needs_new_bitfield_unit(mtype, mbit_size):
            self._start_new_bitfield_unit(mtype, size, alignment)

        self._add_bitfield_to_layout(mname, mtype, mbit_size)
        self.bitfield_bit_offset += mbit_size

    def _process_regular_member(self, member: Union[Tuple[str, str], dict]):
        # 若此成員為 bitfield，改由 bitfield 流程處理（不可重置 bitfield 單元狀態）
        is_bf = False
        try:
            # 支援 dataclass/dict/tuple 取得屬性
            is_bf = self._get_attr(member, "is_bitfield", False)
        except Exception:
            is_bf = False
        if is_bf:
            self._process_bitfield_member(member)
            return

        # 遇到一般欄位時才重置 bitfield 單元狀態
        self.bitfield_unit_type = None
        self.bitfield_bit_offset = 0

        member_type = self._get_attr(member, "type")
        member_name = self._get_attr(member, "name")
        array_dims = self._get_attr(member, "array_dims") or []
        nested = self._get_attr(member, "nested", None)

        if array_dims:
            self._process_array_member(member_name, member_type, array_dims, nested)
            return

        # 巢狀 struct/union: 只要 nested 不為 None 就遞迴展開
        nested_members = None
        if nested is not None:
            if hasattr(nested, "members"):
                nested_members = nested.members
            elif isinstance(nested, dict):
                nested_members = nested.get("members", [])
        if nested_members is not None:
            struct_layout, struct_size, struct_align = StructLayoutCalculator(pack_alignment=self.pack_alignment).calculate(nested_members)
            if struct_align > self.max_alignment:
                self.max_alignment = struct_align
            self._add_padding_if_needed(struct_align)
            base_offset = self.current_offset
            for member in nested_members:
                self._process_regular_member(self._clone_member_with_prefix(member, member_name, base_offset))
            self.current_offset += struct_size
            return

        size, alignment = self._get_type_size_and_align(member_type, nested)
        effective_align = self._effective_alignment(alignment)
        if effective_align > self.max_alignment:
            self.max_alignment = effective_align
        self._add_padding_if_needed(alignment)
        self._add_member_to_layout(member_name, member_type, size)
        self.current_offset += size

    def _needs_new_bitfield_unit(self, mtype: str, mbit_size: int) -> bool:
        return (
            self.bitfield_unit_type != mtype
            or self.bitfield_bit_offset + mbit_size > self.bitfield_unit_size * 8
        )

    def _start_new_bitfield_unit(self, mtype: str, size: int, alignment: int):
        self._add_padding_if_needed(alignment)
        self.bitfield_unit_type = mtype
        self.bitfield_unit_size = size
        self.bitfield_unit_align = alignment
        self.bitfield_bit_offset = 0
        self.bitfield_unit_offset = self.current_offset

        effective_align = self._effective_alignment(alignment)
        if effective_align > self.max_alignment:
            self.max_alignment = effective_align

        self.current_offset += size

    def _add_bitfield_to_layout(self, name: str, mtype: str, bit_size: int):
        """Add a bit field entry to ``self.layout``.

        ``name`` may be ``None`` in future versions when supporting anonymous
        bit fields. For now all callers still pass a string.
        """
        self.layout.append(
            LayoutItem(
                name=name,
                type=mtype,
                size=self.bitfield_unit_size,
                offset=self.bitfield_unit_offset,
                is_bitfield=True,
                bit_offset=self.bitfield_bit_offset,
                bit_size=bit_size,
            )
        )

    def _add_member_to_layout(self, name: str, member_type: str, size: int):
        self.layout.append(
            LayoutItem(
                name=name,
                type=member_type,
                size=size,
                offset=self.current_offset,
                is_bitfield=False,
                bit_offset=0,
                bit_size=size * 8,
            )
        )

    def _add_padding_if_needed(self, alignment: int):
        effective = self._effective_alignment(alignment)
        padding = (effective - (self.current_offset % effective)) % effective
        if padding > 0:
            self._add_padding_entry("(padding)", padding)

    def _add_final_padding(self):
        effective = self._effective_alignment(self.max_alignment)
        final_padding = (
            effective - (self.current_offset % effective)
        ) % effective
        if final_padding > 0:
            self._add_padding_entry("(final padding)", final_padding)

    def _add_padding_entry(self, name: str, size: int):
        self.layout.append(
            LayoutItem(
                name=name,
                type="padding",
                size=size,
                offset=self.current_offset,
                is_bitfield=False,
                bit_offset=0,
                bit_size=size * 8,
            )
        )
        self.current_offset += size


class UnionLayoutCalculator(BaseLayoutCalculator):
    """Calculate memory layout for a C union."""

    def __init__(self, pack_alignment: Optional[int] = None):
        super().__init__(pack_alignment=pack_alignment)

    def _get_type_size_and_align(self, mtype: str) -> Tuple[int, int]:
        info = TYPE_INFO[mtype]
        return info["size"], info["align"]

    def calculate(self, members: List[Union[Tuple[str, str], dict]]):
        max_size = 0
        for member in members:
            if isinstance(member, tuple):
                mtype, mname = member
            elif isinstance(member, dict):
                mtype = member["type"]
                mname = member["name"]
            elif hasattr(member, "type"):
                mtype = member.type
                mname = member.name
            else:
                raise ValueError(f"Invalid member format: {member}")

            size, alignment = self._get_type_size_and_align(mtype)
            if alignment > self.max_alignment:
                self.max_alignment = alignment
            if size > max_size:
                max_size = size
            self.layout.append(
                LayoutItem(
                    name=mname,
                    type=mtype,
                    size=size,
                    offset=0,
                    is_bitfield=False,
                    bit_offset=0,
                    bit_size=size * 8,
                )
            )

        self.current_offset = max_size
        self._add_final_padding()
        return (
            self.layout,
            self.current_offset,
            self._effective_alignment(self.max_alignment),
        )


# Maintain backward compatibility
LayoutCalculator = StructLayoutCalculator

