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
        if cls.is_constant_size():
            size = f'{cls.__hydras_metadata__.array_size_min}:{cls.__hydras_metadata__.array_size_max}'
        else:
            size = f'{cls.__hydras_metadata__.array_size_min}'
        return f'<array <{cls.__hydras_metadata__.serializer}> [{size}]>'


class Array(Serializer, metaclass=ArrayMeta):
    """
    A type formatter which enables the developer to format a list of items.

    The default value's type is a byte (uint8_t), but can subtituted for any Struct or Scalar.
    """

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
        if default_value is None:
            default_value = [copy.deepcopy(self.serializer.default_value) for _ in range(self.min_size)]
        elif isinstance(default_value, (bytes, bytearray)) and not isinstance(self.serializer, BYTE_TYPES):
            raise TypeError('Using `bytes` or `bytearray` for an array value is only valid when the item type is `u8`')
        elif not isinstance(default_value, self.allowed_py_types):
            raise TypeError('Default value of invalid type', default_value)

        super(Array, self).__init__(default_value, *args, **kwargs)

    @property
    def serializer(self):
        return self.__hydras_metadata__.serializer

    @property
    def min_size(self):
        return self.__hydras_metadata__.array_size_min

    @property
    def max_size(self):
        return self.__hydras_metadata__.array_size_max

    @property
    def allowed_py_types(self):
        base_list = (list, tuple)
        if isinstance(self.serializer, BYTE_TYPES):
            base_list += (bytes, bytearray)
        return base_list

    def serialize(self, value, settings: HydraSettings = None):
        """ Return a serialized representation of this object. """

        return padto(b''.join(self.serializer.serialize(s, settings) for s in value), self.byte_size)

    def deserialize(self, raw_data, settings: HydraSettings = None):
        fmt_size = self.serializer.byte_size

        if self.max_size is not None and \
                len(raw_data) > self.max_size * fmt_size:
            raise ValueError('Raw data is too long for array.')
        elif len(raw_data) < self.min_size * fmt_size:
            raise ValueError('Raw data is too short for array.')
        elif len(raw_data) % fmt_size != 0:
            raise ValueError('Raw data is not aligned to item size.')

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

        for i in value:
            self.serializer.validate(i)

        super(Array, self).validate(value)

    def get_actual_length(self, value):
        return len(value) * self.serializer.byte_size
