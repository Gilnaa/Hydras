"""
Contains the bitfield type formatter implementation.

:file: bitfield.py
:date: 03/09/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

import collections

from .base import *
from .utils import *


sequential_id = 0


def get_next_id():
    """ Returns an incrementing counter that is globally-unique """
    global sequential_id
    sequential_id += 1
    return sequential_id


class Bits(object):
    """ A class used to define a bit section. """

    def __init__(self, size, default_value=0):
        """
        Construct a new bit section object.

        :param size:            The size of the section, in bits.
        :param default_value:   The initial value of the bit section.
        """
        self.id = get_next_id()
        self.size = size
        self.default_value = default_value


class BitField(Serializer):
    """ A type formatter class used to format a bitfield. """

    def __init__(self, *args, **kwargs):
        """
        Construct a new BitField object.

        Bit sections should be passed using named arguments, in their designated order.
        Example:

            field = BitField(first_field=Bits(5),
                                second_field=Bits(2))
        """
        bits_names = list(filter(lambda key: isinstance(kwargs[key], Bits), kwargs))
        bits_names.sort(key=lambda bits_name: kwargs[bits_name].id)

        self.bits = collections.OrderedDict()
        self.length_in_bits = 0
        for name in bits_names:
            self.bits[name] = kwargs[name]
            self.length_in_bits += self.bits[name].size

            # The arguments are delete so they won't get passed to the base-constructor.
            del kwargs[name]

        self.padding_bits = (8 - self.length_in_bits) % 8
        self.byte_size = (self.length_in_bits + self.padding_bits) // 8

        default_value = {name: self.bits[name].default_value for name in self.bits}

        super(BitField, self).__init__(default_value, *args, **kwargs)

    def format(self, value, settings=None):
        """
        Return a serialized version of the given value.

        :param value:       A dictionary mapping bit-fields names to values.
        :param settings:    An optional dictionary of serialization settings.
        :return:            A byte string.
        """
        # Note:
        #   This code was written based on information extracted from:
        #   http://mjfrazer.org/mjfrazer/bitfields/

        unknown_keys = set(value.keys()) - set(self.bits.keys())
        if len(unknown_keys) > 0:
            raise KeyError('Unknown bitfield field names: %s' % list(unknown_keys))

        settings = self.resolve_settings(settings)
        little_endian = is_little_endian(settings['endian'])

        bits = self.bits.items()
        if little_endian:
            bits = list(bits)[::-1]

        # Create an integer containing all the bit sections in the right order.
        # The order is determined by the above condition.
        byte_value = 0
        for name, bit_section in bits:
            bit_value = bit_section.default_value
            if name in value:
                bit_value = value[name]

            if settings['enforce_bitfield_size'] and (bit_value.bit_length() > bit_section.size):
                raise ValueError('Bitfield value %u exceeds maximum bit size. ("%s": %u bits)' %
                                 (bit_value, name, bit_section.size))

            bit_value &= mask(bit_section.size)
            byte_value = (byte_value << bit_section.size) | bit_value

        # Big endian bitfields have the padding on the LSB end.
        if not little_endian:
            byte_value <<= self.padding_bits

        # Convert the integer into a byte-list using struct.pack.
        output = b''
        for byte_index in range(self.byte_size):
            output += struct.pack('B', byte_value & 0xFF)
            byte_value >>= 8

        if not little_endian:
            output = output[::-1]

        return output

    def parse(self, raw_data, settings=None):
        """
        Parse the given byte string into a usable value.

        :param raw_data:    A string of bytes.
        :param settings:    Optional deserialization settings.
        :return:            A dictionary mapping bit-fields names to values.
        """
        settings = self.resolve_settings(settings)
        little_endian = is_little_endian(settings['endian'])
        bits = self.bits.items()

        if little_endian:
            raw_data = raw_data[::-1]
        else:
            bits = list(bits)[::-1]

        num = 0
        for byte in raw_data:
            # Compatability: In python3, iterating a bytes object will yield an integer,
            #                   in python2 the iteration will yield a string.
            if type(byte) == str:
                byte = ord(byte)

            num = (num << 8) | (byte & 0xFF)

        if not little_endian:
            num >>= self.padding_bits

        output = {}
        for name, bit_section in bits:
            output[name] = (num & mask(bit_section.size))
            num = num >> bit_section.size

        return output

    def __len__(self):
        """ Return the byte size of this bitfield. """
        return self.byte_size
