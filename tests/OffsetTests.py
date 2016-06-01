#!/usr/bin/env python
"""
Contains tests for the struct-offset framework feature.

:file: OffsetTests.py
:date: 10/03/2016
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
"""

from hydra import *
import unittest


class ExampleStruct(Struct):
    a = uint8_t()
    b = uint16_t(0x1111)
    c = uint32_t(0x22222222)
    d = uint8_t(0x33)


class OffsetTests(unittest.TestCase):
    """ A testcase for testing the offset feature. """

    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_ranged_serialize(self):
        o = ExampleStruct()
        self.assertEqual(o.serialize(), b'\x00\x11\x11\x22\x22\x22\x22\x33')
        self.assertEqual(o.serialize(start=ExampleStruct.c), b'\x22\x22\x22\x22\x33')
        self.assertEqual(o.serialize(end=ExampleStruct.c), b'\x00\x11\x11\x22\x22\x22\x22')

    def test_offsetof(self):
        self.assertEqual(ExampleStruct.offsetof(ExampleStruct.a), 0)
        self.assertEqual(ExampleStruct.offsetof(ExampleStruct.b), 1)
        self.assertEqual(ExampleStruct.offsetof(ExampleStruct.c), 3)
        self.assertEqual(ExampleStruct.offsetof(ExampleStruct.d), 7)


if __name__ == '__main__':
    unittest.main()