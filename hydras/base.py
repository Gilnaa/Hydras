"""
Contains the core classes of the framework.

:file: base.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

import copy
import collections
from typing import Any, Dict, Union as TypeUnion, Iterator

from .validators import *


class HydraSettings(object):
    """ Contains global default settings. """

    # Determines whether the serialize hooks will be called.
    dry_run = False

    # Determines whether the validate hook will be checked.
    validate = True

    # The endianness of the "target" CPU. By the default is the same as the host.
    target_endian = Endianness.HOST

    @classmethod
    def resolve(cls, *args):
        """ Resolve settings dictionaries."""
        global_settings = cls.snapshot()

        for overrides in args:
            if overrides is not None and isinstance(overrides, dict):
                global_settings.update(overrides)

        return global_settings

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


def _create_array(size: TypeUnion[int, slice], underlying_type):
    # Importing locally in order to avoid weird import-cycle issues
    from .array import Array
    return Array[size, underlying_type]


class SerializerMetadata:
    __slots__ = ('size', )

    def __init__(self, size):
        self.size = size

    def is_constant_size(self) -> bool:
        return True


class SerializerMeta(type):
    METAATTR = '__hydras_metadata'

    def __getitem__(self, item_count):
        """
        This hack enables the familiar array syntax: `type[count]`.
        For example, a 3-item array of type uint8_t might look like `uint8_t[3]`.
        """
        return _create_array(item_count, self)

    @property
    def is_constant_size(cls) -> bool:
        return cls.__hydras_metadata__.is_constant_size()

    @property
    def byte_size(cls) -> int:
        return cls.__hydras_metadata__.size

    @property
    def __hydras_metadata__(cls) -> SerializerMetadata:
        return getattr(cls, cls.METAATTR)


class Serializer(metaclass=SerializerMeta):
    """ The base type for Hydra's serializers. """

    @property
    def is_constant_size(self) -> bool:
        return self.__hydras_metadata__.is_constant_size()

    @property
    def byte_size(self) -> int:
        return self.__hydras_metadata__.size

    @property
    def __hydras_metadata__(self) -> SerializerMetadata:
        return type(self).__hydras_metadata__

    def __init__(self, default_value, validator=None, settings=None):
        """
        Creates a new formatter.

        :param default_value:   The default value of the formatter.
        :param validator:       [Optional] A validation object.
        :param settings:        [Optional] Serialization settings.
        """
        self.validator = validator
        self.default_value = default_value
        self.settings = settings or {}

        if not self.validate(default_value):
            raise ValueError('Default value validation failed')

    def resolve_settings(self, overrides=None):
        """ Resolves the flat settings for a single action on this formatter. """
        return HydraSettings.resolve(overrides, self.settings)

    def format(self, value, settings=None) -> bytes:
        """ When implemented in derived classes, returns the byte representation of the give value. """
        raise NotImplementedError()

    def parse(self, raw_data, settings=None):
        """ When implemented in derived classes, parses the raw data. """
        raise NotImplementedError()

    def validate(self, value) -> bool:
        """
        Validate the given value using this serializer's rules.

        :param value:   The value to validate.
        :return:        `True` if the value is valid; `False` otherwise.
        """
        if self.validator is not None:
            if isinstance(self.validator, Validator):
                return self.validator.validate(value)

            if hasattr(get_as_type(self.validator), '__call__'):
                return self.validator(value)

        return True

    def values_equal(self, a, b):
        """ Determines whether the given two values are equal. """
        return a == b

    def get_actual_length(self, value):
        """ When used on variable length formatters, returns the actual serialized length of the given python value. """
        return self.byte_size

    def __getitem__(self, item_count):
        return _create_array(item_count, self)
