"""
:file: union.py

Contains the union type formatter.

:date: 20/01/2016
:authors:
    - Kfir Gollan
"""

import struct
import inspect
from .base import TypeFormatter
from .vectors import NestedStruct
from .utils import padto, get_as_type, get_as_value

class ParsedUnion(object):
    def __init__(self, types, binary_data):
        super(ParsedUnion, self).__init__()

        if not all(isinstance(t, TypeFormatter) for t in types):
            raise ValueError('All union types must inherit TypeFormatter')

        self.formatters = types
        self.binary_data = binary_data

    def get(self, typ):
        typ = get_as_type(typ)

        for t in self.formatters:
            if (type(t) == typ or
                    type(t) is NestedStruct and t.nested_object_type == typ):
                return t.parse(self.binary_data[:len(t)])

        raise ValueError('Requested type not part of the union')

    def __len__(self):
        return len(self.binary_data)

    def __repr__(self):
        return 'ParsedUnion {} [{}]'.format(self.formatters, len(self))


class Union(TypeFormatter):

    def __init__(self, types, default_value=None, pad_length=0, *args, **kwargs):
        self.formatters = tuple(get_as_value(t) if issubclass(get_as_type(t), TypeFormatter) else NestedStruct(t) for t in types)

        if len(self.formatters) < 2:
            raise ValueError('A union must contain at least 2 types')

        if not all(isinstance(t, TypeFormatter) for t in self.formatters):
            raise ValueError('All union types must inherit TypeFormatter')

        if default_value is not None and (
                inspect.isclass(default_value) or type(default_value) not in (type(t) for t in self.formatters)):
            raise ValueError('default_value must be an instance of one of the union types')

        self.byte_count = max(pad_length, max(len(t) for t in self.formatters))

        super(Union, self).__init__(default_value, *args, **kwargs)

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

        return super(Union, self).validate(value)

    def __len__(self):
        return self.byte_count

    def parse(self, raw_data, settings=None):
        return ParsedUnion(self.formatters, raw_data)

    def format(self, value, settings=None):
        if isinstance(value, (str, bytes)) and len(value) == len(self):
            return value

        for t in self.formatters:
            if (type(t) == type(value) or
                    type(t) is NestedStruct and t.nested_object_type == type(value)):
                return padto(t.format(value), len(self))
        else:
            if isinstance(value, ParsedUnion) and value.formatters == self.formatters and len(value) == len(self):
                return value.binary_data

        raise ValueError('Invalid union value')
