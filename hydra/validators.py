"""
Contains the validation components of this library.

:file: validators.py
:date: 15/09/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

from .utils import *
from .compatibility import *


class Validator(object):
    """ A base class for validators. """

    def validate(self, value):
        """
        Determine the validity of the specified item.

        :param value:   The value to validate.

        :return:    `True` if the value is valid; `False` otherwise.
        """
        raise NotImplementedError()


class TrueValidator(Validator):
    """ An optimist validator. """
    def validate(self, value):
        """
        Determine the validity of the specified item.

        :param value:   The value to validate.

        :return:    `True`.
        """
        return True


class FalseValidator(Validator):
    """ A realist validator. """
    def validate(self, value):
        """
        Determine the validity of the specified item.

        :param value:   The value to validate.

        :return:    `False`.
        """
        return False


class RangeValidator(Validator):
    """ A validator that does a range check. """
    def __init__(self, min_val, max_val, inclusive=True):
        """
        Construct a new RangeValidator instance.

        :param min_val:     The lower bound of the range.
        :param max_val:     The upper bound of the range.
        :param inclusive:   Determines whether the range check
                            includes the upper bound. [Default: True]
        """
        if inclusive:
            self.range = xrange(min_val, max_val + 1)
        else:
            self.range = xrange(min_val, max_val)

    def validate(self, value):
        """
        Determine the validity of the specified item.

        :param value:   The value to validate.

        :return:    `True` if the value is within range; `False` otherwise.
        """
        return value in self.range


class ExactValueValidator(Validator):
    """ A validator that checks for an exact value. """
    def __init__(self, expected_value):
        """
        Constructs a new ExactValueValidator.

        :param expected_value:  The single valid value.
        """
        self.expected_value = expected_value

    def validate(self, value):
        """
        Determine the validity of the specified item.

        :param value:   The value to validate.

        :return:    `True` if the value matches the expected value; `False` otherwise.
        """
        return value == self.expected_value


class BitSizeValidator(Validator):
    """
    A validator that ensures the bit-size of an integer is in (0..N).

    Example:
        validator = BitSizeValidator(5)
        validator.validate(0b0)      #=> True  (Size = 0)
        validator.validate(0b1110)   #=> True  (Size = 4)
        validator.validate(0b100000) #=> False (Size = 6)
        validator.validate(-1)       #=> False (Value < 0)
    """

    def __init__(self, max_bit_size):
        """
        Construct a new BitSizeValidator.

        :param max_bit_size:    The desired valid bit size.
        """
        self.max_bit_size = max_bit_size

    def validate(self, value):
        """
        Determine the validity of the specified item.

        :param value:   The value to validate.

        :return:    `True` if the value has a valid bit size; `False` otherwise.
        """
        return (value >= 0) and (bit_length(value) <= self.max_bit_size)


class ListValidator(Validator):
    """ A validator that checks if a value is in a list of valid values. """

    def __init__(self, lst):
        """
        Construct a new ListValidator.

        :param lst:    The list of valid values.
        """
        self.items = lst

    def validate(self, value):
        """
        Determine the validity of the specified item.

        :param value:   The value to validate.

        :return:    `True` if the value exists in the list; `False` otherwise.
        """
        return value in self.items
