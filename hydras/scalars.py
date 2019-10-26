"""
:file:  scalars.py.

Contains various primitive type formatters.

:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .base import *
import struct


class Scalar(Serializer):
    """ Provides a handy base class for primitive-value formatters. """

    def __init__(self, default_value=0, *args, **kwargs):
        """
        Initialize the scalar object.

        :param format_string:   The format string of the primitive, according to `struct.pack`
        :param default_value:   The default value of this formatter.
        :param endian:          The endian of this formatter.
        """
        super(Scalar, self).__init__(default_value, *args, **kwargs)
        self.validate_assignment(default_value)
        self._length = len(self.format(0))

    def validate_assignment(self, value):
        if self._range is not None:
            if value not in self._range:
                return False

        return type(value) is self._pytype

    def format(self, value, settings=None):
        settings = self.resolve_settings(settings)

        if self._endianness == Endianness.TARGET:
            endian = settings['target_endian']
        else:
            endian = self._endianness

        return struct.pack(endian.value + self._fmt, value)

    def parse(self, raw_data, settings=None):
        return struct.unpack(self._fmt, raw_data)[0]

    @classmethod
    def __len__(cls):
        return cls()._length

    # These declarations exists just to satisfy IDEs and is overriden by the real format string
    _length = 0
    _fmt = None
    _pytype = None
    _range = None
    _endianness = None


def _create_integer_type(name: str, format_string: str, endianness: Endianness, min: int, max: int) -> type:
    return type(name, (Scalar, ), {
        '_fmt': format_string,
        '_range': range(min, max + 1),
        '_pytype': int,
        '_endianness': endianness
    })


def _create_float_type(name: str, format_string: str, endianness: Endianness) -> type:
    return type(name, (Scalar, ), {
        '_fmt': format_string,
        '_pytype': float,
        '_endianness': endianness
    })


# Target endian scalars
u8 = _create_integer_type('u8', 'B', Endianness.TARGET, 0, 0xFF)
i8 = _create_integer_type('i8', 'b', Endianness.TARGET, -128, 127)
u16 = _create_integer_type('u16', 'H', Endianness.TARGET, 0, 0xFFFF)
i16 = _create_integer_type('i16', 'h', Endianness.TARGET, -32768, 32767)
u32 = _create_integer_type('u32', 'I', Endianness.TARGET, 0, 0xFFFFFFFF)
i32 = _create_integer_type('i32', 'i', Endianness.TARGET, -2147483648, 2147483647)
u64 = _create_integer_type('u64', 'Q', Endianness.TARGET, 0, 0xFFFFFFFFFFFFFFFF)
i64 = _create_integer_type('i64', 'q', Endianness.TARGET, -9223372036854775808, 9223372036854775807)
f32 = _create_float_type('f32', 'f',  Endianness.TARGET)
f64 = _create_float_type('f64', 'd',  Endianness.TARGET)

# Big-endian scalars
u8_be = _create_integer_type('u8_be', 'B', Endianness.BIG, 0, 0xFF)
i8_be = _create_integer_type('i8_be', 'b', Endianness.BIG, -128, 127)
u16_be = _create_integer_type('u16_be', 'H', Endianness.BIG, 0, 0xFFFF)
i16_be = _create_integer_type('i16_be', 'h', Endianness.BIG, -32768, 32767)
u32_be = _create_integer_type('u32_be', 'I', Endianness.BIG, 0, 0xFFFFFFFF)
i32_be = _create_integer_type('i32_be', 'i', Endianness.BIG, -2147483648, 2147483647)
u64_be = _create_integer_type('u64_be', 'Q', Endianness.BIG, 0, 0xFFFFFFFFFFFFFFFF)
i64_be = _create_integer_type('i64_be', 'q', Endianness.BIG, -9223372036854775808, 9223372036854775807)
f32_be = _create_float_type('f32_be', 'f',  Endianness.BIG)
f64_be = _create_float_type('f64_be', 'd',  Endianness.BIG)

# Little-endian scalars
u8_le = _create_integer_type('u8_le', 'B', Endianness.LITTLE, 0, 0xFF)
i8_le = _create_integer_type('i8_le', 'b', Endianness.LITTLE, -128, 127)
u16_le = _create_integer_type('u16_le', 'H', Endianness.LITTLE, 0, 0xFFFF)
i16_le = _create_integer_type('i16_le', 'h', Endianness.LITTLE, -32768, 32767)
u32_le = _create_integer_type('u32_le', 'I', Endianness.LITTLE, 0, 0xFFFFFFFF)
i32_le = _create_integer_type('i32_le', 'i', Endianness.LITTLE, -2147483648, 2147483647)
u64_le = _create_integer_type('u64_le', 'Q', Endianness.LITTLE, 0, 0xFFFFFFFFFFFFFFFF)
i64_le = _create_integer_type('i64_le', 'q', Endianness.LITTLE, -9223372036854775808, 9223372036854775807)
f32_le = _create_float_type('f32_le', 'f',  Endianness.LITTLE)
f64_le = _create_float_type('f64_le', 'd',  Endianness.LITTLE)
