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


class RangeValidated(Struct):
    member = u8(10, validator=RangeValidator(10, 100))


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
        with self.assertRaises(ValidationError):
            RangeValidated.deserialize(b'\x00')
        #
        # try:
        #     RangeValidated.deserialize(b'\x00')
        # except ValidationError as e:
        #     print(e)

        # Make sure no exceptions are raised when validation is off.
        HydraSettings.validate = False

        try:
            Unvalidated.deserialize(b'\x00')
            RangeValidated.deserialize(b'\x00')
        except ValidationError:
            self.fail("An exception was raised even when turned off by user.")

    def test_exact_value_validation(self):
        formatter = u8(13, validator=ExactValueValidator(13))
        formatter.validate(13)
        with self.assertRaises(ValidationError):
            formatter.validate(0)

    def test_range_validation(self):
        inclusive_formatter = i32(0, validator=RangeValidator(-15, 15))
        exclusive_formatter = i32(0, validator=RangeValidator(-15, 15, inclusive=False))

        # Inclusive
        inclusive_formatter.validate(-15)
        inclusive_formatter.validate(-3)
        inclusive_formatter.validate(0)
        inclusive_formatter.validate(7)
        inclusive_formatter.validate(15)

        with self.assertRaises(ValidationError):
            inclusive_formatter.validate(-100)
        with self.assertRaises(ValidationError):
            inclusive_formatter.validate(1000000)
        with self.assertRaises(ValidationError):
            inclusive_formatter.validate(1 << 16)

        # Exclusive
        exclusive_formatter.validate(-15)
        exclusive_formatter.validate(-3)
        exclusive_formatter.validate(0)
        exclusive_formatter.validate(7)

        with self.assertRaises(ValidationError):
            exclusive_formatter.validate(15)
        with self.assertRaises(ValidationError):
            exclusive_formatter.validate(-100)
        with self.assertRaises(ValidationError):
            exclusive_formatter.validate(1000000)
        with self.assertRaises(ValidationError):
            exclusive_formatter.validate(1 << 16)

    def test_bit_length_validation(self):
        formatter = i64(0, validator=BitSizeValidator(10))

        formatter.validate(1 << 9)
        formatter.validate((1 << 10) - 1)
        formatter.validate(0)

        with self.assertRaises(ValidationError):
            formatter.validate(-1)
        with self.assertRaises(ValidationError):
            formatter.validate(1 << 10)
        with self.assertRaises(ValidationError):
            formatter.validate(1 << 11)

    def test_lambda_validation(self):
        formatter = u8(5, validator=lambda value: value > 4)
        formatter.validate(6)
        with self.assertRaises(ValidationError):
            formatter.validate(0)
