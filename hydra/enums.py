"""
:file: enums.py

Contains the enum type formatter.

:date: 20/01/2016
:authors:
    - Kfir Gollan
"""

import inspect
from .base import *
from .scalars import *


class Enum(TypeFormatter):
    """
    The base class for enumerator scalars provided by the library.

    Example:
        class Example(Struct):
            field = Enum('A', {'A': 20, 'B': 40})

        struct = Example()
        struct.field = Example.field.A
    """

    def __init__(self, default_value, enum_values, format_type=UInt32, *args, **kwargs):
        """
        Constructs a new Enum

        :param default_value:   The name of the default enum value.
        :param enum_values:     A dictionary of enum values.
        :param format_type:     [Optional] A scalar specifying the format of the enum. (Default = UInt8)
        """
        if default_value not in enum_values:
            raise ValueError('The provided default value is not a valid enum key.')

        self.items = enum_values
        if inspect.isclass(format_type):
            self.scalar_formatter = format_type()
        else:
            self.scalar_formatter = format_type

        super(Enum, self).__init__(enum_values[default_value], *args, **kwargs)

    def values_equal(self, a, b):
        """ Determines whether the given enum values are equal. """
        if isinstance(a, str):
            a = self[a]
        if isinstance(b, str):
            b = self[b]

        return a == b

    def validate(self, value):
        """ Validate the given value as an enum member. """
        return (value in self.items.values()) and (super(Enum, self).validate(value))

    def format(self, value, settings=None):
        """ Formats the given value into its binary form. """
        if isinstance(value, str):
            value = self[value]

        return self.scalar_formatter.format(value, settings)

    def parse(self, raw_data, settings=None):
        """ Parses the given raw_data into an enum constant. """
        return self.scalar_formatter.parse(raw_data, settings)

    def __getattr__(self, item):
        """ Support the `enum.constant_name` notation. """
        if item not in self.items:
            raise AttributeError

        return self.items[item]

    def __getitem__(self, item):
        """ Support the `enum["constant_name"]` notation. """
        return getattr(self, item)

    def __len__(self):
        """ The byte size of the enum. """
        return len(self.scalar_formatter)
