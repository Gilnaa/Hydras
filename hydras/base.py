"""
Contains the core classes of the framework.

:file: base.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

import copy
import collections
from typing import Any, List, Dict, Union, Iterator, Callable
from abc import ABCMeta, abstractmethod
from .validators import *


class HydraSettings:
    """ Contains global default settings. """

    # Determines whether the serialize hooks will be called.
    dry_run = False

    # Determines whether the validate hook will be checked.
    validate = True

    # The endianness of the "target" CPU. By the default is the same as the host.
    target_endian = Endianness.HOST

    def __init__(self, *,
                 dry_run: bool = None,
                 validate: bool = None,
                 target_endian: Endianness = None):

        super().__init__()

        if dry_run is not None:
            self.dry_run = dry_run

        if validate is not None:
            self.validate = validate

        if target_endian is not None:
            self.target_endian = target_endian

    @classmethod
    def resolve(cls, settings):
        """ Resolve settings dictionaries."""
        return settings or cls()

    @classmethod
    def snapshot(cls):
        """ Retrieve a snapshot of the settings at the moment of the call. """
        return {name: value for name, value in vars(cls).items()
                if (not name.startswith('_')) and (type(value) is not classmethod)}

    @classmethod
    def update(cls, new_settings):
        """
        Update the global settings according to the given dictionary.
        Preferences not found in the new dictionary will retain their values.
        Unrecognized keys will be ignored.

        :param new_settings:    A dictionary containing overrides of the settings.
        :return:                A snapshot of the new settings.
        """
        for var, value in new_settings.items():
            if var in vars(cls):
                setattr(cls, var, value)

        return cls.snapshot()


class RenderOptions:
    def __init__(self,
                 indent='    ',
                 compact_bytes=False,
                 hex_integers=False,
                 no_line_break_in_arrays=False):
        self.indent = indent
        self.compact_bytes = compact_bytes
        self.hex_integers = hex_integers
        self.no_line_break_in_arrays = no_line_break_in_arrays


class SerializerMetadata:
    __slots__ = ('size', )

    def __init__(self, size):
        self.size = size

    def is_constant_size(self) -> bool:
        return True


class SerializerMeta(ABCMeta):
    METAATTR = '_hydras_metadata'

    _hydras_metadata: SerializerMetadata

    def __getitem__(self, item_count):
        """
        This hack enables the familiar array syntax: `type[count]`.
        For example, a 3-item array of type uint8_t might look like `uint8_t[3]`.
        """
        return create_array(item_count, self())

    @property
    def is_constant_size(cls) -> bool:
        return cls._hydras_metadata.is_constant_size()

    @property
    def byte_size(cls) -> int:
        return cls._hydras_metadata.size

    def __len__(self):
        return self.byte_size


class Serializer(metaclass=SerializerMeta):
    """ The base type for Hydra's serializers. """
    __slots__ = ('byte_size', 'is_constant_size', 'validator', 'default_value')

    def __len__(self):
        return self.byte_size

    def __init__(self, default_value, validator: Callable[[Any], bool] = None):
        """
        Creates a new formatter.

        :param default_value:   The default value of the formatter.
        :param validator:       A callable
        """
        self.byte_size = self._hydras_metadata.size
        self.is_constant_size = self._hydras_metadata.is_constant_size()
        self.validator = validator
        self.default_value = default_value

        self.validate(default_value)

    def get_initial_value(self):
        return self.default_value

    def get_initial_values(self, count):
        return [self.get_initial_value() for _ in range(count)]

    def serialize(self, value, settings: HydraSettings = None) -> bytes:
        """ When implemented in derived classes, returns the byte representation of the give value. """
        storage = bytearray(self.get_actual_length(value))
        self.serialize_into(memoryview(storage), 0, value, settings)
        return bytes(storage)

    @abstractmethod
    def serialize_into(self,
                       storage: memoryview,
                       offset: int,
                       value: Any,
                       settings: HydraSettings = None) -> int:
        raise NotImplementedError()

    def serialize_many_into(self,
                            storage: memoryview,
                            offset: int,
                            value: List[Any],
                            min_values_count: int,
                            settings: HydraSettings) -> int:
        for s in value:
            offset = self.serialize_into(storage, offset, s, settings)
        if len(value) < min_values_count:
            s = self.get_initial_value()
            for _ in range(min_values_count - len(value)):
                offset = self.serialize_into(storage, offset, s, settings)
        return offset

    @abstractmethod
    def deserialize(self, raw_data: bytes, settings: HydraSettings = None):
        """ When implemented in derived classes, parses the raw data. """
        raise NotImplementedError()

    def render_lines(self, name, value, options: RenderOptions = None) -> List[str]:
        if name is None:
            return [str(value)]
        return [f'{name}: {str(value)}']  # + str(value).splitlines()

    def validate(self, value):
        """
        Validate the given value using this serializer's rules.
        Raises if invalid

        :param value:   The value to validate.
        """
        if self.validator is not None and not self.validator(value):
            raise ValidationError(value)

    def values_equal(self, a, b):
        """ Determines whether the given two values are equal. """
        return a == b

    def get_actual_length(self, value):
        """ When used on variable length formatters, returns the actual serialized length of the given python value. """
        return self.byte_size

    def __getitem__(self, item_count):
        """
        This hack enables the familiar array syntax: `type()[count]`.
        For example, a 3-item array of type uint8_t might look like `uint8_t(0)[3]`.
        """
        return create_array(item_count, self)
