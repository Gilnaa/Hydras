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

    def test_member_length(self):
        self.assertEqual(len(SimpleStruct.b_first_variable), 1)
        self.assertEqual(len(SimpleStruct.a_second_variable), 2)
        self.assertEqual(len(SimpleStruct.x_third_variable), 1)

        self.assertEqual(len(ComplicatedStruct.other_struct), 1)
        self.assertEqual(len(ComplicatedStruct.some_field), 12)

    def test_serialize_simple(self):
        """ Test serialization of a simple struct. """
        obj = SimpleStruct()
        raw_data = bytes(obj)
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

    def test_derived_struct(self):
        class DerivedStruct(SimpleStruct):
            derived = u8

        class DerivedStructEmpty(SimpleStruct):
            pass

        simple = SimpleStruct()
        derived = DerivedStruct()
        empty = DerivedStructEmpty()

        self.assertEqual(simple.serialize() + b'\x00', derived.serialize())
        self.assertEqual(simple.serialize(), empty.serialize())

    def test_invalid_multiple_derives(self):
        class A(Struct):
            a = u8

        class B(Struct):
            b = u8

        with self.assertRaises(TypeError):
            class C(A, B):
                pass

    def test_pickles(self):
        import pickle
        o = pickle.loads(pickle.dumps(SimpleStruct()))
        self.assertEqual(o, SimpleStruct())

        o = pickle.loads(pickle.dumps(ComplicatedStruct()))
        self.assertEqual(o, ComplicatedStruct())

    def test_mixin(self):
        class Header(Struct):
            a = u8
            b = u16

        class Body(Struct):
            foo = u8
            _hdr = Mixin(Header)
            _hdr2 = Mixin(Header, prefix='h_')
            bar = u8

        expected_members = [('foo', u8()), ('a', u8()), ('b', u16()), ('h_a', u8()), ('h_b', u16()), ('bar', u8())]

        for actual, expected in zip(Body._hydras_members().items(), expected_members):
            self.assertEqual(actual[0], expected[0])
            self.assertTrue(isinstance(actual[1], type(expected[1])))

    def test_mixin_name_clash(self):
        class Header(Struct):
            a = u8

        with self.assertRaises(TypeError):
            class BodyA(Struct):
                a = u8
                _hdr = Mixin(Header)

        with self.assertRaises(TypeError):
            class BodyB(Struct):
                _hdr = Mixin(Header)
                a = u8

        with self.assertRaises(TypeError):
            class BodyC(Struct):
                b = u8
                _hdr = Mixin(Header)
                _hdr2 = Mixin(Header)


if __name__ == '__main__':
    unittest.main()
