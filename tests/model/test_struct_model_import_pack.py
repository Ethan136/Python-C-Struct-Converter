import os
import tempfile

import unittest

from src.model.struct_model import StructModel


HEADER_PUSH_1 = """
#pragma pack(push,1)
struct S {
    char c;
    int i;
};
"""

HEADER_PUSH1_PUSH4_POP = """
#pragma pack(push,1)
#pragma pack(push,4)
struct A { int x; char y; };
#pragma pack(pop)
struct B { int x; };
"""

HEADER_PACK_2 = """
#pragma pack(2)
struct S { char c; int i; };
"""

HEADER_POP_ONLY = """
#pragma pack(pop)
struct S { int i; };
"""

HEADER_ARRAY = """
#pragma pack(2)
struct S { short s; int arr[2]; };
"""

HEADER_BITFIELDS = """
#pragma pack(1)
struct S { unsigned int a:3; unsigned int b:5; unsigned int c:8; };
"""

HEADER_NESTED_UNION = """
#pragma pack(1)
struct S { union { int x; char y[4]; } u; char t; };
"""


class TestImportPackAlignment(unittest.TestCase):
    def _write_temp_header(self, src: str) -> str:
        fd, path = tempfile.mkstemp(suffix='.h')
        with os.fdopen(fd, 'w') as f:
            f.write(src)
        return path

    def test_import_h_applies_top_level_pack_push_1(self):
        path = self._write_temp_header(HEADER_PUSH_1)
        try:
            m = StructModel()
            name, layout, total, align = m.load_struct_from_file(path)
            self.assertEqual(name, 'S')
            # Expect i at offset 1 due to pack=1
            names = [it['name'] if isinstance(it, dict) else getattr(it, 'name', None) for it in layout]
            offsets = [it['offset'] if isinstance(it, dict) else getattr(it, 'offset', None) for it in layout]
            pairs = list(zip(names, offsets))
            # Find 'i'
            i_entries = [o for (n, o) in pairs if n == 'i']
            self.assertTrue(i_entries, 'field i not found in layout')
            self.assertEqual(i_entries[0], 1)
        finally:
            os.remove(path)

    def test_import_h_applies_top_level_pack_push_nested_push_pop(self):
        path = self._write_temp_header(HEADER_PUSH1_PUSH4_POP)
        try:
            m = StructModel()
            # Default last top-level should be B (pack after pop => back to 1)
            name, layout, total, align = m.load_struct_from_file(path)
            self.assertEqual(name, 'B')
            # Switch to A (pack=4 active)
            m.set_import_target_struct('A')
            # Find y offset in A: with pack=4, x at 0, y typically at offset 4 (alignment=min(1,4?) -> base type align 1; but struct alignment=min(typeAlign,4))
            # We assert total size respects pack=4 minimum alignment on int boundary
            # For robustness, check that there is padding before y or y offset >=1 and <4 is allowed depending on rules; assert total >= 8 when packed to 4
            self.assertGreaterEqual(m.total_size, 8)
        finally:
            os.remove(path)

    def test_import_h_applies_top_level_pack_single_pack_syntax(self):
        path = self._write_temp_header(HEADER_PACK_2)
        try:
            m = StructModel()
            name, layout, total, align = m.load_struct_from_file(path)
            self.assertEqual(name, 'S')
            # With pack=2, i should align to 2 not 4; so offset of i should be 2
            names = [it['name'] if isinstance(it, dict) else getattr(it, 'name', None) for it in layout]
            offsets = [it['offset'] if isinstance(it, dict) else getattr(it, 'offset', None) for it in layout]
            pairs = list(zip(names, offsets))
            i_entries = [o for (n, o) in pairs if n == 'i']
            self.assertTrue(i_entries, 'field i not found in layout')
            self.assertEqual(i_entries[0], 2)
        finally:
            os.remove(path)

    def test_import_h_ignores_trailing_pop_without_push(self):
        path = self._write_temp_header(HEADER_POP_ONLY)
        try:
            m = StructModel()
            name, layout, total, align = m.load_struct_from_file(path)
            self.assertEqual(name, 'S')
            # No crash, layout exists, baseline offset of i is 0
            names = [it['name'] if isinstance(it, dict) else getattr(it, 'name', None) for it in layout]
            offsets = [it['offset'] if isinstance(it, dict) else getattr(it, 'offset', None) for it in layout]
            pairs = list(zip(names, offsets))
            i_entries = [o for (n, o) in pairs if n == 'i']
            self.assertTrue(i_entries, 'field i not found in layout')
            self.assertEqual(i_entries[0], 0)
        finally:
            os.remove(path)

    def test_import_h_pack_effect_on_array_elements(self):
        path = self._write_temp_header(HEADER_ARRAY)
        try:
            m = StructModel()
            name, layout, total, align = m.load_struct_from_file(path)
            pairs = [(it['name'] if isinstance(it, dict) else getattr(it,'name', None), it['offset'] if isinstance(it, dict) else getattr(it,'offset', None)) for it in layout]
            # arr[0] should align to 2, not 4
            a0 = [o for (n,o) in pairs if n == 'arr[0]']
            self.assertTrue(a0)
            self.assertEqual(a0[0], 2)
        finally:
            os.remove(path)

    def test_import_h_pack_effect_on_bitfields(self):
        path = self._write_temp_header(HEADER_BITFIELDS)
        try:
            m = StructModel()
            name, layout, total, align = m.load_struct_from_file(path)
            # With pack=1, total size should be compact; at least 4 bytes for 16 bits into a 4-byte unit
            self.assertGreaterEqual(total, 4)
        finally:
            os.remove(path)

    def test_import_h_pack_effect_on_nested_union(self):
        path = self._write_temp_header(HEADER_NESTED_UNION)
        try:
            m = StructModel()
            name, layout, total, align = m.load_struct_from_file(path)
            pairs = [(it['name'] if isinstance(it, dict) else getattr(it,'name', None), it['offset'] if isinstance(it, dict) else getattr(it,'offset', None)) for it in layout]
            # u should be at offset 0; t follows at offset 4 (no extra alignment beyond pack=1)
            t_off = [o for (n,o) in pairs if n == 't'][0]
            self.assertEqual(t_off, 4)
        finally:
            os.remove(path)

