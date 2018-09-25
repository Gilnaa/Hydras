"""
:file: enums.py

Contains the enum type formatter.

:date: 20/01/2016
:authors:
    - Kfir Gollan
"""

import struct
from .base import TypeFormatter
from .utils import padto, string2bytes


class Bcd(TypeFormatter):

    def __init__(self, digits, default_value=0, compressed=True, *args, **kwargs):
        self.byte_count = digits if not compressed else (digits + 1) // 2
        if compressed and digits % 2 != 0:
            raise ValueError('Compressed BCD must have an even number of digits')

        if int(default_value) != default_value or default_value < 0:
            raise ValueError('Default value can only be a positive integer')

        if self.byte_count <= 1:
            self.fstring = '>B'
        elif self.byte_count <= 2:
            self.fstring = '>H'
        elif self.byte_count <= 4:
            self.fstring = '>I'
        elif self.byte_count <= 8:
            self.fstring = '>Q'
        else:
            raise ValueError('A BCD number cannot take more than 8 bytes')

        self.mask = 0xf if compressed else 0xff
        self.shift = 4 if compressed else 8

        super(Bcd, self).__init__(default_value, *args, **kwargs)

    def values_equal(self, a, b):
        if not isinstance(a, (str, bytes)):
            a = self.format(a)
        if not isinstance(b, (str, bytes)):
            b = self.format(b)
        return a == b

    def validate(self, value):
        """
        Validate the specified value by checking it against the items list.

        :param value:   The value to validate.
        :return:    `True` if the value is valid; `False` otherwise.
        """
        try:
            self.format(value)
        except:
            return False

        return super(Bcd, self).validate(value)

    def __len__(self):
        return self.byte_count

    def parse(self, raw_data, settings={}):
        padded_len = {'>B': 1, '>H': 2, '>I': 4, '>Q': 8}[self.fstring]
        val = struct.unpack(self.fstring, padto(raw_data, padded_len, leftpad=True))[0]
        mult = 1
        parsed = 0
        while val:
            data = val & self.mask
            if data > 9:
                raise ValueError('Invalid BCD value')
            parsed += data * mult
            mult *= 10
            val >>= self.shift

        return parsed

    def format(self, value, settings={}):
        if isinstance(value, (str, bytes)):
            if len(value) > len(self):
                raise ValueError('Cannot fit {} bytes into {} bytes'.format(len(value), len(self)))
            # Pad value and return it
            val = padto(string2bytes(value), len(self), leftpad=True)
            self.parse(val)
            return val

        bcd = 0
        mult = 0
        while value:
            bcd += (value % 10) << (self.shift * mult)
            value /= 10
            mult += 1

        formatted = struct.pack(self.fstring, bcd)
        diff = len(formatted) - len(self)
        if diff:
            for i in range(diff):
                if ord(formatted[i]) != 0:
                    raise ValueError('{} Cannot be encoded in {} bytes'.format(value, len(self)))
            formatted = formatted[diff:]
        return formatted
