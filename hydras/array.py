"""
Contains non-trivial type formatters.

:file:  array.py
:date:  27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

from .base import *
from .struct import *
from .scalars import *
from .utils import *
import copy
import binascii
import itertools

BYTE_TYPES = (u8, u8_be, u8_le)


class ArrayMetadata(SerializerMetadata):
    __slots__ = ('array_size_min', 'array_size_max', 'serializer')

    def __init__(self, array_size_min: int, array_size_max: int, serializer: Serializer):
        super().__init__(array_size_min * serializer.byte_size)
        self.array_size_min = array_size_min
        self.array_size_max = array_size_max
        self.serializer = serializer

    def is_constant_size(self) -> bool:
        return self.array_size_min == self.array_size_max


class ArrayMeta(SerializerMeta):
    def __getitem__(cls, args):
        is_array_type = (
                issubclass(cls, Array) and
                getattr(cls, '__module__', None) == __name__ and
                getattr(sys.modules[__name__], get_type_name(cls), None) == cls)

        if not is_array_type or not isinstance(args, tuple) or len(args) != 2:
            return super().__getitem__(args)

        size, serializer = args
        if isinstance(size, int):
            if size < 0:
                raise ValueError(f'Array size must not be negative, got {size}')
            size_min = size_max = size
        elif isinstance(size, slice):
            size_min, size_max = size.start or 0, size.stop
            if size.step is not None:
                raise ValueError('Cannot supply step to Array size')
            elif not isinstance(size_min, int) or not isinstance(size_max, (int, type(None))):
                raise ValueError('Array min and max length must be integers')
            elif size_min < 0:
                raise ValueError(f'Array minimum size must not be negative, got {size_min}')
            elif size_max is not None and size_max < size_min:
                raise ValueError('Array maximum size must be greater than its minimum size')
        else:
            raise TypeError(f'Expected int or a slice as array size, got {get_type_name(size)}')

        if not issubclass(type(serializer), Serializer):
            raise TypeError('Array: items_type must be a Serializer')

        serializer = get_as_value(serializer)
        return type(get_type_name(cls), (cls,), {
            SerializerMeta.METAATTR: ArrayMetadata(size_min, size_max, serializer)
        })

    def __repr__(cls) -> str:
        if not cls.is_constant_size:
            size = f'{cls.__hydras_metadata__.array_size_min}:{cls.__hydras_metadata__.array_size_max}'
        else:
            size = f'{cls.__hydras_metadata__.array_size_min}'
        return f'{cls.__hydras_metadata__.serializer}[{size}]'


class Array(Serializer, metaclass=ArrayMeta):
    """
    A type formatter which enables the developer to format a list of items.

    The default value's type is a byte (uint8_t), but can subtituted for any Struct or Scalar.
    """
    __slots__ = ('serializer', 'min_size', 'max_size', 'allowed_py_types')

    def __init__(self, default_value=None, *args, **kwargs):
        """
        Initialize this Array object.

        Note:
            `items_type` can be a class derived from `Scalar`, a class derived
            from `Struct` or an object of this class.
            Any other value will cause a `TypeError` to be raised.

        :param length:          The number of items in this Array.
        :param items_type:      The type of each item in the Array. [default: `uint8_t`]
        :param default_value:   The default value for the Array.    [default: `None`]

        :param args:            A paramater list to be passed to the base class.
        :param kwargs:          A paramater dict to be passed to the base class.
        """
        # Caching because calling `__hydras_metadata__` has a non-trivial overhead
        metadata = self.__hydras_metadata__
        self.serializer = metadata.serializer
        self.min_size = metadata.array_size_min
        self.max_size = metadata.array_size_max
        self.allowed_py_types = (list, tuple)
        if isinstance(self.serializer, BYTE_TYPES):
            self.allowed_py_types += (bytes, bytearray)

        if default_value is None:
            default_value = self.serializer.get_initial_values(self.min_size)
        elif isinstance(default_value, (bytes, bytearray)) and not isinstance(self.serializer, BYTE_TYPES):
            raise TypeError('Using `bytes` or `bytearray` for an array value is only valid when the item type is `u8`')
        elif not isinstance(default_value, self.allowed_py_types):
            raise TypeError('Default value of invalid type', default_value)

        super(Array, self).__init__(default_value, *args, **kwargs)

    def serialize_into(self, storage: memoryview, offset: int, value, settings: HydraSettings = None) -> int:
        """ Return a serialized representation of this object. """

        # TODO: When using a scalar, this function always pads with zeroes, instead of with the default value
        return self.serializer.serialize_many_into(storage, offset, value, self.min_size, settings)

    def deserialize(self, raw_data, settings: HydraSettings = None):
        fmt_size = self.serializer.byte_size

        if self.max_size is not None and \
                len(raw_data) > self.max_size * fmt_size:
            raise ValueError('Raw data is too long for array.')
        elif len(raw_data) < self.min_size * fmt_size:
            raise ValueError('Raw data is too short for array.')
        elif len(raw_data) % fmt_size != 0:
            raise ValueError('Raw data is not aligned to item size.')

        # Skip deserialization when the output is bytes.
        if isinstance(self.default_value, (bytes, bytearray)):
            parsed = type(self.default_value)(raw_data)
        elif isinstance(self.serializer, Scalar):
            fmt = self.serializer.get_format_string(settings, len(raw_data) // self.serializer.byte_size)
            parsed = type(self.default_value)(struct.unpack(fmt, raw_data))
        else:
            parsed = type(self.default_value)(self.serializer.deserialize(raw_data[begin:begin + self.serializer.byte_size], settings)
                                              for begin in range(0, len(raw_data), self.serializer.byte_size))

        return parsed

    def values_equal(self, a, b):
        return len(a) == len(b) and all(self.serializer.values_equal(ai, bi) for ai, bi in zip(a, b))

    def validate(self, value):
        if not isinstance(value, self.allowed_py_types):
            raise TypeError('Assigned value must be a tuple or a list.')

        if self.max_size is not None and len(value) > self.max_size:
            raise ValueError('Assigned array length is incorrect.')

        if not isinstance(value, (bytes, bytearray)):
            for i in value:
                self.serializer.validate(i)

        super(Array, self).validate(value)

    def get_actual_length(self, value):
        return len(value) * self.serializer.byte_size

    def __repr__(self) -> str:
        if not self.is_constant_size:
            size = f'{self.min_size}:{self.max_size}'
        else:
            size = f'{self.min_size}'
        return f'{self.serializer}[{size}]'

    def render_lines(self, name, value, options: RenderOptions = None) -> List[str]:
        options = options or RenderOptions()
        if options.compact_bytes and isinstance(value, (bytes, bytearray)):
            prefix = f'{name}: ' if name is not None else ''
            return [f'{prefix}{binascii.hexlify(value)}']

        if name is not None:
            lines = [f'{name}: [ ']
        else:
            lines = ['[ ']

        for v in value:
            cur_lines = [options.indent + l
                         for l in self.serializer.render_lines(None, v, options)]
            cur_lines[-1] += ', '
            if not options.no_line_break_in_arrays:
                lines.extend(cur_lines)
            else:
                lines[-1] += cur_lines[0].lstrip()
                lines.extend(cur_lines[1:])

        if not options.no_line_break_in_arrays:
            lines.append(']')
        else:
            lines[-1] += ']'
        return lines
