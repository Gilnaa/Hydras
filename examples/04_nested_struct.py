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


class SomeHeader(Struct):
    opcode = uint32_t()
    timestamp = uint64_t()


class SomePacket(Struct):
    header = NestedStruct(SomeHeader)
    data = Array(12)


if __name__ == '__main__':
    packet = SomePacket()

    print(type(packet))
    print(type(packet.header))
    print(type(packet.data))
