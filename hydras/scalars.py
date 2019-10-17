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
        self.validate_assignment(default_value)

        super(Scalar, self).__init__(default_value, *args, **kwargs)

    def validate_assignment(self, value):
        # Try to pack the value. An exception will be raised if the the value is too big.
        try:
            struct.pack(self._fmt, value)
        except struct.error:
            raise ValueError("Value out of type bounds")

    def format(self, value, settings=None):
        return struct.pack(self._fmt, value)

    def parse(self, raw_data, settings=None):
        return struct.unpack(self._fmt, string2bytes(raw_data))[0]

    def __len__(self):
        return len(self.format(0))

    # This declaration exists just to satisfy IDEs and is overriden by the real format string
    _fmt = None


# Native endian scalars
u8 = type('uint8_t', (Scalar,), {'_fmt': '=B'})
i8 = type('int8_t', (Scalar,), {'_fmt': '=b'})
u16 = type('uint16_t', (Scalar,), {'_fmt': '=H'})
i16 = type('int16_t', (Scalar,), {'_fmt': '=h'})
u32 = type('uint32_t', (Scalar,), {'_fmt': '=I'})
i32 = type('int32_t', (Scalar,), {'_fmt': '=i'})
u64 = type('uint64_t', (Scalar,), {'_fmt': '=Q'})
i64 = type('int64_t', (Scalar,), {'_fmt': '=q'})
f32 = type('float32_t', (Scalar,), {'_fmt': '=f'})
f64 = type('float64_t', (Scalar,), {'_fmt': '=d'})

# Big-endian scalars
u8_be = type('be_uint8_t', (Scalar,), {'_fmt': '>B'})
i8_be = type('be_int8_t', (Scalar,), {'_fmt': '>b'})
u16_be = type('be_uint16_t', (Scalar,), {'_fmt': '>H'})
i16_be = type('be_int16_t', (Scalar,), {'_fmt': '>h'})
u32_be = type('be_uint32_t', (Scalar,), {'_fmt': '>I'})
i32_be = type('be_int32_t', (Scalar,), {'_fmt': '>i'})
u64_be = type('be_uint64_t', (Scalar,), {'_fmt': '>Q'})
i64_be = type('be_int64_t', (Scalar,), {'_fmt': '>q'})
f32_be = type('be_float32_t', (Scalar,), {'_fmt': '>f'})
f64_be = type('be_float64_t', (Scalar,), {'_fmt': '>d'})

# Little-endian scalars
u8_le = type('le_uint8_t', (Scalar,), {'_fmt': '<B'})
i8_le = type('le_int8_t', (Scalar,), {'_fmt': '<b'})
u16_le = type('le_uint16_t', (Scalar,), {'_fmt': '<H'})
i16_le = type('le_int16_t', (Scalar,), {'_fmt': '<h'})
u32_le = type('le_uint32_t', (Scalar,), {'_fmt': '<I'})
i32_le = type('le_int32_t', (Scalar,), {'_fmt': '<i'})
u64_le = type('le_uint64_t', (Scalar,), {'_fmt': '<Q'})
i64_le = type('le_int64_t', (Scalar,), {'_fmt': '<q'})
f32_le = type('le_float32_t', (Scalar,), {'_fmt': '<f'})
f64_le = type('le_float64_t', (Scalar,), {'_fmt': '<d'})
