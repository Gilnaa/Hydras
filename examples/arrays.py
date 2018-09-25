#!/usr/bin/env python
"""
This example shows the usage of the TypedArray class.

:file: arrays.py
:date: 08/09/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""
from hydra import *


class SmallStruct(Struct):
    member = UInt16()
    spare = Pad(2)


class ThisIsAStruct(Struct):
    byte_array = TypedArray(8)                  # A byte array with 8 items.
    int_array = TypedArray(5, Int32)            # An integer array with 5 items.
    struct_array = TypedArray(3, SmallStruct)   # An array of 3 struct, each sized 4 bytes.


if __name__ == '__main__':
    instance = ThisIsAStruct()
    # =>
    #   byte_array: [0, 0, 0, 0, 0, 0, 0, 0]
    #   int_array: [0, 0, 0, 0, 0]

    instance.byte_array[5] = 62
    instance.int_array[4] = -6781

    data = instance.serialize()
    # => b'\x0\x0\x0\x0\x0\x3e\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x0\x83\xe5\xff\xff'

    deserialized_instance = ThisIsAStruct.deserialize(data)

    assert instance == deserialized_instance
