#!/usr/bin/env python
"""
Contains tests for type formatters from the `array.py` module.

:file: VectorTests.py
:date: 29/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *


class ThatStruct(Struct):
    """ A simple `Struct`. """

    data = u16(0x55AA)
    indicator = u8(0xFA)
    alignment = u8


class HasArray(Struct):
    array = u8[4]


class VectorTests(HydrasTestCase):
    """ A testcase for testing types from the `array.py` module. """

    def test_typed_array_default_type(self):
        """ Test the Array's default item type. """
        array = u8[3]()
        self.assertEqual(array.serialize([0] * 3), b'\x00\x00\x00')

    def test_typed_array_non_default_type(self):
        """ Test the TypeArray using a scalar value other than the default. """
        array = u16[2]()
        data = [0xDEAF, 0xCAFE]
        self.assertEqual(array.serialize(data), b'\xAF\xDE\xFE\xCA')

    def test_typed_array_big_endian(self):
        """ Test the Array with a multi-byte type in BigEndian. """
        array = i16_be[3]()

        data = [-2, 100, 200]
        self.assertEqual(array.serialize(data), b'\xFF\xFE\x00\x64\x00\xC8')

    def test_nested_struct_array(self):
        """ Test the Array with a Struct type. """
        array = ThatStruct[2]()
        data = [ThatStruct(), ThatStruct()]
        data[0].indicator = 0

        self.assertEqual(array.serialize(data), b'\xAA\x55\x00\x00\xAA\x55\xFA\x00')

    def test_value_assignments(self):
        o = HasArray()
        o.array = b'\x00' * 4
        o.array = [0] * 4
        o.array = (0, ) * 4
        
        wrong_types = [None, 0, True]
        for v in wrong_types:
            with self.assertRaises(TypeError):
                o.array = v

    def test_default_value(self):
        self.assertEqual(u16[2]([1]).default_value, [1])
        self.assertEqual(u16[2]([1, 1]).default_value, [1, 1])
        with self.assertRaises(ValueError):
            u16[2]([1, 1, 1])

    def test_shorter_value(self):
        a = HasArray()
        a.array = [0, 0]
        self.assertEqual(a.serialize(), b'\00\x00\x00\x00')

