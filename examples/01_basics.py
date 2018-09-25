#!/usr/bin/env python
"""
:file: 01_basics.py

Shows the basic use of the Hydra framework.

:date: 11/06/2016
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

from hydra import *
import binascii


class BasicStruct(Struct):
    """ An example struct that contains no meaningful information. """
    integer_field = UInt32()
    smaller_field = UInt16()
    signed_field = Int32()


if __name__ == '__main__':
    struct_object = BasicStruct()
    print 'integer_field =', struct_object.integer_field    # => integer_field = 0
    print 'smaller_field =', struct_object.smaller_field    # => smaller_field = 0
    print 'signed_field =', struct_object.signed_field      # => signed_field = 0

    data = struct_object.serialize()
    print 'serialized data:', binascii.hexlify(data)
    # => serialized data: 00000000000000000000

    struct_object.integer_field = 42
    struct_object.smaller_field = 0xCAFE
    struct_object.signed_field = -128

    data = struct_object.serialize()
    print 'new serialized data:', binascii.hexlify(data)
    # => new serialized data: 2a000000feca80ffffff

    data = struct_object.serialize({'endian': BigEndian})
    print 'big-endian serialized data:', binascii.hexlify(data)
    # => big-endian serialized data: 0000002acafeffffff80
