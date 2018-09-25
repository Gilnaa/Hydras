#!/usr/bin/env python
"""
Contains tests for the variable length array.

:file: VLA.py
:date: 22/03/2018
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

from hydra import *
import unittest


class TestVLA(unittest.TestCase):
    def setUp(self):
        HydraSettings.push()
        HydraSettings.endian = LittleEndian

    def tearDown(self):
        HydraSettings.pop()

    def test_default_value(self):
        # Default value should be the minimal length
        self.assertEqual(VariableArray(5, 7).default_value, (0, ) * 5)

    def test_vla_sizes(self):
        a = VariableArray(1, 4, uint16_t)

        # Assert the len(Formatter) issues the minimal length
        self.assertEqual(len(a), len(uint16_t()))

        # The "real" length should depend on the used value
        self.assertEqual(a.get_actual_length([1]),              len(uint16_t()) * 1)
        self.assertEqual(a.get_actual_length([1, 2]),           len(uint16_t()) * 2)
        self.assertEqual(a.get_actual_length([1, 2, 3]),        len(uint16_t()) * 3)
        self.assertEqual(a.get_actual_length([1, 2, 3, 4]),     len(uint16_t()) * 4)

    def test_vla_wrong_sizes_on_assignment(self):
        class FUBAR(Struct):
            florp = VariableArray(1, 4)

        nimrod_fucking_kaplan = FUBAR()

        # Positive tests
        for i in xrange(1, 5):
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
            a = u8()
            b = VariableArray(1, 15)

        # Negative case
        with self.assertRaises(TypeError):
            class Blarg(Struct):
                b = VariableArray(1, 15)
                a = u8()

    def test_vla_value_assignment_checks(self):
        class Florper(Struct):
            a = VariableArray(4, 16)

        a = Florper()

        with self.assertRaises(ValueError):
            a.a = [0] * 2

        with self.assertRaises(ValueError):
            a.a = [0] * 18

        a.a = [0] * 5

if __name__ == '__main__':
    unittest.main()
