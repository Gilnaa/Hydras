"""
:file: scalars.py

Contains various primitive type formatters.

:date: 15/09/2015
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
"""

from .utils import *
from .compatibility import *


class Validator(object):
    """ A base class for validators. """

    def validate(self, value):
        raise NotImplementedError()


class TrueValidator(Validator):
    """ An optimist validator. """
    def validate(self, value):
        return True


class FalseValidator(Validator):
    """ A realist validator. """
    def validate(self, value):
        return False


class RangeValidator(Validator):
    """ A validator that does a range check. """
    def __init__(self, min_val, max_val, inclusive=True):
        if inclusive:
            self.range = xrange(min_val, max_val + 1)
        else:
            self.range = xrange(min_val, max_val)

    def validate(self, value):
        return value in self.range


class ExactValueValidator(Validator):
    """ A validator that checks for an exact value. """
    def __init__(self, expected_value):
        self.expected_value = expected_value

    def validate(self, value):
        return value == self.expected_value


class BitSizeValidator(Validator):
    """ A validator that checks for the bit size of a number."""
    def __init__(self, max_bit_size):
        self.max_bit_size = max_bit_size

    def validate(self, value):
        return (value >= 0) and (bit_length(value) <= self.max_bit_size)