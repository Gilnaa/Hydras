#!/usr/bin/env python
"""
This example shows the usage of the Offset feature class.

:file: offset.py
:date: 09/03/2016
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from hydras import *
from binascii import hexlify


# A simple struct that will be used for the example
class A(Struct):
    a = uint8_t(1)
    b = uint8_t(2)
    c = uint8_t(3)
    d = uint8_t(4)
    e = uint8_t(5)
    f = uint8_t(6)
    g = uint8_t(7)
    h = uint8_t(8)
    i = uint8_t(9)


if __name__ == '__main__':
    print('A#d has the offset', A.offsetof(A.d))    # => "A#d has the offset 3"
    print('A#h has the offset', A.offsetof(A.h))    # => "A#d has the offset 7"

    obj = A()
    print(hexlify(obj.serialize()))                     # => "010203040506070809"
    print(hexlify(obj.serialize(start=A.c)))            # =>     "03040506070809"
    print(hexlify(obj.serialize(end=A.f)))              # => "010203040506"
    print(hexlify(obj.serialize(start=A.c, end=A.f)))   # =>     "03040506"
