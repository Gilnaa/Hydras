#!/usr/bin/env python
"""
Contains tests for the variable length array.

:file: VLA.py
:date: 22/03/2018
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *


class TestVLA(HydrasTestCase):

    def test_default_value(self):
        # Default value should be the minimal length
        self.assertEqual(u8[5:7]().get_initial_value(), bytearray(5))
        self.assertEqual(u16[5:7]().get_initial_value(), [0] * 5)

    def test_vla_sizes(self):
        class Florp(Struct):
            a = u16[1:4]

        # Assert the len(Formatter) issues the minimal length
        self.assertEqual(len(Florp), u16.byte_size)

        # The "real" length should depend on the used value
        f = Florp()
        f.a = [1]
        self.assertEqual(len(f), u16.byte_size * 1)
        f.a = [1, 2]
        self.assertEqual(len(f), u16.byte_size * 2)
        f.a = [1, 2, 3]
        self.assertEqual(len(f), u16.byte_size * 3)
        f.a = [1, 2, 3, 4]
        self.assertEqual(len(f), u16.byte_size * 4)

    def test_vla_wrong_sizes_on_assignment(self):
        class FUBAR(Struct):
            florp = u8[1:4]

        nimrod_fucking_kaplan = FUBAR()

        # Positive tests
        for i in range(1, 5):
            nimrod_fucking_kaplan.florp = [0] * i

        # Accept a sub-minimum length array. The serialized result should be padded.
        nimrod_fucking_kaplan.florp = []

        # above- maximal length
        with self.assertRaises(ValueError):
            nimrod_fucking_kaplan.florp = [0] * 5

    def test_vla_must_be_at_end_of_struct(self):
        # Positive case
        class Florp(Struct):
            a = u8
            b = u8[1:15]

        self.assertFalse(Florp.is_constant_size())

        # Negative case
        with self.assertRaises(TypeError):
            class Blarg(Struct):
                b = u8[1:15]
                a = u8

        with self.assertRaises(TypeError):
            class Zlorp(Struct):
                a = Florp
                b = u8

    def test_unaligned_raw_data(self):
        # Positive case
        class Florp(Struct):
            b = u16[0:15]

        with self.assertRaises(ValueError):
            Florp.deserialize(b'\x00\x00\x00')

    def test_open_ended_slice(self):
        class UpperBound(Struct):
            b = u8[:3]

        self.assertEqual(len(UpperBound.deserialize(b'').b), 0)
        self.assertEqual(len(UpperBound.deserialize(b'\x00\x00\x00').b), 3)

        class LowerBound(Struct):
            b = u8[3:]

        self.assertEqual(len(LowerBound.deserialize(b'\x00\x00\x00').b), 3)
        self.assertEqual(len(LowerBound.deserialize(b'\x00' * 100).b), 100)

        class Unbound(Struct):
            b = u8[:]

        self.assertEqual(len(Unbound.deserialize(b'\x00\x00\x00').b), 3)
        self.assertEqual(len(Unbound.deserialize(b'\x00' * 100).b), 100)
        self.assertEqual(len(Unbound.deserialize(b'').b), 0)

    def test_vla_derivation(self):
        class ConstantSizeStruct(Struct):
            d = u8

        class VLA(Struct):
            c = u8
            a = u8[1:2]

        # This derivation is valid since we're not adding any members
        class ValidDerivation(VLA):
            pass

        with self.assertRaises(TypeError):
            class InvalidDerivation(VLA):
                b = u8
        with self.assertRaises(TypeError):
            class InvalidMutiDerivation(VLA, ConstantSizeStruct):
                pass

    def test_vla_value_assignment_checks(self):
        class Florper(Struct):
            a = u8[4:16]

        a = Florper()

        a.a = [0] * 2

        with self.assertRaises(ValueError):
            a.a = [0] * 18

        a.a = [0] * 5
