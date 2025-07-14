"""Data structures and helpers for struct layout calculations."""

from dataclasses import dataclass
from typing import List, Tuple, Union


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
    "long":               {"size": 8, "align": 8},
    "unsigned long":      {"size": 8, "align": 8},
    "long long":          {"size": 8, "align": 8},
    "unsigned long long": {"size": 8, "align": 8},
    "float":              {"size": 4, "align": 4},
    "double":             {"size": 8, "align": 8},
    "pointer":            {"size": 8, "align": 8},  # Generic for all pointer types
}


@dataclass
class LayoutItem:
    """Represents a single entry in a struct layout."""

    name: str
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


class LayoutCalculator:
    """Helper class for calculating struct memory layout."""

    def __init__(self):
        self.layout: List[LayoutItem] = []
        self.current_offset = 0
        self.max_alignment = 1
        self.bitfield_unit_type = None
        self.bitfield_unit_size = 0
        self.bitfield_unit_align = 0
        self.bitfield_bit_offset = 0
        self.bitfield_unit_offset = 0

    def _get_type_size_and_align(self, mtype: str) -> Tuple[int, int]:
        """Return (size, alignment) for a given C type."""
        info = TYPE_INFO[mtype]
        return info["size"], info["align"]

    # Array processing -------------------------------------------------
    def _process_array_member(self, name: str, mtype: str, array_dims: list):
        """Placeholder for array member handling.

        Currently treats the array as a single element to preserve legacy
        behavior. This will be expanded for full N-D array support in the
        future.
        """
        size, alignment = self._get_type_size_and_align(mtype)
        if alignment > self.max_alignment:
            self.max_alignment = alignment
        self._add_padding_if_needed(alignment)
        # TODO: expand array dimensions in future implementation
        self._add_member_to_layout(name, mtype, size)
        self.current_offset += size

    def calculate(self, members: List[Union[Tuple[str, str], dict]]):
        """Calculate the complete memory layout for the struct."""
        for member in members:
            if isinstance(member, dict) and member.get("is_bitfield", False):
                self._process_bitfield_member(member)
            else:
                self._process_regular_member(member)

        self._add_final_padding()
        return self.layout, self.current_offset, self.max_alignment

    # Internal helpers -------------------------------------------------
    def _process_bitfield_member(self, member: dict):
        mtype = member["type"]
        mname = member["name"]
        mbit_size = member["bit_size"]
        info = TYPE_INFO[mtype]
        size, alignment = info["size"], info["align"]

        if self._needs_new_bitfield_unit(mtype, mbit_size):
            self._start_new_bitfield_unit(mtype, size, alignment)

        self._add_bitfield_to_layout(mname, mtype, mbit_size)
        self.bitfield_bit_offset += mbit_size

    def _process_regular_member(self, member: Union[Tuple[str, str], dict]):
        # End any open bitfield unit
        self.bitfield_unit_type = None
        self.bitfield_bit_offset = 0

        if isinstance(member, tuple):
            member_type, member_name = member
            array_dims = []
        elif isinstance(member, dict):
            member_type = member["type"]
            member_name = member["name"]
            array_dims = member.get("array_dims", [])
        else:
            raise ValueError(f"Invalid member format: {member}")

        if array_dims:
            self._process_array_member(member_name, member_type, array_dims)
            return

        size, alignment = self._get_type_size_and_align(member_type)

        if alignment > self.max_alignment:
            self.max_alignment = alignment

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

        if alignment > self.max_alignment:
            self.max_alignment = alignment

        self.current_offset += size

    def _add_bitfield_to_layout(self, name: str, mtype: str, bit_size: int):
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
        padding = (alignment - (self.current_offset % alignment)) % alignment
        if padding > 0:
            self._add_padding_entry("(padding)", padding)

    def _add_final_padding(self):
        final_padding = (
            self.max_alignment - (self.current_offset % self.max_alignment)
        ) % self.max_alignment
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

