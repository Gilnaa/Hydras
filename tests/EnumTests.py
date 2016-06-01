#!/usr/bin/env python
"""
:file: EnumTests.py

This file contains tests for the 'Enum' type formatter.

:date: 20/01/2016
:authors:
    - Kfir Gollan
"""

import unittest
from hydra import *


class EnumTests(unittest.TestCase):
    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian
        self.enum_params = ['A', {'A': 1, 'B': 2}]

    def tearDown(self):
        HydraSettings.pop()

    def test_get_attributes(self):
        enum = Enum(*self.enum_params)
        self.assertEqual(1, enum.A)
        self.assertEqual(2, enum.B)

        with self.assertRaises(AttributeError):
            a = enum.InvalidEnumConst

    def test_validate(self):
        enum = Enum(*self.enum_params)
        self.assertFalse(enum.validate(4))
        self.assertTrue(enum.validate(1))
        self.assertTrue(enum.validate(enum.B))

    def test_format_parse(self):
        test_set = [{
                'class': UInt8,
                'value': 1,
                'little': b'\x01',
                'big': b'\x01',
                'len': 1
            },
            {
                'class': UInt16,
                'value': 1,
                'little': b'\x01\x00',
                'big': b'\x00\x01',
                'len': 2
            },
            {
                'class': UInt32,
                'value': 1,
                'little': b'\x01\x00\x00\x00',
                'big': b'\x00\x00\x00\x01',
                'len': 4
            },
            {
                'class': UInt64,
                'value': 1,
                'little': b'\x01\x00\x00\x00\x00\x00\x00\x00',
                'big': b'\x00\x00\x00\x00\x00\x00\x00\x01',
                'len': 8
            },
        ]
        for test in test_set:
            enum = Enum(*self.enum_params, format_type=test['class'])
            self.assertEqual(enum.format(test['value'], {'endian': LittleEndian}), test['little'])
            self.assertEqual(enum.parse(test['little'], {'endian': LittleEndian}), test['value'])

            self.assertEqual(enum.format(test['value'], {'endian': BigEndian}), test['big'])
            self.assertEqual(enum.parse(test['big'], {'endian': BigEndian}), test['value'])

            self.assertEqual(len(enum), test['len'])


if __name__ == '__main__':
    unittest.main()
