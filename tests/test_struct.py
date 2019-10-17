#!/usr/bin/env python
"""
Contains various tests for the `Struct` class of the base module.

:file: StructTests.py
:date: 30/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .utils import *

#########################
# "Structs" for testing #
#########################


class SmallStruct(Struct):
    only_element = u8


class SimpleStruct(Struct):
    b_first_variable = u8(0xDE)
    a_second_variable = u16(0xCAFE)
    x_third_variable = u8(0xAD)


class ComplicatedStruct(Struct):
    other_struct = SmallStruct
    some_field = SimpleStruct[3]
    numeric = u32


##############
# Test Cases #
##############


class StructTests(HydrasTestCase):
    """ A testcase checking for a few of `Struct`'s features. """

    def test_serialize_simple(self):
        """ Test serialization of a simple struct. """
        obj = SimpleStruct()
        raw_data = obj.serialize()
        self.assertEqual(raw_data, b'\xDE\xFE\xCA\xAD')

    def test_one_does_not_complicatedly(self):
        """ Test serialization and deserialization of a more complicated struct."""
        s = ComplicatedStruct()
        s.numeric = 0xAEAEAEAE
        data = s.serialize()
        # Test serialization.
        self.assertEqual(data, b'\x00\xDE\xFE\xCA\xAD\xDE\xFE\xCA\xAD\xDE\xFE\xCA\xAD\xAE\xAE\xAE\xAE')

        # Test deserialization.
        d_s = ComplicatedStruct.deserialize(data)
        self.assertEqual(d_s, s)
    
    def test_dict_conversion(self):
        d = dict(ComplicatedStruct())
        expected_dict = {
                'other_struct': {'only_element': 0},
                'some_field': [
                    {'b_first_variable': 0xDE, 'a_second_variable': 0xCAFE, 'x_third_variable': 0xAD},
                    {'b_first_variable': 0xDE, 'a_second_variable': 0xCAFE, 'x_third_variable': 0xAD},
                    {'b_first_variable': 0xDE, 'a_second_variable': 0xCAFE, 'x_third_variable': 0xAD},
                    ],
                'numeric': 0
            }
        self.assertEqual(d, expected_dict)


if __name__ == '__main__':
    unittest.main()
