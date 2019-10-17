#!/usr/bin/env python
"""
Contains tests for the struct-offset feature.

:file: OffsetTests.py
:date: 10/03/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *


class ExampleStruct(Struct):
    a = u8(0)
    b = u16(0x1111)
    c = u32(0x22222222)
    d = u8(0x33)


class OffsetTests(HydrasTestCase):
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