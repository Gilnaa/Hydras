#!/usr/bin/env python

from .utils import *


class HostEndianStruct(Struct):
    a = u16(0xAABB)


class SpecificStruct(Struct):
    a = u16_be(0xAABB)


class SettingsTests(HydrasTestCase):
    def test_priority(self):
        # 1. Global
        self.assertEqual(HostEndianStruct().serialize(), b'\xBB\xAA')
        HydraSettings.target_endian = Endianness.BIG
        self.assertEqual(HostEndianStruct().serialize(), b'\xAA\xBB')

        # 2. Serialization-settings
        HydraSettings.target_endian = Endianness.LITTLE
        self.assertEqual(HostEndianStruct().serialize({'target_endian': Endianness.BIG}), b'\xAA\xBB')

        # 3. Field-settings
        HydraSettings.target_endian = Endianness.LITTLE
        self.assertEqual(SpecificStruct().serialize(), b'\xAA\xBB')

        HydraSettings.target_endian = Endianness.BIG
        self.assertEqual(SpecificStruct().serialize(), b'\xAA\xBB')
        self.assertEqual(SpecificStruct().serialize({'target_endian': Endianness.BIG}), b'\xAA\xBB')
        self.assertEqual(SpecificStruct().serialize({'target_endian': Endianness.LITTLE}), b'\xAA\xBB')


if __name__ == '__main__':
    unittest.main()