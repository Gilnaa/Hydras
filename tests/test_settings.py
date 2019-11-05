#!/usr/bin/env python

from .utils import *


# This struct's endianness is of the "target"
class TargetStruct(Struct):
    a = u16(0xAABB)


# while this struct's endianness is always big.
class SpecificStruct(Struct):
    a = u16_be(0xAABB)


class SettingsTests(HydrasTestCase):
    def test_priority(self):
        s = SpecificStruct()
        h = TargetStruct()

        # 1. Global - Make sure that the serialized struct reacts to the global settings.
        HydraSettings.target_endian = Endianness.LITTLE
        self.assertEqual(h.serialize(), b'\xBB\xAA')
        HydraSettings.target_endian = Endianness.BIG
        self.assertEqual(h.serialize(), b'\xAA\xBB')

        # 2. Serialization-settings - Make sure that the struct uses the overriden endianness
        HydraSettings.target_endian = Endianness.LITTLE
        self.assertEqual(h.serialize(HydraSettings(target_endian=Endianness.BIG)), b'\xAA\xBB')
        self.assertEqual(h, TargetStruct.deserialize(b'\xAA\xBB', HydraSettings(target_endian=Endianness.BIG)))

        HydraSettings.target_endian = Endianness.BIG
        self.assertEqual(h, TargetStruct.deserialize(b'\xBB\xAA', HydraSettings(target_endian=Endianness.LITTLE)))

        # 3. Field-settings - Make sure that the BE fields ignore any settings
        HydraSettings.target_endian = Endianness.LITTLE
        self.assertEqual(s.serialize(), b'\xAA\xBB')

        HydraSettings.target_endian = Endianness.BIG
        self.assertEqual(s.serialize(), b'\xAA\xBB')

        self.assertEqual(s.serialize(HydraSettings(target_endian=Endianness.BIG)), b'\xAA\xBB')
        self.assertEqual(s.serialize(HydraSettings(target_endian=Endianness.LITTLE)), b'\xAA\xBB')
        self.assertEqual(SpecificStruct.deserialize(b'\xAA\xBB', HydraSettings(target_endian=Endianness.BIG)), s)
        self.assertEqual(SpecificStruct.deserialize(b'\xAA\xBB', HydraSettings(target_endian=Endianness.LITTLE)), s)


if __name__ == '__main__':
    unittest.main()