"""
:file:  scalars.py.

Contains various primitive type formatters.

:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

from .base import *
import struct

class Scalar(TypeFormatter):

    """ Provides a handy base class for primitive-value formatters. """

    def __init__(self, format_string, default_value=0, endian=None, *args, **kwargs):
        """
        Initialize the scalar object.

        :param format_string:   The format string of the primitive, according to `struct.pack`
        :param default_value:   The default value of this formatter.
        :param endian:          The endian of this formatter.
        """
        settings = {}
        self.format_string = format_string
        if endian is not None:
            settings['endian'] = endian

        self.validate_assignment(default_value)

        super(Scalar, self).__init__(default_value, settings=settings, *args, **kwargs)

    def validate_assignment(self, value):
        # Try to pack the value. An exception will be raised if the the value is too big.

        if isinstance(value, str) or isinstance(value, bytes):
            return

        try:
            struct.pack(self.format_string, value)
        except struct.error:
            raise ValueError("Value out of type bounds")


    def format(self, value, settings=None):
        if isinstance(value, (str, bytes)):
            if len(value) != len(self):
                raise ValueError('Got formatted data with invalid length')
            return value

        endian = self.resolve_settings(settings)['endian']
        return struct.pack(endian + self.format_string, value)

    def parse(self, raw_data, settings=None):
        endian = self.resolve_settings(settings)['endian']
        return struct.unpack(endian + self.format_string, string2bytes(raw_data))[0]

    def __len__(self):
        return len(self.format(0))


class UInt8(Scalar):
    """ An 8 bits long unsigned integer. """

    def __init__(self, *args, **kwargs):
        super(UInt8, self).__init__('B', *args, **kwargs)


class Int8(Scalar):
    """ An 8 bits long signed integer. """

    def __init__(self, *args, **kwargs):
        super(Int8, self).__init__('b', *args, **kwargs)


class UInt16(Scalar):
    """ A 16 bits long unsigned integer. """

    def __init__(self, *args, **kwargs):
        super(UInt16, self).__init__('H', *args, **kwargs)


class Int16(Scalar):
    """ A 16 bits long signed integer. """

    def __init__(self, *args, **kwargs):
        super(Int16, self).__init__('h', *args, **kwargs)


class UInt32(Scalar):
    """ A 32 bits long unsigned integer. """

    def __init__(self, *args, **kwargs):
        super(UInt32, self).__init__('I', *args, **kwargs)


class Int32(Scalar):
    """ A 32 bits long signed integer. """

    def __init__(self, *args, **kwargs):
        super(Int32, self).__init__('i', *args, **kwargs)


class UInt64(Scalar):
    """ A 64 bits long unsigned integer. """

    def __init__(self, *args, **kwargs):
        super(UInt64, self).__init__('Q', *args, **kwargs)


class Int64(Scalar):
    """ A 64 bits long signed integer. """

    def __init__(self, *args, **kwargs):
        super(Int64, self).__init__('q', *args, **kwargs)


class Float(Scalar):
    """
    A 32 bits long floating point number.

    The value will be serialized using the 'IEEE 754 binary32' format
    """

    def __init__(self, *args, **kwargs):
        super(Float, self).__init__('f', *args, **kwargs)


class Double(Scalar):
    """
    A 64 bits long floating point number.

    The value will be serialized using the 'IEEE 754 binary64' format
    """

    def __init__(self, *args, **kwargs):
        super(Double, self).__init__('d', *args, **kwargs)
