#!/usr/bin/env python

from .utils import *


class SettingsTests(HydrasTestCase):
    def test_priority(self):
        pass
        # TODO: Rewrite test with another setting. (e.g. `dry_run`)
        # # 1. Global
        # self.assertEqual(NativeStruct().serialize(), b'\xBB\xAA')
        # HydraSettings.endian = BigEndian
        # self.assertEqual(NativeStruct().serialize(), b'\xAA\xBB')
        #
        # # 2. Struct-settings
        # self.assertEqual(BigStruct().serialize(), b'\xAA\xBB')
        # HydraSettings.endian = LittleEndian
        # self.assertEqual(BigStruct().serialize(), b'\xAA\xBB')
        #
        # # 3. Serialization-settings
        # self.assertEqual(BigStruct().serialize({'endian': LittleEndian}), b'\xBB\xAA')
        #
        # # 4. Field-settings
        # HydraSettings.endian = LittleEndian
        # self.assertEqual(SpecificStruct().serialize(), b'\xAA\xBB')
        #
        # HydraSettings.endian = BigEndian
        # self.assertEqual(SpecificStruct().serialize(), b'\xAA\xBB')
        #
        # self.assertEqual(SpecificStruct().serialize({'endian': BigEndian}), b'\xAA\xBB')
        # self.assertEqual(SpecificStruct().serialize({'endian': LittleEndian}), b'\xAA\xBB')


if __name__ == '__main__':
    unittest.main()