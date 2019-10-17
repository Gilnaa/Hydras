#!/usr/bin/env python
"""
:file: 02_integral_formatters.py

A showcase of the available "primitive" types.

:date: 11/06/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from hydras import *
import binascii


class Showcase(Struct):
    """ A list of the available 'primitive' numeric types. """
    unsigned_byte = u8()
    unsigned_word = u16()
    unsigned_dword = u32()
    unsigned_qword = u64()

    signed_byte = i8()
    signed_word = i16()
    signed_dword = i32()
    signed_qword = i64()

    single_float = f32()
    double_float = f64()


class StdintAliases(Struct):
    """ A bunch of aliases that looks like the typedefs from stdint.h"""
    unsigned_byte = u8()
    unsigned_word = u16()
    unsigned_dword = u32()
    unsigned_qword = u64()

    signed_byte = i8()
    signed_word = i16()
    signed_dword = i32()
    signed_qword = i64()


class PrimitiveFeatures(Struct):
    has_a_default_value = u8(0x39)
    big_endian = u16_be
    a_big_default = u32_be(0xDEADBEEF)


if __name__ == '__main__':
    print(binascii.hexlify(PrimitiveFeatures().serialize()))
