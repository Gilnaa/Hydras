"""
Contains various utility methods.

:file: utils.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

import struct
import inspect


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


def is_native_endian_little():
    """ Determine whether the host machine's native endian is little or not. """
    return struct.pack('@H', 0x00FF) == struct.pack('<H', 0x00FF)


def is_native_endian_big():
    """ Determine whether the host machine's native endian is big or not. """
    return struct.pack('@H', 0x00FF) == struct.pack('>H', 0x00FF)


def is_little_endian(endian):
    """ Determine whether the give endian is little or not on the host machine. """
    if endian == '<':
        return True

    return struct.pack(endian + 'H', 0x00FF) == struct.pack('<H', 0x00FF)


def get_as_type(t):
    return t if inspect.isclass(t) else type(t)


def get_as_value(v):
    return v() if inspect.isclass(v) else v


def indexof(callable, it):
    for i, v in enumerate(it):
        if callable(v):
            return i
    raise ValueError


def to_chunks(byte_string, chunk_size):
    """
    Divide the given byte_string into chunks in the given size.

    :param byte_string: The string to divide.
    :param chunk_size:  The size of each of the chunks.
    :return:            A list of byte-strings.
    """
    chunks = []
    for idx in range(0, len(byte_string), chunk_size):
        chunks.append(byte_string[idx:idx + chunk_size])

    return chunks


def mask(length, offset=0):
    """
    Generate a bitmask with the given parameter.

    :param length:  The bit length of the mask.
    :param offset:  The offset of the mask from the LSB bit. [default: 0]
    :return:        An integer representing the bit mask.
    """
    return ((1 << length) - 1) << offset


def string2bytes(s):
    """ Make regular ol' strings work as bytes in python3. """
    if isinstance(s, tuple):
        s = ''.join([chr(i) for i in s])

    if not isinstance(s, bytes):
        return s.encode('ascii')
    return s


def padto(data, size, pad_val=b'\x00', leftpad=False):
    assert type(pad_val) == bytes and len(pad_val) == 1, 'Padding value must be 1 byte'
    if len(data) < size:
        padding = pad_val * (size - len(data))

        if not leftpad:
            data += padding
        else:
            data = padding + data
    return data
