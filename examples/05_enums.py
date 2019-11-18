#!/usr/bin/env python
"""
:file: 03_arrays.py

A review of the Array type.

:date: 11/06/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from hydras import *
import binascii


class Opcodes(Enum):
    Invalid = auto()
    Data = auto()
    Ack = auto()
    Nack = auto()


class Status(Enum, underlying_type=u8):
    OK = auto()
    Corrupted = auto()
    Unknown = auto()


class AnotherHeader(Struct):
    opcode = Opcodes
    different_default = Opcodes(Opcodes.Data)
    status = Status
    timestamp = u64


class ThirdHeader(Struct):
    opcode = Opcodes
    useless_variable = u8[3]


if __name__ == '__main__':
    header = AnotherHeader()
    print(binascii.hexlify(header.serialize()))
    print(ThirdHeader().useless_variable)
