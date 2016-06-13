#!/usr/bin/env python
"""
Contains tests for the bitfield type formatter.

:file: BitFieldTests.py
:date: 27/01/2016
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
"""

from hydra import *
import unittest


class BitFieldTests(unittest.TestCase):
    """ A testcase for testing the BitField formatter. """

    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_bitfield_user_facing_value(self):
        """ Test the "Default Value" of the bitfield. """
        bitfield = BitField(first=Bits(5), second=Bits(11))
        self.assertEqual(bitfield.default_value, {'first': 0, 'second': 0})

        bitfield = BitField(first=Bits(6), second=Bits(12))
        self.assertEqual(bitfield.default_value, {'first': 0, 'second': 0})

        bitfield = BitField(first=Bits(5, 32), second=Bits(11, 42))
        self.assertEqual(bitfield.default_value, {'first': 32, 'second': 42})

    def test_bitfields_validates_bit_length(self):
        with self.assertRaises(ValueError):
            bitfield = BitField(first=Bits(1))
            bitfield.format({'first': 2}, {'enforce_bitfield_size': True})

        try:
            bitfield.format({'first': 2}, {'enforce_bitfield_size': False})
        except ValueError:
            self.fail('ValueError was raised from a non-enforcing bitfield.')

    def test_bitfield_little_endian(self):
        tests = {
            # Size: 16 bits => 2 bytes.
            BitField(i=Bits(5, 31), j=Bits(11)):                    b'\x1F\x00',
            BitField(i=Bits(5, 29), j=Bits(11, 1020)):              b'\x9D\x7F',
            # Size: 17 bits => 3 bytes (w/ padding).
            BitField(i=Bits(6, 28), j=Bits(3, 5), k=Bits(8, 7)):    b'\x5C\x0F\x00',
            BitField(i=Bits(6, 63), j=Bits(3, 0), k=Bits(8, 15)):   b'\x3F\x1E\x00'
        }

        for bitfield, result in tests.items():
            # Serialization
            self.assertEqual(result, bitfield.format(bitfield.default_value))

            # Deserialization
            self.assertEqual(bitfield.parse(result), bitfield.default_value)

    def test_bitfield_big_endian(self):
        tests = {
            # Size: 16 bits => 2 bytes.
            BitField(i=Bits(5, 31), j=Bits(11)):                    b'\xF8\x00',
            BitField(i=Bits(5, 29), j=Bits(11, 1020)):              b'\xEB\xFC',
            # Size: 17 bits => 3 bytes (w/ padding).
            BitField(i=Bits(6, 28), j=Bits(3, 5), k=Bits(8, 7)):    b'\x72\x83\x80',
            BitField(i=Bits(6, 63), j=Bits(3, 0), k=Bits(8, 15)):   b'\xFC\x07\x80'
        }

        HydraSettings.endian = BigEndian

        for bitfield, result in tests.items():
            # Serialization
            self.assertEqual(result, bitfield.format(bitfield.default_value))

            # Deserialization
            self.assertEqual(bitfield.parse(result), bitfield.default_value)

    def test_bitfield_enforces_invalid_keys(self):
        bitfield = BitField(a=Bits(15), b=Bits(3))

        with self.assertRaises(KeyError):
            bitfield.format({'a': 3, 'b': 5, 'c': 10})