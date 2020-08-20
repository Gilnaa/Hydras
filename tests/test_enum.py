#!/usr/bin/env python
"""
:file: EnumClassTests.py

This file contains tests for the 'EnumClass' type formatter.

:date: 10/06/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *


class EOpcodeThingie(Enum):
    a = auto()
    b = auto()
    c = 10
    d = auto()


class StructThingie(Struct):
    opcode = EOpcodeThingie(EOpcodeThingie.a)
    pad = u8(0xFF)


class ESizedOpcodeThingie(Enum, underlying_type=u8):
    a = auto()
    b = auto()
    c = 10
    d = auto()


class SizedStructThingie(Struct):
    opcode = ESizedOpcodeThingie


class EnumClassTests(HydrasTestCase):
    def test_enum_class(self):
        s = StructThingie()

        # Test values
        s.opcode = EOpcodeThingie.a
        self.assertEqual(s.serialize(), b'\x00\x00\x00\x00\xFF')
        s.opcode = EOpcodeThingie.b
        self.assertEqual(s.serialize(), b'\x01\x00\x00\x00\xFF')
        s.opcode = EOpcodeThingie.c
        self.assertEqual(s.serialize(), b'\x0a\x00\x00\x00\xFF')
        s.opcode = EOpcodeThingie.d
        self.assertEqual(s.serialize(), b'\x0b\x00\x00\x00\xFF')

    def test_sized_enum_class(self):
        s = SizedStructThingie()

        s.opcode = ESizedOpcodeThingie.a
        self.assertEqual(s.serialize(), b'\x00')
        s.opcode = ESizedOpcodeThingie.b
        self.assertEqual(s.serialize(), b'\x01')
        s.opcode = ESizedOpcodeThingie.c
        self.assertEqual(s.serialize(), b'\x0a')
        s.opcode = ESizedOpcodeThingie.d
        self.assertEqual(s.serialize(), b'\x0b')

    def test_self_compatibility(self):
        s = StructThingie()
        self.assertEqual(s, StructThingie.deserialize(s.serialize()))

    def test_enum_array(self):
        enarr = EOpcodeThingie[2]()
        self.assertEqual(enarr.serialize((EOpcodeThingie.a, EOpcodeThingie.b)), b'\x00\x00\x00\x00\x01\x00\x00\x00')

    def test_direct_enum_instantiation(self):
        with self.assertRaises(RuntimeError):
            a = Enum()

    def test_literal_hash_smoke_test(self):
        self.assertEqual(hash(EOpcodeThingie.a),
                         hash(EOpcodeThingie.a))
        self.assertNotEqual(hash(EOpcodeThingie.a),
                            hash(EOpcodeThingie.b))

    def test_int_construction(self):
        val = int(EOpcodeThingie.a)
        fmt = EOpcodeThingie(val)
        lit = fmt.get_literal_by_value(val)
        lit_ty = EOpcodeThingie.get_literal_by_value(val)
        self.assertEqual(lit, EOpcodeThingie.a)
        self.assertEqual(lit_ty, EOpcodeThingie.a)


if __name__ == '__main__':
    unittest.main()
