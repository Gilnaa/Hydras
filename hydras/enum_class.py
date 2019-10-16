"""
:file: enum_class.py

Contains a more natural enum implementation.

:date: 10/06/2016
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

from .base import *
from .scalars import *
import collections


class Literal(object):
    def __init__(self, value=None, enum_name=None, literal_name=None):
        if value is not None and not isinstance(value, int):
            raise TypeError('value must be an int type')
        self.value = value
        self._enum_name = enum_name
        self._literal_name = literal_name

    def __eq__(self, other):
        if isinstance(other, Literal):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return TypeError()

    def __int__(self):
        return self.value

    def __repr__(self):
        return '{}.{}'.format(self._enum_name, self._literal_name)


class EnumClassMeta(SerializerMeta):
    def __new__(cls, name, bases, attributes):
        if not hasattr(cls, '_metadata') or cls._metadata['name'] != name:
            metadata = {
                'name': name,
                'literals': None
            }

            literals = (
                (k, v) for k, v in attributes.items()
                if isinstance(v, (int, Literal)) and not k.startswith('_')
            )
            literals_dict = collections.OrderedDict()

            # Initialize static members
            next_expected_value = 0
            for lit_name, literal in literals:
                if literal is None:
                    lit_value = next_expected_value
                elif isinstance(literal, Literal):
                    # Update the literal object before taking its value
                    lit_value = literal.value or next_expected_value
                else:
                    lit_value = literal

                next_expected_value = lit_value + 1
                literals_dict[lit_name] = Literal(lit_value, name, lit_name)
                attributes[lit_name] = literals_dict[lit_name]

            metadata['literals'] = literals_dict
            setattr(cls, '_metadata', metadata)
        attributes.update({'_metadata': cls._metadata})
        return super(EnumClassMeta, cls).__new__(cls, name, bases, attributes)

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()


class EnumClass(Serializer, metaclass=EnumClassMeta):
    """ An enum formatter that can be shared between structs. """
    def __init__(self, default_value=None, type_formatter=None, *args, **kwargs):
        self.enum_literals = collections.OrderedDict()
        self.formatter = get_as_value(type_formatter or uint32_t)

        # Validate the default_value
        if default_value is None:
            default_value = list(self.literals.values())[0]
        elif isinstance(default_value, str):
            if default_value not in self.literals:
                raise ValueError('Literal name does not exist: %s' % default_value)
            default_value = self.literals[default_value].value
        elif isinstance(default_value, Literal):
            if default_value.value not in self.literals.values():
                raise ValueError('Literal object is not included in the enum.')
            default_value = default_value.value
        elif isinstance(default_value, int):
            if not self.is_constant_valid(default_value):
                raise ValueError('Literal constant is not included in the enum: %d' % default_value)

        super(EnumClass, self).__init__(default_value, *args, **kwargs)

    def format(self, value, settings=None):
        """ Format the enum value into its binary form. """
        settings = self.resolve_settings(settings)

        if isinstance(value, str):
            value = self.literals[value]

        return self.formatter.format(int(value), settings)

    def parse(self, raw_data, settings=None):
        """ Parse the raw_data into an enum literal. """
        settings = self.resolve_settings(settings)
        value = self.formatter.parse(raw_data, settings)

        if settings['strong_enum_literals'] and not self.is_constant_valid(value):
            raise ValueError('Parsed enum value is unknown: %d' % value)

        return value

    def validate(self, value):
        """ Validate the given enum value. """
        if HydraSettings.strong_enum_literals and \
                not self.is_constant_valid(value.value if isinstance(value, Literal) else value):
            return False

        return super(EnumClass, self).validate(value)

    @property
    def literals(self):
        return self._metadata['literals']

    def __len__(self):
        """ Get the byte size of the formatter. """
        return len(self.formatter)

    def is_constant_valid(self, num):
        """ Determine if the given number is a valid enum literal. """
        return any(v == num for _, v in self.literals.items())

    def get_const_name(self, num):
        """ Get the name of the constant from a number or a Literal object. """
        if isinstance(num, Literal):
            num = num.value
        elif not isinstance(num, int):
            raise TypeError()

        return next((n for n, v in self.literals.items() if v == num), None)

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

        if isinstance(value, Literal):
            return str(value.value)

        if isinstance(value, str):
            return str(self.literals[value])

        raise ValueError()

    def render_string(self, value):
        """ Render the enum value as a string. """
        template = '%s'
        if HydraSettings.full_enum_names:
            template = type(self).__name__ + '.%s'

        if isinstance(value, int):
            return template % self.get_const_name(value)

        if isinstance(value, Literal):
            return template % self.get_const_name(value.value)

        if isinstance(value, str):
            return template % value

        raise ValueError()

    def values_equal(self, a, b):
        def normalize_value(val):
            if isinstance(val, int):
                return val
            if isinstance(val, Literal):
                return val.value
            if isinstance(val, str):
                return self.literals[val]

            raise ValueError()

        return normalize_value(a) == normalize_value(b)

    def __iter__(self):
        return self.literals.items().__iter__()
