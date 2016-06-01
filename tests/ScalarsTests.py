#!/usr/bin/env python

import unittest
from hydra import *


class TestScalarFormatters(unittest.TestCase):
    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_unsigned_integers(self):
        u8 = UInt8()
        u16 = UInt16()
        u32 = UInt32()
        u64 = UInt64()

        # Little endian
        self.assertEqual(u8.format(1), b'\x01')
        self.assertEqual(u8.format(64), b'\x40')
        self.assertEqual(u16.format(0xCAFE), b'\xFE\xCA')
        self.assertEqual(u32.format(0xDEADBEEF), b'\xEF\xBE\xAD\xDE')
        self.assertEqual(u64.format(0xDEAFDEADBEEFCAFE), b'\xFE\xCA\xEF\xBE\xAD\xDE\xAF\xDE')

        # Big endian
        HydraSettings.endian = BigEndian
        self.assertEqual(u16.format(0xCAFE), b'\xCA\xFE')
        self.assertEqual(u32.format(0xDEADBEEF), b'\xDE\xAD\xBE\xEF')
        self.assertEqual(u64.format(0xDEAFDEADBEEFCAFE), b'\xDE\xAF\xDE\xAD\xBE\xEF\xCA\xFE')

    def test_endian(self):
        big_u32 = UInt32(endian=BigEndian)

        self.assertEqual(big_u32.format(0xDEADBEEF), b'\xDE\xAD\xBE\xEF')

    def test_parse(self):
        big_u16 = UInt16(endian=BigEndian)
        little_u16 = UInt16(endian=LittleEndian)

        self.assertEqual(big_u16.parse('\xAA\xBB'), 0xAABB)
        self.assertEqual(little_u16.parse('\xAA\xBB'), 0xBBAA)


if __name__ == '__main__':
    unittest.main()