#!/usr/bin/env python
"""
Contains tests for validation feature.

:file: ValidationTests.py
:date: 28/01/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *


class Unvalidated(Struct):
    member = u8


class FalseValidated(Struct):
    member = u8(0, validator=FalseValidator())


class ValidationTests(HydrasTestCase):
    """ A testcase for testing struct member validation. """

    def test_struct_validation(self):
        """ Test that a struct will throw an exception when a validation fails."""
        # Make sure no exception is thrown when there's no validation rules.
        try:
            Unvalidated.deserialize(b'\x00')
        except ValueError:
            self.fail("Valid data deemed invalid by framework.")

        # Make sure that an exception is raised when needed.
        with self.assertRaises(ValueError):
            FalseValidated.deserialize(b'\x00')

        # Make sure no exceptions are raised when validation is off.
        HydraSettings.validate = False

        try:
            Unvalidated.deserialize(b'\x00')
            FalseValidated.deserialize(b'\x00')
        except ValueError:
            self.fail("An exception was raised even when turned off by user.")

    def test_exact_value_validation(self):
        formatter = u8(0, validator=ExactValueValidator(13))
        self.assertTrue(formatter.validate(13))
        self.assertFalse(formatter.validate(0))

    def test_range_validation(self):
        inclusive_formatter = u32(0, validator=RangeValidator(-15, 15))
        exclusive_formatter = u32(0, validator=RangeValidator(-15, 15, inclusive=False))

        # Inclusive
        self.assertTrue(inclusive_formatter.validate(-15))
        self.assertTrue(inclusive_formatter.validate(-3))
        self.assertTrue(inclusive_formatter.validate(0))
        self.assertTrue(inclusive_formatter.validate(7))
        self.assertTrue(inclusive_formatter.validate(15))

        self.assertFalse(inclusive_formatter.validate(-100))
        self.assertFalse(inclusive_formatter.validate(1000000))
        self.assertFalse(inclusive_formatter.validate(1 << 16))

        # Exclusive
        self.assertTrue(exclusive_formatter.validate(-15))
        self.assertTrue(exclusive_formatter.validate(-3))
        self.assertTrue(exclusive_formatter.validate(0))
        self.assertTrue(exclusive_formatter.validate(7))

        self.assertFalse(exclusive_formatter.validate(15))
        self.assertFalse(exclusive_formatter.validate(-100))
        self.assertFalse(exclusive_formatter.validate(1000000))
        self.assertFalse(exclusive_formatter.validate(1 << 16))

    def test_bit_length_validation(self):
        formatter = u64(0, validator=BitSizeValidator(10))

        self.assertTrue(formatter.validate(1 << 9))
        self.assertTrue(formatter.validate((1 << 10) - 1))
        self.assertTrue(formatter.validate(0))

        self.assertFalse(formatter.validate(-1))
        self.assertFalse(formatter.validate(1 << 10))
        self.assertFalse(formatter.validate(1 << 11))

    def test_lambda_validation(self):
        formatter = u8(0, validator=lambda value: value > 4)
        self.assertTrue(formatter.validate(6))
        self.assertFalse(formatter.validate(0))
