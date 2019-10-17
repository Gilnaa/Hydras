#!/usr/bin/env python
"""
This file tests the libraries ability to cope with Python3.

:file: Python3Tests.py
:date: 05/02/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *


class Sample(Struct):
    member = u32()


class TestPython3(HydrasTestCase):
    def test_bytes_object(self):
        """ Tests the deserialize function works with both strings and bytes. """
        data_str = '\x00\x00\x00\x32'
        data_bytes = b'\x00\x00\x00\x32'

        obj_str = Sample.deserialize(data_str)
        obj_bytes = Sample.deserialize(data_bytes)

        serialized_str = obj_str.serialize()
        serialized_bytes = obj_bytes.serialize()

        self.assertEqual(type(serialized_str), bytes)
        self.assertEqual(type(serialized_bytes), bytes)

        self.assertEqual(serialized_str, serialized_bytes)
