#!/usr/bin/env python
"""
:file: 01_basics.py

Shows the basic use of the Hydra framework.

:date: 11/06/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from hydras import *
import binascii


class BasicStruct(Struct):
    integer_field = u32
    smaller_field = u16
    signed_field = i32


if __name__ == '__main__':
    struct_object = BasicStruct()
    print(f'integer_field = {struct_object.integer_field}')     # => integer_field = 0
    print(f'smaller_field = {struct_object.smaller_field}')     # => smaller_field = 0
    print(f'signed_field = {struct_object.signed_field}')       # => signed_field = 0

    data = struct_object.serialize()
    print('serialized data:', binascii.hexlify(data))           # => serialized data: 00000000000000000000

    struct_object.integer_field = 42
    struct_object.smaller_field = 0xCAFE
    struct_object.signed_field = -128

    data = struct_object.serialize()
    print('new serialized data:', binascii.hexlify(data))       # => new serialized data: 2a000000feca80ffffff

    data = struct_object.serialize(HydraSettings(target_endian=Endianness.BIG))
    print('big-endian serialization:', binascii.hexlify(data))
    # => big-endian serialized data: 0000002acafeffffff80
