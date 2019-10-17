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


class SmallStruct(Struct):
    a = u8(0xAA)
    b = u8(0xFF)


class HasArraysInIt(Struct):
    byte_array = Array(8)
    dword_array = u32[2]
    object_array = SmallStruct[4]


if __name__ == '__main__':
    obj = HasArraysInIt()

    print(obj.byte_array)
    # => [0, 0, 0, 0, 0, 0, 0, 0]
    print(obj.dword_array)
    # => [0, 0]
    print(obj.object_array)
    # => [{
    #        a: 170
    #        b: 255
    #    }, {
    #        a: 170
    #        b: 255
    #    }, {
    #        a: 170
    #        b: 255
    #    }, {
    #        a: 170
    #        b: 255
    #    }]

    print(binascii.hexlify(obj.serialize()))
    # => 00000000000000000000000000000000aaffaaffaaffaaff

    obj.byte_array = [0xFF]
    print(binascii.hexlify(obj.serialize()))
    # => ff000000000000000000000000000000aaffaaffaaffaaff

    obj.byte_array = [0xFF, 0xEE, 0xDD]
    print(binascii.hexlify(obj.serialize()))
    # => ffeedd00000000000000000000000000aaffaaffaaffaaff

    obj.dword_array = [0xDEADBEEF, 0xCAFECAFE]
    print(binascii.hexlify(obj.serialize()))
    # => ffeedd0000000000efbeaddefecafecaaaffaaffaaffaaff

    obj = HasArraysInIt()
    obj.object_array[0].a = 0xBB
    obj.object_array[0].b = 0xCC
    print(binascii.hexlify(obj.serialize()))
    # => 00000000000000000000000000000000bbccaaffaaffaaff
