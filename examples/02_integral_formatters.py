#!/usr/bin/env python
"""
:file: 02_integral_formatters.py

A showcase of the available "primitive" types.

:date: 11/06/2016
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

from hydra import *
import binascii


class Showcase(Struct):
    """ A list of the available 'primitive' numeric types. """
    unsigned_byte = UInt8()
    unsigned_word = UInt16()
    unsigned_dword = UInt32()
    unsigned_qword = UInt64()

    signed_byte = Int8()
    signed_word = Int16()
    signed_dword = Int32()
    signed_qword = Int64()

    single_float = Float()
    double_float = Double()


class StdintAliases(Struct):
    """ A bunch of aliases that looks like the typedefs from stdint.h"""
    unsigned_byte = uint8_t()
    unsigned_word = uint16_t()
    unsigned_dword = uint32_t()
    unsigned_qword = uint64_t()

    signed_byte = int8_t()
    signed_word = int16_t()
    signed_dword = int32_t()
    signed_qword = int64_t()


class PrimitiveFeatures(Struct):
    has_a_default_value = uint8_t(0x39)
    big_endian = uint16_t(endian=BigEndian)
    a_big_default = uint32_t(0xDEADBEEF, endian=BigEndian)


if __name__ == '__main__':
    print binascii.hexlify(PrimitiveFeatures().serialize())