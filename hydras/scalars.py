"""
:file:  scalars.py.

Contains various primitive type formatters.

:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .base import *
import struct


class ScalarMetadata(SerializerMetadata):
    __slots__ = ('endianness', 'fmt', 'validator', 'py_types')
    _FORMATTERS_INFO = {
        'B': (1, (int, ), RangeValidator(0, 255)),
        'b': (1, (int, ), RangeValidator(-128, 127)),
        'H': (2, (int, ), RangeValidator(0, 65535)),
        'h': (2, (int, ), RangeValidator(-32768, 32767)),
        'I': (4, (int, ), RangeValidator(0, 4294967295)),
        'i': (4, (int, ), RangeValidator(-2147483648, 2147483647)),
        'Q': (8, (int, ), RangeValidator(0, 18446744073709551615)),
        'q': (8, (int, ), RangeValidator(-9223372036854775808, 9223372036854775807)),
        'f': (4, (int, float), TrueValidator()),
        'd': (8, (int, float), TrueValidator()),
    }

    def __init__(self, *, fmt: str, endianness: Endianness):
        size, self.py_types, self.validator = ScalarMetadata._FORMATTERS_INFO[fmt]
        self.endianness = endianness
        self.fmt = fmt
        super(ScalarMetadata, self).__init__(size)


class ScalarMeta(SerializerMeta):
    def __new__(mcs, name, bases, classdict, fmt: str = None, endianness: Endianness = Endianness.TARGET):
        if hasattr(sys.modules[__name__], 'Scalar'):
            classdict[SerializerMeta.METAATTR] = ScalarMetadata(fmt=fmt, endianness=endianness)
        return super(ScalarMeta, mcs).__new__(mcs, name, bases, classdict)


class Scalar(Serializer, metaclass=ScalarMeta):
    """ Provides a handy base class for primitive-value formatters. """

    @property
    def endianness(self) -> Endianness:
        return self.__hydras_metadata__.endianness

    @property
    def fmt(self) -> str:
        return self.__hydras_metadata__.fmt

    @property
    def py_types(self):
        return self.__hydras_metadata__.py_types

    @property
    def primitive_validator(self):
        return self.__hydras_metadata__.validator

    def __init__(self, default_value=0, *args, **kwargs):
        """
        Initialize the scalar object.

        :param format_string:   The format string of the primitive, according to `struct.pack`
        :param default_value:   The default value of this formatter.
        :param endian:          The endian of this formatter.
        """
        super(Scalar, self).__init__(default_value, *args, **kwargs)
        self._length = len(self.serialize(0))

    def validate(self, value):
        if not isinstance(value, self.py_types):
            raise TypeError(f'Expected value of type {self.py_types}, but got {type(value)}')
        elif not self.primitive_validator(value):
            raise ValueError('Value outside of type bounds')

        super(Scalar, self).validate(value)

    def serialize_into(self, storage: memoryview, offset: int, value, settings: HydraSettings = None) -> int:
        struct.pack_into(self.get_format_string(settings), storage, offset, value)
        return offset + self.byte_size

    def deserialize(self, raw_data, settings: HydraSettings = None):
        settings = HydraSettings.resolve(settings)

        if self.endianness == Endianness.TARGET:
            endian = settings.target_endian
        else:
            endian = self.endianness

        return struct.unpack(endian.value + self.fmt, raw_data)[0]

    def get_format_string(self, settings: HydraSettings = None, count: int = 1):
        if self.endianness == Endianness.TARGET:
            settings = HydraSettings.resolve(settings)
            endian = settings.target_endian
        else:
            endian = self.endianness

        if count > 1:
            return endian.value + str(count) + self.fmt
        return endian.value + self.fmt


class ByteType(Scalar, fmt='B'):
    def get_initial_values(self, count):
        initial_value = self.get_initial_value()
        if initial_value == 0:
            return bytearray(count)
        return bytearray((initial_value, )) * count

# Target endian scalars
class u8(ByteType, fmt='B', endianness=Endianness.TARGET): pass
class i8(Scalar, fmt='b', endianness=Endianness.TARGET): pass
class u16(Scalar, fmt='H', endianness=Endianness.TARGET): pass
class i16(Scalar, fmt='h', endianness=Endianness.TARGET): pass
class u32(Scalar, fmt='I', endianness=Endianness.TARGET): pass
class i32(Scalar, fmt='i', endianness=Endianness.TARGET): pass
class u64(Scalar, fmt='Q', endianness=Endianness.TARGET): pass
class i64(Scalar, fmt='q', endianness=Endianness.TARGET): pass
class f32(Scalar, fmt='f', endianness=Endianness.TARGET): pass
class f64(Scalar, fmt='d', endianness=Endianness.TARGET): pass


# Big-endian scalars
class u8_be(ByteType, fmt='B', endianness=Endianness.BIG): pass
class i8_be(Scalar, fmt='b', endianness=Endianness.BIG): pass
class u16_be(Scalar, fmt='H', endianness=Endianness.BIG): pass
class i16_be(Scalar, fmt='h', endianness=Endianness.BIG): pass
class u32_be(Scalar, fmt='I', endianness=Endianness.BIG): pass
class i32_be(Scalar, fmt='i', endianness=Endianness.BIG): pass
class u64_be(Scalar, fmt='Q', endianness=Endianness.BIG): pass
class i64_be(Scalar, fmt='q', endianness=Endianness.BIG): pass
class f32_be(Scalar, fmt='f', endianness=Endianness.BIG): pass
class f64_be(Scalar, fmt='d', endianness=Endianness.BIG): pass


# Little-endian scalars
class u8_le(ByteType, fmt='B', endianness=Endianness.LITTLE): pass
class i8_le(Scalar, fmt='b', endianness=Endianness.LITTLE): pass
class u16_le(Scalar, fmt='H', endianness=Endianness.LITTLE): pass
class i16_le(Scalar, fmt='h', endianness=Endianness.LITTLE): pass
class u32_le(Scalar, fmt='I', endianness=Endianness.LITTLE): pass
class i32_le(Scalar, fmt='i', endianness=Endianness.LITTLE): pass
class u64_le(Scalar, fmt='Q', endianness=Endianness.LITTLE): pass
class i64_le(Scalar, fmt='q', endianness=Endianness.LITTLE): pass
class f32_le(Scalar, fmt='f', endianness=  Endianness.LITTLE): pass
class f64_le(Scalar, fmt='d', endianness=  Endianness.LITTLE): pass
