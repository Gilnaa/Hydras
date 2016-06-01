"""
Contains non-trivial type formatters.

:file:  vectors.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
"""

from .base import *
from .compatibility import *
from .scalars import *
from .utils import *

import struct
import copy
import inspect


class Pad(TypeFormatter):
    def __init__(self, length=1, *args, **kwargs):
        self.length = length
        super(Pad, self).__init__(b'\x00' * length, *args, **kwargs)

    def __len__(self):
        return self.length

    def format(self, value, settings=None):
        return value

    def parse(self, raw_data, settings=None):
        return fit_bytes_to_size(raw_data, self.length)


class Array(TypeFormatter):
    def __init__(self, length, items_type=UInt8, default_value=None, *args, **kwargs):
        # Defaults
        self.is_type_scalar = False
        self.nested_struct_type = None
        self.scalar_format_string = 'B'

        alternate_default_value = self.init_type_resolver(items_type, length)

        self.length = length
        if self.is_type_scalar:
            self.byte_size = length * len(items_type())
        else:
            self.byte_size = length * len(alternate_default_value[0])

        if default_value is None:
            default_value = alternate_default_value

        super(Array, self).__init__(default_value, *args, **kwargs)

    def init_type_resolver(self, items_type, length):
        if isinstance(items_type, Struct):
            self.nested_struct_type = type(items_type)
            return [copy.deepcopy(items_type) for i in xrange(length)]
        elif inspect.isclass(items_type) and issubclass(items_type, Struct):
            self.nested_struct_type = items_type
            return [items_type() for i in xrange(length)]
        elif inspect.isclass(items_type) and issubclass(items_type, Scalar):
            self.is_type_scalar = True
            self.scalar_format_string = items_type().format_string
            self.nested_struct_type = items_type
            return [0] * length

        raise TypeError('Array: items_type should be either a scalar type, a struct, or a struct object.')

    def format(self, value, settings=None):
        settings = HydraSettings.resolve(self.settings, settings)
        if self.is_type_scalar:
            if isinstance(value, str):
                return fit_bytes_to_size(value, len(self))

            endian = settings['endian']
            format_string = '%s%d%s' % (endian, len(value), self.scalar_format_string)

            output = struct.pack(format_string, *value)
            return fit_bytes_to_size(output, len(self))
        else:
            output = b''
            for nested_struct in value:
                output += nested_struct.serialize(settings)

            return fit_bytes_to_size(output, len(self))

    def parse(self, raw_data, settings=None):
        if len(raw_data) != len(self):
            raise ValueError('Raw data is not in the correct length.')

        settings = HydraSettings.resolve(self.settings, settings)

        raw_data = string2bytes(raw_data)

        if self.is_type_scalar:
            format_string = '%s%d%s' % (settings['endian'], len(self), self.scalar_format_string)
            return list(struct.unpack(format_string, raw_data))

        output = []

        chunks = to_chunks(raw_data, len(self.nested_struct_type()))
        for raw_chunk in chunks:
            output.append(self.nested_struct_type.deserialize(raw_chunk, settings))

        return output

    def __len__(self):
        return self.byte_size

    def values_equal(self, a, b):
        if isinstance(a, list):
            a = self.format(a)
        if isinstance(b, list):
            b = self.format(b)
        return a == b


class NestedStruct(TypeFormatter):

    def __init__(self, struct, *args, **kwargs):
        default_value = None
        if inspect.isclass(struct) and issubclass(struct, Struct):
            self.nested_object_type = struct
            default_value = struct()
        elif isinstance(struct, Struct):
            self.nested_object_type = type(struct)
            default_value = struct
        else:
            raise TypeError('"struct" parameter must be either a Struct subclass or a Struct object.')

        super(NestedStruct, self).__init__(default_value, *args, **kwargs)

    def format(self, value, settings=None):
        return value.serialize(settings)

    def parse(self, raw_data, settings=None):
        return self.nested_object_type.deserialize(raw_data, settings)

    def __len__(self):
        return len(self.default_value)