#!/usr/bin/env python

# `hydra` is designed to be imported with this notation.
# You can use the regular import notation, but it can get a bit cumbersome.
from hydras import *


# You can inherit from the Struct class to define a description of
# the memory layout of a structure.
class StructName(Struct):
    FieldName = u32        # Unsigned; 4 bytes.
    AnotherField = u8(87)  # Signed; 1 byte. Default value is 87
    SpareForAlignment = u8[3]  # Padding.
    ThirdField = u64       # Signed; 8 bytes.


if __name__ == '__main__':
    # Create a new instance of the struct.
    struct_instance = StructName()
    # =>
    #    FieldName: 0 
    #    AnotherField: 87
    #    SpareForAlignment: b'\x00\x00\x00'
    #    ThirdField: 0

    # You can freely set the properties of the struct.
    struct_instance.FieldName = 128
    struct_instance.ThirdField = 0xAA000000000000FF

    # This is how you serialize a struct.
    packed_data = struct_instance.serialize()  # => b'\x80\x00\x00\x00\x57\x00\x00\x00\xFF\x00\x00\x00\x00\x00\x00\xAA'

    # This is how you deserialize a struct from packed data.
    deserialized_struct = StructName.deserialize(packed_data)
    # =>
    #    FieldName: 128
    #    AnotherField: 87
    #    SpareForAlignment: b'\x00\x00\x00'
    #    ThirdField: 12249790986447749375L

    assert struct_instance == deserialized_struct
