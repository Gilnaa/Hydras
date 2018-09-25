#!/usr/bin/env python
"""
Contains tests for type formatters from the `vectors.py` module.

:file: VectorTests.py
:date: 29/08/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""
from hydra import *
import unittest


class ThatStruct(Struct):
    """ A simple `Struct`. """

    data = UInt16(0x55AA)
    indicator = UInt8(0xFA)
    alignment = Pad()


class VectorTests(unittest.TestCase):
    """ A testcase for testing types from the `vectors.py` module. """

    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_typed_array_default_type(self):
        """ Test the TypedArray's default item type. """
        array = TypedArray(3)
        self.assertEqual(array.format([0] * 3), b'\x00\x00\x00')

    def test_typed_array_non_default_type(self):
        """ Test the TypeArray using a scalar value other than the default. """
        array = TypedArray(2, UInt16)
        data = [0xDEAF, 0xCAFE]
        self.assertEqual(array.format(data), b'\xAF\xDE\xFE\xCA')

    def test_typed_array_big_endian(self):
        """ Test the TypedArray with a multi-byte type in BigEndian. """
        array = TypedArray(3, Int16)
        HydraSettings.endian = BigEndian

        data = [-2, 100, 200]
        self.assertEqual(array.format(data), b'\xFF\xFE\x00\x64\x00\xC8')

    def test_nested_struct_array(self):
        """ Test the TypedArray with a Struct type. """
        array = TypedArray(2, ThatStruct)
        data = [ThatStruct(), ThatStruct()]
        data[0].indicator = 0

        self.assertEqual(array.format(data), b'\xAA\x55\x00\x00\xAA\x55\xFA\x00')


if __name__ == '__main__':
    unittest.main()
