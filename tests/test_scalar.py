#!/usr/bin/env python
"""
This file contains tests for the "Scalar" type formatters.

:file: ScalarsTests.py
:date: 29/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *


class TestScalarFormatters(HydrasTestCase):
    def test_unsigned_integers(self):
        # Little endian
        self.assertEqual(u8_le().serialize(1), b'\x01')
        self.assertEqual(u8_le().serialize(64), b'\x40')
        self.assertEqual(u16_le().serialize(0xCAFE), b'\xFE\xCA')
        self.assertEqual(u32_le().serialize(0xDEADBEEF), b'\xEF\xBE\xAD\xDE')
        self.assertEqual(u64_le().serialize(0xDEAFDEADBEEFCAFE), b'\xFE\xCA\xEF\xBE\xAD\xDE\xAF\xDE')

        # Big endian
        self.assertEqual(u16_be().serialize(0xCAFE), b'\xCA\xFE')
        self.assertEqual(u32_be().serialize(0xDEADBEEF), b'\xDE\xAD\xBE\xEF')
        self.assertEqual(u64_be().serialize(0xDEAFDEADBEEFCAFE), b'\xDE\xAF\xDE\xAD\xBE\xEF\xCA\xFE')

    def test_value_assignment_out_of_bounds(self):
        class Foo(Struct):
            byte = u8
            twobytes = u16
            fourbytes = u32
            eightbytes = u64

        f = Foo()

        with self.assertRaises(ValueError):
            f.byte = 0x100

        with self.assertRaises(ValueError):
            f.twobytes = 0x10000

        with self.assertRaises(ValueError):
            f.fourbytes = 0x100000000

        with self.assertRaises(ValueError):
            f.eightbytes = 0x10000000000000000

    def test_floats(self):
        class Foo(Struct):
            float = f32
            double = f64

        self.assertEqual(bytes(Foo(dict(float=1,
                                        double=1))), b'\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\xF0\x3F')
