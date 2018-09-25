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

        self.literals = enum_values
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
        return (value in self.literals.values()) and (super(Enum, self).validate(value))

    def format(self, value, settings=None):
        """ Formats the given value into its binary form. """
        if isinstance(value, str):
            value = self[value]

        return self.scalar_formatter.format(value, settings)

    def parse(self, raw_data, settings=None):
        """ Parses the given raw_data into an enum constant. """
        return self.scalar_formatter.parse(raw_data, settings)

    def render(self, value, name):
        """ Returns a displayable string for the given value. """
        if HydraSettings.render_enums_as_integers:
            cname = self.get_const_name(value)
            value = '{} ({})'.format('?' if cname is None else cname, value)
            
        return '%s: %s' % (name, value)

    def get_const_name(self, num):
        """ Get the name of the constant from a number or a Literal object. """
        if not isinstance(num, int_types):
            raise TypeError()

        matching_literals = tuple(n for n, v in self.literals.items() if v == num)

        if len(matching_literals) == 0:
            return None

        return matching_literals[0]

    def __getattr__(self, item):
        """ Support the `enum.constant_name` notation. """
        if item not in self.literals:
            raise AttributeError("Invalid enum literal name %s. Available literals are %s" % (item, str(self.literals.keys())))

        return self.literals[item]

    def __getitem__(self, item):
        """ Support the `enum["constant_name"]` notation. """
        return getattr(self, item)

    def __len__(self):
        """ The byte size of the enum. """
        return len(self.scalar_formatter)

    def __iter__(self):
        return self.literals.items().__iter__()
