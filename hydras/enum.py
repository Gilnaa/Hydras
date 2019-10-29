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


class Literal:
    def __init__(self, enum, literal_name, value):
        self.enum = enum
        self.literal_name = literal_name
        self.value = value

    def __int__(self):
        return self.value

    def __repr__(self):
        return f'{get_type_name(self.enum)}.{self.literal_name}'


class EnumMetadata(SerializerMetadata):
    _VALID_UNDERLYING_TYPES = (
        u8, u16, u32, u64, i8, i16, i32, i64,
        u8_le, u16_le, u32_le, u64_le, i8_le, i16_le, i32_le, i64_le,
        u8_be, u16_be, u32_be, u64_be, i8_be, i16_be, i32_be, i64_be)

    def __init__(self, *, literals: collections.OrderedDict, underlying: Type['Scalar'] = i32, flags: bool = False):
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
    def __new__(mcs, name, bases, classdict: collections.OrderedDict, underlying_type=u32):
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

            for lit_name in literals_dict:
                del classdict[lit_name]

            classdict.update({
                SerializerMeta.METAATTR: EnumMetadata(literals=literals_dict, underlying=underlying_type)
            })

        return super(EnumMeta, mcs).__new__(mcs, name, bases, classdict)

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()

    @property
    def literals(cls) -> collections.OrderedDict:
        return cls.__hydras_metadata__.literals

    def __getattr__(self, name):
        # Wrap literals in a `Literal` object
        if name in self.literals:
            return Literal(self, name, self.literals[name])
        return super().__getattr__(name)


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
            lit_name, default_value = next(iter(self.literals.items()))
        elif isinstance(default_value, int):
            if not self.is_constant_valid(default_value):
                raise ValueError('Literal constant is not included in the enum: %d' % default_value)
            lit_name = self.get_const_name(default_value)

        default_value = Literal(type(self), lit_name, default_value)
        super(Enum, self).__init__(default_value, *args, **kwargs)

    def format(self, value: Literal, settings=None):
        assert (isinstance(value, Literal) and value.enum == type(self)) or \
               (isinstance(value, int) and self.is_constant_valid(value))

        return self.serializer.format(int(value), self.resolve_settings(settings))

    def parse(self, raw_data, settings=None):
        value = self.serializer.parse(raw_data, self.resolve_settings(settings))

        if not self.is_constant_valid(value):
            raise ValueError('Parsed enum value is unknown: %d' % value)

        return Literal(type(self), self.get_const_name(value) or '<invalid>', value)

    def validate(self, value):
        """ Validate the given enum value. """
        if not self.is_constant_valid(int(value)):
            return False

        return super(Enum, self).validate(int(value))

    def is_constant_valid(self, num):
        """ Determine if the given number is a valid enum literal. """
        return num in self.literals.values()

    def get_const_name(self, num):
        """ Get the name of the constant from a number or a Literal object. """
        return next((n for n, v in self.literals.items() if v == num), None)

    def values_equal(self, a, b):
        return int(a) == int(b)

    def __iter__(self):
        return iter(self.literals.items())
