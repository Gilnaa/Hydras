"""
Contains non-trivial type formatters.

:file:  vectors.py
:date:  27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .base import *
from .scalars import *
from .utils import *

import copy
import inspect


class Pad(Serializer):

    """ A type formatter whose purpose is to act as a data-less padding."""

    def __init__(self, length=1, *args, **kwargs):
        """
        Initialize this `Pad` instance.

        :param length:  The size of this padding, in bytes.
        """
        self.length = length
        super(Pad, self).__init__(b'\x00' * length, *args, **kwargs)

    def __len__(self):
        """ Return the size of this padding, in bytes."""
        return self.length

    def render(self, value, name):
        from binascii import hexlify
        return '{}: {}'.format(name, hexlify(value))

    def format(self, value, settings=None):
        return value

    def parse(self, raw_data, settings=None):
        return fit_bytes_to_size(raw_data, self.length)


class Array(Serializer):

    """
    A type formatter which enables the developer to format a list of items.

    The default value's type is a byte (uint8_t), but can subtituted for any Struct or Scalar.
    """

    def __init__(self, length, items_type=uint8_t, default_value=None, *args, **kwargs):
        """
        Initialize this Array object.

        Note:
            `items_type` can be a class derived from `Scalar`, a class derived
            from `Struct` or an object of this class.
            Any other value will cause a `TypeError` to be raised.

        :param length:          The number of items in this Array.
        :param items_type:      The type of each item in the Array. [default: `uint8_t`]
        :param default_value:   The default value for the Array.    [default: `None`]

        :param args:            A paramater list to be passed to the base class.
        :param kwargs:          A paramater dict to be passed to the base class.
        """
        # Note: line below might throw exception.
        alternate_default_value = self.init_type_resolver(items_type, length)

        self.length = length
        self.byte_size = length * len(self.formatter)

        if default_value is None:
            default_value = alternate_default_value

        super(Array, self).__init__(default_value, *args, **kwargs)

    def init_type_resolver(self, items_type, length):
        """ A helper method for the constructor. """
        # type is a Struct object.
        t = get_as_type(items_type)

        # type is a Struct type/class.
        if issubclass(t, Struct):
            self.formatter = NestedStruct(items_type)
            return tuple(t() if inspect.isclass(items_type) else copy.deepcopy(items_type) for i in range(length))
        # type is a Scalar class.
        elif issubclass(t, Serializer):
            self.formatter = get_as_value(items_type)
            return tuple(self.formatter.default_value for _ in range(length))
        else:
            raise TypeError('Array: items_type should be a Serializer or a Struct')

    def format(self, value, settings=None):
        """ Return a serialized representation of this object. """
        settings = HydraSettings.resolve(self.settings, settings)

        return padto(b''.join(
            self.formatter.format(s, settings) for s in value
        ), len(self))

    def parse(self, raw_data, settings=None):
        if len(raw_data) != len(self):
            raise ValueError('Raw data is not in the correct length.')

        settings = HydraSettings.resolve(self.settings, settings)
        raw_data = string2bytes(raw_data)

        if self.default_value is not None:
            t = get_as_type(self.default_value)
            if t in (str, bytes):
                f = lambda g: b''.join(string2bytes(chr(c)) for c in g)
            else:
                f = t
        else:
            f = tuple

        return f(
            self.formatter.parse(raw_data[begin:begin+len(self.formatter)], settings)
            for begin in range(0, len(self), len(self.formatter))
        )

    def __len__(self):
        """ Return the size of this Array in bytes."""
        return self.byte_size

    def values_equal(self, a, b):
        if isinstance(a, list):
            a = self.format(a)
        if isinstance(b, list):
            b = self.format(b)
        return a == b

    def validate_assignment(self, value):
        if not any([isinstance(value, t) for t in [str, tuple, list, bytes]]):
            raise TypeError('Assigned value must be a string, tuple, or a list.')

        if len(value) > self.length:
            raise ValueError('Assigned array is too long.')

        for i in value:
            self.formatter.validate_assignment(i)


class VariableArray(Serializer):

    """
    A type formatter which enables the developer to format a list of items.

    The default value's type is a byte (uint8_t), but can subtituted for any Struct or Scalar.
    """

    def __init__(self, min_length, max_length, items_type=uint8_t, default_value=None, *args, **kwargs):
        """
        Initialize this Array object.

        Note:
            `items_type` can be a class derived from `Scalar`, a class derived
            from `Struct` or an object of this class.
            Any other value will cause a `TypeError` to be raised.

        :param length:          The number of items in this Array.
        :param items_type:      The type of each item in the Array. [default: `uint8_t`]
        :param default_value:   The default value for the Array.    [default: `None`]

        :param args:            A paramater list to be passed to the base class.
        :param kwargs:          A paramater dict to be passed to the base class.
        """
        # Note: line below might throw exception.
        alternate_default_value = self.init_type_resolver(items_type, min_length)

        self.min_length = min_length
        self.max_length = max_length
        self.byte_size = min_length * len(self.formatter)

        if default_value is None:
            default_value = alternate_default_value

        self.validate_assignment(default_value)

        super(VariableArray, self).__init__(default_value, *args, **kwargs)

    def init_type_resolver(self, items_type, length):
        """ A helper method for the constructor. """
        # type is a Struct object.
        t = get_as_type(items_type)

        # type is a Struct type/class.
        if issubclass(t, Struct):
            self.formatter = NestedStruct(items_type)
            return tuple(t() if inspect.isclass(items_type) else copy.deepcopy(items_type) for i in range(length))
        # type is a Scalar class.
        elif issubclass(t, Serializer):
            self.formatter = get_as_value(items_type)
            return tuple(self.formatter.default_value for _ in range(length))
        else:
            raise TypeError('Array: items_type should be a Serializer or a Struct')

    def format(self, value, settings=None):
        """ Return a serialized representation of this object. """
        settings = HydraSettings.resolve(self.settings, settings)

        return padto(b''.join(
            self.formatter.format(s, settings) for s in value
        ), len(self))

    def parse(self, raw_data, settings=None):
        if len(raw_data) > self.max_length * len(self.formatter):
            raise ValueError('Raw data is too long for variable length array.')
        elif len(raw_data) < self.min_length * len(self.formatter):
            raise ValueError('Raw data is too short for variable length array.')

        settings = HydraSettings.resolve(self.settings, settings)
        raw_data = string2bytes(raw_data)

        if self.default_value is not None:
            t = get_as_type(self.default_value)
            if t in (str, bytes):
                f = lambda g: b''.join(string2bytes(chr(c)) for c in g)
            else:
                f = t
        else:
            f = tuple

        fmt_size = len(self.formatter)
        return f(
            self.formatter.parse(raw_data[begin:begin+len(self.formatter)], settings)
            for begin in range(0, min(self.max_length * fmt_size, len(raw_data)), fmt_size)
        )

    def __len__(self):
        """ Return the *minimal* size of this Array in bytes."""
        return self.byte_size

    def values_equal(self, a, b):
        if isinstance(a, list):
            a = self.format(a)
        if isinstance(b, list):
            b = self.format(b)
        return a == b

    def is_constant_size(self):
        return False

    def validate_assignment(self, value):
        # When using Python 2, `bytes` is an alias to `str`.
        if not isinstance(value, (bytes, tuple, list)):
            raise TypeError('Assigned value must be a string, tuple, or a list.')
            
        if len(value) < self.min_length:
            raise ValueError("Data is too short for serialization of VLA.")
        elif len(value) > self.max_length:
            raise ValueError("Data is too long for serialization of VLA.")

        # Make sure each element in the collection is also valid according to `self.formatter`.
        for i in value:
            # When using Python 2, and `bytes = str`,
            # the iteration emits single character strings instead of integers
            if isinstance(i, str):
                assert len(i) == 1
                i = ord(i)

            self.formatter.validate_assignment(i)

    def get_actual_length(self, value):
        return len(value) * len(self.formatter)
