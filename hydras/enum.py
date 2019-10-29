"""
:file: enum.py

Contains a more natural enum implementation.

:date: 10/06/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from enum import auto
from .base import *
from .scalars import *
import collections


__all__ = ('Enum', 'auto')


class auto:
    pass


class EnumMetadata(SerializerMetadata):
    _VALID_UNDERLYING_TYPES = (
        u8, u16, u32, u64, i8, i16, i32, i64,
        u8_le, u16_le, u32_le, u64_le, i8_le, i16_le, i32_le, i64_le,
        u8_be, u16_be, u32_be, u64_be, i8_be, i16_be, i32_be, i64_be)

    def __init__(self, *, literals: collections.OrderedDict, underlying: Scalar = i32, flags: bool = False):
        super().__init__(underlying.byte_size)

        if underlying not in self._VALID_UNDERLYING_TYPES:
            raise TypeError(f'Invalid underlying type for Enum: {get_type_name(underlying)}')
        serializer = get_as_value(underlying)
        try:
            for k, v in literals.items():
                serializer.validate(v)
        except ValueError as e:
            raise ValueError(f'Invalid value for literal {v}: {e.message}')

        self.flags = flags
        self.serializer = serializer
        self.literals = literals


class EnumMeta(SerializerMeta):
    def __new__(mcs, name, bases, classdict, underlying_type=u32):
        if not hasattr(mcs, SerializerMeta.METAATTR):
            literals = (
                (k, v) for k, v in classdict.items()
                if isinstance(v, (int, auto)) and not k.startswith('_')
            )
            literals_dict = collections.OrderedDict()

            next_expected_value = 0
            for lit_name, literal in literals:
                # Replace `auto` instances with the correct values.
                if isinstance(literal, auto):
                    # Update the literal object before taking its value
                    literal = next_expected_value
                    classdict[lit_name] = literal

                next_expected_value = literal + 1
                literals_dict[lit_name] = literal

            classdict.update({
                SerializerMeta.METAATTR: EnumMetadata(literals=literals_dict, underlying=underlying_type)
            })

        return super(EnumMeta, mcs).__new__(mcs, name, bases, classdict)

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()

    @property
    def literals(cls) -> collections.OrderedDict:
        return cls.__hydras_metadata__.literals


class Enum(Serializer, metaclass=EnumMeta):
    @property
    def literals(self) -> collections.OrderedDict:
        return type(self).literals

    @property
    def serializer(self) -> Scalar:
        return self.__hydras_metadata__.serializer

    """ An enum formatter that can be shared between structs. """
    def __init__(self, default_value=None, *args, **kwargs):

        # Validate the default_value
        if default_value is None:
            default_value = next(iter(self.literals.values()))
        elif isinstance(default_value, int):
            if not self.is_constant_valid(default_value):
                raise ValueError('Literal constant is not included in the enum: %d' % default_value)

        super(Enum, self).__init__(default_value, *args, **kwargs)

    def format(self, value, settings=None):
        return self.serializer.format(value, self.resolve_settings(settings))

    def parse(self, raw_data, settings=None):
        value = self.serializer.parse(raw_data, self.resolve_settings(settings))

        if settings['strong_enum_literals'] and not self.is_constant_valid(value):
            raise ValueError('Parsed enum value is unknown: %d' % value)

        return value

    def validate(self, value):
        """ Validate the given enum value. """
        if HydraSettings.strong_enum_literals and \
                not self.is_constant_valid(value):
            return False

        return super(Enum, self).validate(value)

    def is_constant_valid(self, num):
        """ Determine if the given number is a valid enum literal. """
        return num in self.literals.values()

    def get_const_name(self, num):
        """ Get the name of the constant from a number or a Literal object. """
        return next((n for n, v in self.literals.items() if v == num), None)

    def render(self, value, name):
        """ Render the enum value. """
        if HydraSettings.render_enums_as_integers:
            value = str(value)
        else:
            value = self.render_string(value)

        return '%s = %s' % (name, value)

    def render_string(self, value):
        """ Render the enum value as a string. """
        template = '%s'
        if HydraSettings.full_enum_names:
            template = get_type_name(self) + '.%s'

        if isinstance(value, int):
            return template % self.get_const_name(value)

        if isinstance(value, str):
            return template % value

        raise ValueError()

    def values_equal(self, a, b):
        return a == b

    def __iter__(self):
        return self.literals.items().__iter__()
