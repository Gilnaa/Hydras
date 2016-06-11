#!/usr/bin/env python

import unittest
from hydra import *


class BigStruct(Struct):
    settings = {'endian': BigEndian}
    a = uint16_t(0xAABB)


class NativeStruct(Struct):
    a = uint16_t(0xAABB)


class SpecificStruct(Struct):
    a = uint16_t(0xAABB, endian=BigEndian)

class SettingsTests(unittest.TestCase):
    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_priority(self):
        # 1. Global
        self.assertEqual(NativeStruct().serialize(), b'\xBB\xAA')
        HydraSettings.endian = BigEndian
        self.assertEqual(NativeStruct().serialize(), b'\xAA\xBB')

        # 2. Struct-settings
        self.assertEqual(BigStruct().serialize(), b'\xAA\xBB')
        HydraSettings.endian = LittleEndian
        self.assertEqual(BigStruct().serialize(), b'\xAA\xBB')

        # 3. Serialization-settings
        self.assertEqual(BigStruct().serialize({'endian': LittleEndian}), b'\xBB\xAA')

        # 4. Field-settings
        HydraSettings.endian = LittleEndian
        self.assertEqual(SpecificStruct().serialize(), b'\xAA\xBB')

        HydraSettings.endian = BigEndian
        self.assertEqual(SpecificStruct().serialize(), b'\xAA\xBB')

        self.assertEqual(SpecificStruct().serialize({'endian': BigEndian}), b'\xAA\xBB')
        self.assertEqual(SpecificStruct().serialize({'endian': LittleEndian}), b'\xAA\xBB')


if __name__ == '__main__':
    unittest.main()