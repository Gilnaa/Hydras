#!/usr/bin/env python
"""
Contains tests for the struct-offset feature.

:file: OffsetTests.py
:date: 10/03/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""
from hydras import *
import unittest


class ExampleStruct(Struct):
    a = uint8_t(0)
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
        obj = ExampleStruct()
        self.assertEqual(obj.serialize(), b'\x00\x11\x11\x22\x22\x22\x22\x33')
        self.assertEqual(obj.serialize(start='c'), b'\x22\x22\x22\x22\x33')
        self.assertEqual(obj.serialize(end='c'), b'\x00\x11\x11\x22\x22\x22\x22')

    def test_offsetof(self):
        self.assertEqual(ExampleStruct.offsetof('a'), 0)
        self.assertEqual(ExampleStruct.offsetof('b'), 1)
        self.assertEqual(ExampleStruct.offsetof('c'), 3)
        self.assertEqual(ExampleStruct.offsetof('d'), 7)