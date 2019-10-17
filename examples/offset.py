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
    a = u8(1)
    b = u8(2)
    c = u8(3)
    d = u8(4)
    e = u8(5)
    f = u8(6)
    g = u8(7)
    h = u8(8)
    i = u8(9)


if __name__ == '__main__':
    print('A#d has the offset', A.offsetof(A.d))    # => "A#d has the offset 3"
    print('A#h has the offset', A.offsetof(A.h))    # => "A#d has the offset 7"

    obj = A()
    print(hexlify(obj.serialize()))                     # => "010203040506070809"
    print(hexlify(obj.serialize(start=A.c)))            # =>     "03040506070809"
    print(hexlify(obj.serialize(end=A.f)))              # => "010203040506"
    print(hexlify(obj.serialize(start=A.c, end=A.f)))   # =>     "03040506"
