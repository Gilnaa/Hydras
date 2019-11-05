"""
Contains the validation components of this library.

:file: validators.py
:date: 15/09/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *
from typing import Iterable
import abc


class ValidationError(ValueError):
    def __init__(self, value, field_name: str = None, parent=None, inner_error=None):
        self.value = value
        self.field_name = field_name
        self.parent = parent
        self.inner_exception = inner_error
        super(ValidationError, self).__init__(f'Validation error for field {field_name}')


class Validator(abc.ABC):
    @abc.abstractmethod
    def __call__(self, value: Any) -> bool: ...


class TrueValidator(Validator):
    """ An optimist validator. """

    def __call__(self, value: Any) -> bool:
        return True


class FalseValidator(Validator):
    """ A realist validator. """

    def __call__(self, value: Any) -> bool:
        return False


class RangeValidator(Validator):
    def __init__(self, min_val, max_val, inclusive=True):
        """
        Construct a new RangeValidator instance.

        :param min_val:     The lower bound of the range.
        :param max_val:     The upper bound of the range.
        :param inclusive:   Determines whether the range check includes the upper bound.
        """
        self.min_val = min_val
        self.max_val = max_val
        self.inclusive = inclusive

    def __call__(self, value: Union[int, float]) -> bool:
        if self.inclusive:
            return self.min_val <= value <= self.max_val
        return self.min_val <= value < self.max_val


class ExactValueValidator(Validator):
    def __init__(self, expected_value):
        """
        Constructs a new ExactValueValidator.

        :param expected_value:  The single valid value.
        """
        self.expected_value = expected_value

    def __call__(self, value: Any) -> bool:
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

        :param max_bit_size:    The desired valid bit size. (inclusive)
        """
        self.max_bit_size = max_bit_size

    def __call__(self, value: int) -> bool:
        return (value >= 0) and (value.bit_length() <= self.max_bit_size)


class ListValidator(Validator):
    """ A validator that checks if a value is in a set of items"""

    def __init__(self, lst: Iterable):
        self.items = lst

    def __call__(self, value):
        return value in self.items
