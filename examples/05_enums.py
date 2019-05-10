#!/usr/bin/env python
"""
:file: 03_arrays.py

A review of the Array type.

:date: 11/06/2016
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

from hydras import *
import binascii

################
# Inline Enums #
################


class SomeHeader(Struct):
    #             [default]  [The list of values]
    opcode = Enum('Invalid', {'Invalid': 0,
                              'Data': 1,
                              'Ack': 2,
                              'Nack': 3})

    sized_enum = Enum('Z', {'A': 0,
                            'B': 1,
                            'C': 2,
                            'D': 3,
                            'Z': 0xFF}, format_type=uint8_t)

if __name__ == '__main__':
    print '>> Inline Enums'
    header = SomeHeader()

    print binascii.hexlify(header.serialize())
    # => 00000000ff

    header.opcode = 'Ack'
    print binascii.hexlify(header.serialize())
    # => 02000000ff

    header.opcode = SomeHeader.opcode.Nack
    print binascii.hexlify(header.serialize())
    # => 03000000ff


################
# Enum Classes #
################


class Opcodes(EnumClass):
    Invalid = Literal()
    Data = Literal()
    Ack = Literal()
    Nack = Literal()


class AnotherHeader(Struct):
    opcode = Opcodes()
    different_default = Opcodes(Opcodes.Data)
    smaller_opcode = Opcodes(type_formatter=uint8_t)
    timestamp = uint64_t()


class ThirdHeader(Struct):
    opcode = Opcodes()
    useless_variable = uint8_t()


if __name__ == '__main__':
    print '>> Enums Classes'

    header = AnotherHeader()
    print binascii.hexlify(header.serialize())
