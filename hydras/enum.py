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
    # This is implemented solely to satisfy PyCharm's type-checker.
    # In reality this function will never be called
    def __int__(self):
        raise RuntimeError('This is not supposed to happen')


class Literal:
    def __init__(self, enum, literal_name, value):
        self.enum = enum
        self.literal_name = literal_name
        self.value = value

    def __int__(self):
        return self.value

    def __repr__(self):
        return f'{get_type_name(self.enum)}.{self.literal_name}'

    def __eq__(self, other):
        return int(self) == int(other)


class EnumMetadata(SerializerMetadata):
    __slots__ = ('flags', 'serializer', 'literals')
    _VALID_UNDERLYING_TYPES = (
        u8, u16, u32, u64, i8, i16, i32, i64,
        u8_le, u16_le, u32_le, u64_le, i8_le, i16_le, i32_le, i64_le,
        u8_be, u16_be, u32_be, u64_be, i8_be, i16_be, i32_be, i64_be)

    def __init__(self, *, literals: collections.OrderedDict, underlying: Type['Scalar'], flags: bool = False):
        super().__init__(underlying.byte_size)

        if underlying not in self._VALID_UNDERLYING_TYPES:
            raise TypeError(f'Invalid underlying type for Enum: {get_type_name(underlying)}')
        serializer = get_as_value(underlying)
        try:
            for k, v in literals.items():
                serializer.validate(v)
        except ValueError as e:
            raise ValueError(f'Invalid value for literal {v}: {e}')

        self.flags = flags
        self.serializer = serializer
        self.literals = literals


class EnumMeta(SerializerMeta):
    def __new__(mcs, name, bases, classdict: collections.OrderedDict, underlying_type=i32):
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
        if type(self) is Enum:
            raise RuntimeError('Cannot instantiate `Enum` directly. Must subclass it.')
        elif len(self.literals) == 0:
            raise RuntimeError('Cannot instantiate an empty Enum')

        assert default_value is None or isinstance(default_value, (int, Literal))

        # Validate the default_value
        if default_value is None:
            default_value = self.get_literal_by_name(next(iter(self.literals)))
        elif isinstance(default_value, int):
            if not self.is_constant_valid(default_value):
                raise ValueError('Literal constant is not included in the enum: %d' % default_value)
            default_value = self.get_literal_by_value(default_value)
        elif isinstance(default_value, Literal):
            if default_value.enum is not type(self) or \
                    not self.is_constant_valid(default_value.value) or \
                    default_value.literal_name not in self.literals:
                raise ValueError('Invalid or corrupted literal')

        super(Enum, self).__init__(default_value, *args, **kwargs)

    def serialize_into(self, storage: memoryview, offset: int, value: Literal, settings: HydraSettings = None) -> int:
        assert (isinstance(value, Literal) and value.enum == type(self)) or \
               (isinstance(value, int) and self.is_constant_valid(value))

        return self.serializer.serialize_into(storage, offset, int(value), settings)

    def deserialize(self, raw_data, settings: HydraSettings = None):
        value = self.serializer.deserialize(raw_data, settings)

        if not self.is_constant_valid(value):
            raise ValueError('Parsed enum value is unknown: %d' % value)

        return Literal(type(self), self.get_literal_name(value) or '<invalid>', value)

    def validate(self, value):
        """ Validate the given enum value. """
        if not self.is_constant_valid(int(value)):
            return ValueError('Enum literal value is not part of the enum')

        super(Enum, self).validate(int(value))

    def is_constant_valid(self, num):
        """ Determine if the given number is a valid enum literal. """
        return num in self.literals.values()

    def get_literal_name(self, num):
        """ Get the name of the constant from a number or a Literal object. """
        return next((n for n, v in self.literals.items() if v == num), None)

    def get_literal_by_name(self, name):
        return Literal(type(self), name, self.literals[name])

    def get_literal_by_value(self, value):
        return Literal(type(self), self.get_literal_name(value), value)

    def values_equal(self, a, b):
        return int(a) == int(b)
