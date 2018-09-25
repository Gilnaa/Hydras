#!/usr/bin/env python
"""
This example demonstrates how to implement several of `Struct`'s hooks.

:file: hooks.py
:date: 08/09/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

from hydra import *

class DynamicStruct(Struct):
    """ 
    A `Struct` that is aware of serialization and deserialization.

    After serialization, the object changes itself (raises the message index).
    After deserialization, the validate method is called. If it returns False, 
    an exception is thrown,
    """

    # Data members.
    index = UInt32()
    even_message = UInt8()

    # Hooks.
    def after_serialize(self):
        """ Advances the index and updates the even_message member. """
        self.index += 1
        self.even_message = (self.even_message + 1) % 2

    def validate(self):
        """ Ensures the validity of the DynamicStruct's data members. """
        if self.even_message not in xrange(2):
            return False

        if self.index < 0:
            return False

        if self.index % 2 != self.even_message:
            return False

        return True

def print_raw_data(raw_data):
    for byte in raw_data:
        print '%02x' % ord(byte),
    print

if __name__ == '__main__':
    s = DynamicStruct()
    for i in xrange(5):
        print_raw_data(s.serialize())
    # Output:
    #   00 00 00 00 00
    #   01 00 00 00 01
    #   02 00 00 00 00
    #   03 00 00 00 01
    #   04 00 00 00 00
    #  ^ index     ^ even_message

    raw_data = b'\x00\x00\x00\x00\x03'
    try:
        s2 = DynamicStruct.deserialize(raw_data)
    except Exception, e:
        print e 
    # => "The deserialized data is invalid"


    # Available hooks:
    #   - `before_serialize`    Arbitrary method called before serialization.
    #                           Depends on the `dry_run` setting.
    #
    #   - `after_serialize`     Arbitrary method called after serialization.
    #                           Depends on the `dry_run` setting.
    #
    #   - `validate`            Validation method called after deserialization.
    #                           Should return True/False.
    #                           Depends on the `validate` setting.
