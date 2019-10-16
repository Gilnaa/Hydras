#!/usr/bin/env python
"""
This file contains tests for the "Scalar" type formatters.

:file: ScalarsTests.py
:date: 29/08/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

import unittest
from hydras import *


class TestScalarFormatters(unittest.TestCase):
    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_unsigned_integers(self):
        # Create the formatters objects.
        u8 = uint8_t()
        u16 = uint16_t()
        u32 = uint32_t()
        u64 = uint64_t()

        # Little endian
        self.assertEqual(u8.format(1), b'\x01')
        self.assertEqual(u8.format(64), b'\x40')
        self.assertEqual(u16.format(0xCAFE), b'\xFE\xCA')
        self.assertEqual(u32.format(0xDEADBEEF), b'\xEF\xBE\xAD\xDE')
        self.assertEqual(u64.format(0xDEAFDEADBEEFCAFE), b'\xFE\xCA\xEF\xBE\xAD\xDE\xAF\xDE')

        HydraSettings.endian = BigEndian
        # Big endian
        self.assertEqual(u16.format(0xCAFE), b'\xCA\xFE')
        self.assertEqual(u32.format(0xDEADBEEF), b'\xDE\xAD\xBE\xEF')
        self.assertEqual(u64.format(0xDEAFDEADBEEFCAFE), b'\xDE\xAF\xDE\xAD\xBE\xEF\xCA\xFE')

    def test_endian(self):
        little_u32 = uint32_t(endian=BigEndian)

        self.assertEqual(little_u32.format(0xDEADBEEF), b'\xDE\xAD\xBE\xEF')

    def test_value_assignment_out_of_bounds(self):
        class Foo(Struct):
            u8 = uint8_t()
            u16 = uint16_t()
            u32 = uint32_t()
            u64 = uint64_t()

        f = Foo()

        with self.assertRaises(ValueError):
            f.u8 = 0x100

        with self.assertRaises(ValueError):
            f.u16 = 0x10000

        with self.assertRaises(ValueError):
            f.u32 = 0x100000000

        with self.assertRaises(ValueError):
            f.u64 = 0x10000000000000000
            

if __name__ == '__main__':
    unittest.main()
