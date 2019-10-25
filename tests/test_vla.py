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
        self.assertEqual(u8[5:7].default_value, (0, ) * 5)

    def test_vla_sizes(self):
        a = u16[1:4]

        # Assert the len(Formatter) issues the minimal length
        self.assertEqual(len(a), len(u16))

        # The "real" length should depend on the used value
        self.assertEqual(a.get_actual_length([1]), len(u16) * 1)
        self.assertEqual(a.get_actual_length([1, 2]), len(u16) * 2)
        self.assertEqual(a.get_actual_length([1, 2, 3]), len(u16) * 3)
        self.assertEqual(a.get_actual_length([1, 2, 3, 4]), len(u16) * 4)

    def test_vla_wrong_sizes_on_assignment(self):
        class FUBAR(Struct):
            florp = u8[1:4]

        nimrod_fucking_kaplan = FUBAR()

        # Positive tests
        for i in range(1, 5):
            nimrod_fucking_kaplan.florp = [0] * i

        # sub- minimal length
        with self.assertRaises(ValueError):
            nimrod_fucking_kaplan.florp = []

        # above- maximal length
        with self.assertRaises(ValueError):
            nimrod_fucking_kaplan.florp = [0] * 5

    def test_vla_must_be_at_end_of_struct(self):
        # Positive case
        class Florp(Struct):
            a = u8
            b = u8[1:15]

        # Negative case
        with self.assertRaises(TypeError):
            class Blarg(Struct):
                b = u8[1:15]
                a = u8

    def test_vla_derivation(self):
        class ConstantSizeStruct(Struct):
            d = u8

        class VLA(Struct):
            c = u8
            a = u8[1:2]

        # This derivation is valid since we're not adding any members
        class ValidDerivation(VLA):
            pass

        class ValidMutiDerivation(ConstantSizeStruct, VLA):
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

        with self.assertRaises(ValueError):
            a.a = [0] * 2

        with self.assertRaises(ValueError):
            a.a = [0] * 18

        a.a = [0] * 5
