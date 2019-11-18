"""
Contains various utility methods.

:file: utils.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from typing import Any, Type, Union
import inspect
import enum
import sys


class Endianness(enum.Enum):
    BIG = '>'
    LITTLE = '<'
    HOST = '='
    TARGET = None

    def is_equivalent_to_little_endian(self):
        return self == Endianness.LITTLE or (self == Endianness.HOST and sys.byteorder == 'little')

    def is_equivalent_to_big_endian(self):
        return self == Endianness.LITTLE or (self == Endianness.HOST and sys.byteorder == 'little')


def create_array(size: Union[int, slice], underlying_type):
    # Importing locally in order to avoid weird import-cycle issues
    from .array import Array
    return Array[size, underlying_type]


def fit_bytes_to_size(byte_string, length):
    """
    Ensure the given byte_string is in the correct length

    A long byte_string will be truncated, while a short one will be padded.

    :param byte_string: The string to fit.
    :param length:      The required string size.
    """
    if length is None:
        return byte_string

    if len(byte_string) < length:
        return padto(byte_string, length)

    return byte_string[:length]


def get_as_type(t):
    return t if inspect.isclass(t) else type(t)


def get_as_value(v):
    return v() if inspect.isclass(v) else v


def mask(length, offset=0):
    """
    Generate a bitmask with the given parameter.

    :param length:  The bit length of the mask.
    :param offset:  The offset of the mask from the LSB bit. [default: 0]
    :return:        An integer representing the bit mask.
    """
    return ((1 << length) - 1) << offset


def get_type_name(t: Union[Type, Any]) -> str:
    return get_as_type(t).__name__


def padto(data, size, pad_val=b'\x00', leftpad=False):
    assert type(pad_val) == bytes and len(pad_val) == 1, 'Padding value must be 1 byte'
    if len(data) < size:
        padding = pad_val * (size - len(data))

        if not leftpad:
            data += padding
        else:
            data = padding + data
    return data
