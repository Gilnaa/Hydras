"""
:file: scalars.py

Contains various primitive type formatters.

:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
"""

from .base import *
import struct


class Scalar(TypeFormatter):
    def __init__(self, format_string, default_value=0, endian=None, *args, **kwargs):
        settings = {}
        self.format_string = format_string
        if endian is not None:
            settings['endian'] = endian

        super(Scalar, self).__init__(default_value, settings=settings, *args, **kwargs)

    def format(self, value, settings=None):
        endian = self.resolve_settings(settings)['endian']
        return struct.pack(endian + self.format_string, value)

    def parse(self, raw_data, settings=None):
        endian = self.resolve_settings(settings)['endian']
        return struct.unpack(endian + self.format_string, string2bytes(raw_data))[0]

    def __len__(self):
        return len(self.format(0))


class UInt8(Scalar):
    def __init__(self, *args, **kwargs):
        super(UInt8, self).__init__('B', *args, **kwargs)


class Int8(Scalar):
    def __init__(self, *args, **kwargs):
        super(Int8, self).__init__('b', *args, **kwargs)


class UInt16(Scalar):
    def __init__(self, *args, **kwargs):
        super(UInt16, self).__init__('H', *args, **kwargs)


class Int16(Scalar):
    def __init__(self, *args, **kwargs):
        super(Int16, self).__init__('h', *args, **kwargs)


class UInt32(Scalar):
    def __init__(self, *args, **kwargs):
        super(UInt32, self).__init__('I', *args, **kwargs)


class Int32(Scalar):
    def __init__(self, *args, **kwargs):
        super(Int32, self).__init__('i', *args, **kwargs)


class UInt64(Scalar):
    def __init__(self, *args, **kwargs):
        super(UInt64, self).__init__('Q', *args, **kwargs)


class Int64(Scalar):
    def __init__(self, *args, **kwargs):
        super(Int64, self).__init__('q', *args, **kwargs)


class Float(Scalar):
    def __init__(self, *args, **kwargs):
        super(Float, self).__init__('f', *args, **kwargs)


class Double(Scalar):
    def __init__(self, *args, **kwargs):
        super(Double, self).__init__('d', *args, **kwargs)