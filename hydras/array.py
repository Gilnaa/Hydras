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

        ######
        t = get_as_type(serializer)
        # type is a Struct type/class.
        if issubclass(t, Struct):
            serializer = NestedStruct[serializer]()
        # type is a Scalar class.
        elif issubclass(t, Serializer):
            serializer = get_as_value(serializer)
        else:
            raise TypeError('Array: items_type should be a Serializer or a Struct')
        ######

        serializer = get_as_value(serializer)
        return type(get_type_name(cls), (cls,), {
            '_array_size_min': size_min,
            '_array_size_max': size_max,
            '_serializer': serializer
        })

    def __repr__(cls) -> str:
        if cls.is_constant_size():
            size = f'{cls._array_size_min}:{cls._array_size_max}'
        else:
            size = f'{cls._array_size_min}'
        return f'<array <{cls._serializer}> [{size}]>'


class Pad(Serializer):

    """ A type formatter whose purpose is to act as a data-less padding."""

    def __init__(self, length=1, *args, **kwargs):
        """
        Initialize this `Pad` instance.

        :param length:  The size of this padding, in bytes.
        """
        self.length = length
        super(Pad, self).__init__(b'\x00' * length, *args, **kwargs)

    def __len__(self):
        """ Return the size of this padding, in bytes."""
        return self.length

    def render(self, value, name):
        from binascii import hexlify
        return '{}: {}'.format(name, hexlify(value))

    def format(self, value, settings=None):
        return value

    def parse(self, raw_data, settings=None):
        return fit_bytes_to_size(raw_data, self.length)


class Array(Serializer, metaclass=ArrayMeta):
    _array_size_min = _array_size_max = 0
    _serializer = None

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
        self.byte_size = self._array_size_min * len(self._serializer)

        if default_value is None:
            default_value = [copy.deepcopy(self._serializer.default_value) for _ in range(self._array_size_min)]
        elif isinstance(default_value, bytes) and not isinstance(self._serializer, u8):
            raise ValueError('Using `bytes` for an array value is only valid when the item type is `u8`')

        super(Array, self).__init__(default_value, *args, **kwargs)

    def format(self, value, settings=None):
        """ Return a serialized representation of this object. """
        settings = HydraSettings.resolve(self.settings, settings)

        return padto(b''.join(self._serializer.format(s, settings) for s in value), len(self))

    def parse(self, raw_data, settings=None):
        fmt_size = len(self._serializer)

        if self._array_size_max is not None and \
                len(raw_data) > self._array_size_max * fmt_size:
            raise ValueError('Raw data is too long for array.')
        elif len(raw_data) < self._array_size_min * fmt_size:
            raise ValueError('Raw data is too short for array.')
        elif len(raw_data) % fmt_size != 0:
            raise ValueError('Raw data is not aligned to item size.')

        settings = HydraSettings.resolve(self.settings, settings)

        parsed = [self._serializer.parse(raw_data[begin:begin+len(self._serializer)], settings)
                  for begin in range(0, len(raw_data), len(self._serializer))]

        if isinstance(self.default_value, bytes):
            parsed = bytes(parsed)

        return parsed

    def __len__(self):
        """ Return the size of this Array in bytes."""
        return self.byte_size

    @classmethod
    def is_constant_size(cls):
        return cls._array_size_min == cls._array_size_max

    def values_equal(self, a, b):
        return len(a) == len(b) and all(self._serializer.values_equal(ai, bi) for ai, bi in zip(a, b))

    def validate_assignment(self, value):
        allowed_types = (tuple, list)
        if self._serializer is u8 or type(self._serializer) is u8:
            allowed_types += (bytes, )

        if not isinstance(value, allowed_types):
            raise TypeError('Assigned value must be a string, tuple, or a list.')

        if self._array_size_max is not None and len(value) > self._array_size_max:
            raise ValueError('Assigned array length is incorrect.')

        return all(self._serializer.validate_assignment(i) for i in value)

    def get_actual_length(self, value):
        return len(value) * len(self._serializer)
