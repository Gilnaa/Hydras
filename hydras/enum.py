"""
:file: enum.py

Contains a more natural enum implementation.

:date: 10/06/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

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
    def __init__(self, enum_type, literal_name, value):
        self.enum = enum_type
        self.literal_name = literal_name
        self.value = value

    def __int__(self):
        return self.value

    def __repr__(self):
        return f'{get_type_name(self.enum)}.{self.literal_name}'

    def __eq__(self, other):
        return int(self) == int(other)

    def __hash__(self):
        return hash((self.enum, self.literal_name, self.value))


class EnumMetadata(SerializerMetadata):
    __slots__ = ('flags', 'serializer', 'literals', 'reverse_map')
    _VALID_UNDERLYING_TYPES = (
        u8, u16, u32, u64, i8, i16, i32, i64,
        u8_le, u16_le, u32_le, u64_le, i8_le, i16_le, i32_le, i64_le,
        u8_be, u16_be, u32_be, u64_be, i8_be, i16_be, i32_be, i64_be)

    def __init__(self, *,
                 literals: collections.OrderedDict,
                 reverse_map: Dict,
                 underlying: Type['Scalar'],
                 flags: bool = False):
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
        self.reverse_map = reverse_map


class EnumMeta(SerializerMeta):
    _hydras_metadata: EnumMetadata

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

            reverse_map = {
                value: Literal(mcs, name, value)
                for name, value in literals_dict.items()
            }
            metadata = EnumMetadata(literals=literals_dict, reverse_map=reverse_map, underlying=underlying_type)

            classdict.update({SerializerMeta.METAATTR: metadata})

            # Patch the actual enum type once we get it from super.
            gen_mcs = super(EnumMeta, mcs).__new__(mcs, name, bases, classdict)
            for lit in reverse_map.values():
                lit.enum = gen_mcs
            return gen_mcs

        return super(EnumMeta, mcs).__new__(mcs, name, bases, classdict)

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()

    def __contains__(cls, item):
        if isinstance(item, Literal):
            return item.enum == cls and cls.literals.get(item.literal_name) == item.value
        elif isinstance(item, int):
            return item in cls.literals.values()
        return False

    @property
    def literals(cls) -> collections.OrderedDict:
        return cls._hydras_metadata.literals

    def __getattr__(cls, name):
        # Wrap literals in a `Literal` object
        if name in cls._hydras_metadata.literals:
            return Literal(cls, name, cls._hydras_metadata.literals[name])
        return super().__getattr__(name)

    def __repr__(cls):
        return get_type_name(cls)


class Enum(Serializer, metaclass=EnumMeta):
    __slots__ = ()
    _hydras_metadata: EnumMetadata

    """ An enum formatter that can be shared between structs. """
    def __init__(self, default_value=None, *args, **kwargs):
        if type(self) is Enum:
            raise RuntimeError('Cannot instantiate `Enum` directly. Must subclass it.')
        elif len(self._hydras_metadata.literals) == 0:
            raise RuntimeError('Cannot instantiate an empty Enum')

        assert default_value is None or isinstance(default_value, (int, Literal))

        # Validate the default_value
        if default_value is None:
            default_value = self.get_literal_by_name(next(iter(self._hydras_metadata.literals)))
        elif isinstance(default_value, int):
            if not self.is_constant_valid(default_value):
                raise ValueError('Literal constant is not included in the enum: %d' % default_value)
            default_value = self.get_literal_by_value(default_value)
        elif isinstance(default_value, Literal):
            if default_value.enum is not type(self) or \
                    not self.is_constant_valid(default_value.value) or \
                    default_value.literal_name not in self._hydras_metadata.literals:
                raise ValueError('Invalid or corrupted literal')

        super(Enum, self).__init__(default_value, *args, **kwargs)

    def serialize_into(self, storage: memoryview, offset: int, value: Literal, settings: HydraSettings = None) -> int:
        assert (isinstance(value, Literal) and value.enum == type(self)) or \
               (isinstance(value, int) and self.is_constant_valid(value))

        return self._hydras_metadata.serializer.serialize_into(storage, offset, int(value), settings)

    def deserialize(self, raw_data, settings: HydraSettings = None):
        value = self._hydras_metadata.serializer.deserialize(raw_data, settings)

        lit = self._hydras_metadata.reverse_map[value]
        if lit is None:
            raise ValueError('Parsed enum value is unknown: %d' % value)

        return lit

    def validate(self, value):
        """ Validate the given enum value. """
        if not self.is_constant_valid(int(value)):
            return ValueError('Enum literal value is not part of the enum')

        super(Enum, self).validate(int(value))

    def is_constant_valid(self, num):
        """ Determine if the given number is a valid enum literal. """
        return num in self._hydras_metadata.reverse_map

    @classmethod
    def get_literal_name(cls, num):
        """ Get the name of the constant from a number or a Literal object. """
        lit = cls._hydras_metadata.reverse_map.get(num)
        if lit is not None:
            return lit.literal_name
        return None

    @classmethod
    def get_literal_by_name(cls, name):
        return Literal(cls, name, cls._hydras_metadata.literals[name])

    @classmethod
    def get_literal_by_value(cls, value):
        return cls._hydras_metadata.reverse_map.get(value)

    def values_equal(self, a, b):
        return int(a) == int(b)

    def __repr__(self):
        value = self.get_initial_value()
        if value.literal_name == next(iter(self._hydras_metadata.literals.keys())):
            value = ''
        return f'{get_type_name(self)}({value})'
