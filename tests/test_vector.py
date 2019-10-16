#!/usr/bin/env python
"""
Contains tests for type formatters from the `vectors.py` module.

:file: VectorTests.py
:date: 29/08/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""
from hydras import *
import unittest


class ThatStruct(Struct):
    """ A simple `Struct`. """

    data = uint16_t(0x55AA)
    indicator = uint8_t(0xFA)
    alignment = Pad()


class HasArray(Struct):
    array = uint8_t[4]


class VectorTests(unittest.TestCase):
    """ A testcase for testing types from the `vectors.py` module. """

    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_typed_array_default_type(self):
        """ Test the Array's default item type. """
        array = uint8_t[3]
        self.assertEqual(array.format([0] * 3), b'\x00\x00\x00')

    def test_typed_array_non_default_type(self):
        """ Test the TypeArray using a scalar value other than the default. """
        array = uint16_t[2]
        data = [0xDEAF, 0xCAFE]
        self.assertEqual(array.format(data), b'\xAF\xDE\xFE\xCA')

    def test_typed_array_big_endian(self):
        """ Test the Array with a multi-byte type in BigEndian. """
        array = int16_t[3]
        HydraSettings.endian = BigEndian

        data = [-2, 100, 200]
        self.assertEqual(array.format(data), b'\xFF\xFE\x00\x64\x00\xC8')

    def test_nested_struct_array(self):
        """ Test the Array with a Struct type. """
        array = ThatStruct[2]
        data = [ThatStruct(), ThatStruct()]
        data[0].indicator = 0

        self.assertEqual(array.format(data), b'\xAA\x55\x00\x00\xAA\x55\xFA\x00')

    def test_value_assignments(self):
        o = HasArray()
        o.array = b'\x00' * 4
        o.array = '\x00' * 4
        o.array = [0] * 4
        o.array = (0, ) * 4
        
        wrong_types = [None, 0, True]
        for v in wrong_types:
            with self.assertRaises(TypeError):
                o.array = v


if __name__ == '__main__':
    unittest.main()
