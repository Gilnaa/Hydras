"""
:file: enum_class.py

Contains a more natural enum implementation.

:date: 10/06/2016
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
"""

from .base import *
from .scalars import *
import collections


class Literal(object):
    """ A single Enum-Constant """

    def __init__(self, value=None):
        """
        Initialize the enum constant literal.
        :param value:   [Optional] The literal numeric value.
        """
        self.id = get_id()
        self.value = value


class EnumClass(TypeFormatter):
    """ An enum formatter that can be shared between structs. """
    def __init__(self, default_value=None, type_formatter=None, *args, **kwargs):
        raw_literals = vars(type(self)).items()
        raw_literals = list(filter(lambda tuple: isinstance(tuple[1], Literal), raw_literals))
        raw_literals.sort(key=lambda tuple: tuple[1].id)

        self.enum_literals = collections.OrderedDict()
        self.formatter = (type_formatter or UInt32)()

        # Initialize static members
        next_expected_value = 0
        for name, literal in raw_literals:
            if literal.value is None:
                literal.value = next_expected_value
            next_expected_value = literal.value + 1
            self.enum_literals[name] = literal

        # Validate the default_value
        if default_value is None:
            default_value = list(self.enum_literals.values())[0]
        elif isinstance(default_value, str):
            if default_value not in self.enum_literals:
                raise ValueError('Literal name does not exist: %s' % default_value)
            default_value = self.enum_literals[default_value].value
        elif isinstance(default_value, Literal):
            if default_value not in self.enum_literals.values():
                raise ValueError('Literal object is not included in the enum.')
            default_value = default_value.value
        elif isinstance(default_value, int):
            if not self.is_constant_valid(default_value):
                raise ValueError('Literal constant is not included in the enum: %d' % default_value)

        super(EnumClass, self).__init__(default_value, *args, **kwargs)

    def format(self, value, settings=None):
        """ Format the enum value into its binary form. """
        settings = self.resolve_settings(settings)

        if isinstance(value, Literal):
            value = value.value
        elif isinstance(value, str):
            value = self.enum_literals[value].value

        return self.formatter.format(value, settings)

    def parse(self, raw_data, settings=None):
        """ Parse the raw_data into an enum literal. """
        settings = self.resolve_settings(settings)
        value = self.formatter.parse(raw_data, settings)

        if settings['strong_enum_literals'] and not self.is_constant_valid(value):
            raise ValueError('Parsed enum value is unknown: %d' % value)

        return value

    def validate(self, value):
        """ Validate the given enum value. """
        if HydraSettings.strong_enum_literals and not self.is_constant_valid(value):
            return False

        return super(EnumClass, self).validate(value)

    def __len__(self):
        """ Get the byte size of the formatter. """
        return len(self.formatter)

    def is_constant_valid(self, num):
        """ Determine if the given number is a valid enum literal. """
        matching_literals = list(filter(lambda tuple: tuple[1].value == num, self.enum_literals.items()))
        return len(matching_literals) > 0

    def get_constant_name(self, num):
        """ Get the name of the constant from a number or a Literal object. """
        if isinstance(num, int):
            matching_literals = list(filter(lambda tuple: tuple[1].value == num, self.enum_literals.items()))
        elif isinstance(num, Literal):
            matching_literals = list(filter(lambda tuple: tuple[1].id == num.id, self.enum_literals.items()))
        else:
            raise TypeError()

        if len(matching_literals) == 0:
            return None

        return matching_literals[0][0]

    def render(self, value, name):
        """ Render the enum value. """
        if HydraSettings.render_enums_as_integers:
            value = self.render_integer(value)
        else:
            value = self.render_string(value)

        return '%s = %s' % (name, value)

    def render_integer(self, value):
        """ Render the enum value as an integer. """
        if isinstance(value, int):
            return str(value)

        if isinstance(value, str):
            return str(self.enum_literals[value].value)

        if isinstance(value, Literal):
            return str(value.value)

        raise ValueError()

    def render_string(self, value):
        """ Render the enum value as a string. """
        template = '%s'
        if HydraSettings.full_enum_names:
            template = type(self).__name__ + '.%s'

        if isinstance(value, int) or isinstance(value, Literal):
            return template % self.get_constant_name(value)

        if isinstance(value, str):
            return template % value

        raise ValueError()

    def values_equal(self, a, b):
        def normalize_value(val):
            if isinstance(val, int):
                return val
            if isinstance(val, str):
                return self.enum_literals[val].value
            if isinstance(val, Literal):
                return val.value

            raise ValueError()

        return (normalize_value(a) == normalize_value(b))
