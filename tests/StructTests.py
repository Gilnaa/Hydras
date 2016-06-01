#!/usr/bin/env python

import unittest
from hydra import *

#######################
# Structs for testing #
#######################


class SmallStruct(Struct):
    only_element = uint8_t()


class SimpleStruct(Struct):
    b_first_variable = uint8_t(0xDE)
    a_second_variable = uint16_t(0xCAFE)
    x_third_variable = uint8_t(0xAD)


class ComplicatedStruct(Struct):
    other_struct = NestedStruct(SmallStruct)
    some_field = Array(3, SimpleStruct)
    numeric = uint32_t()


class BigEndianStruct(Struct):
    settings = {'endian': BigEndian}

    hello_i_am_trapped_in_a_variable_factory_please_help_they_are_going_to_ = UInt16(0xFF00)

##############
# Test cases #
##############


class StructTests(unittest.TestCase):
    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_serialize_simple(self):
        obj = SimpleStruct()
        raw_data = obj.serialize()
        self.assertEqual(raw_data, b'\xDE\xFE\xCA\xAD')

    def test_one_does_not_complicatedly(self):
        s = ComplicatedStruct()
        s.numeric = 0xAEAEAEAE
        data = s.serialize()
        self.assertEqual(data, b'\x00\xDE\xFE\xCA\xAD\xDE\xFE\xCA\xAD\xDE\xFE\xCA\xAD\xAE\xAE\xAE\xAE')

        d_s = ComplicatedStruct.deserialize(data)
        self.assertEqual(d_s, s)

    def test_big_endian_struct(self):
        big_endian_struct = BigEndianStruct()
        self.assertEqual(big_endian_struct.serialize(), b'\xFF\x00')

        # Force little-endian
        self.assertEqual(big_endian_struct.serialize({'endian': LittleEndian}), b'\x00\xFF')

if __name__ == '__main__':
    unittest.main()