"""
Contains the core classes of the framework.

:file: base.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

import copy
import collections
from typing import Any, Dict, Union as TypeUnion

from .validators import *


class HydraSettings(object):
    """ Contains global default settings. """

    # Determines whether the serialize hooks will be called.
    dry_run = False

    # Determines whether the validate hook will be checked.
    validate = True

    # Determines whether parsed enum literals have to be part of the enum.
    strong_enum_literals = True

    # When True, renders enum values as integers instead of strings.
    render_enums_as_integers = False

    # When True and `render_enums_as_integers == False`, renders enum literals as "EnumName.LiteralName"
    full_enum_names = True

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


class SerializerMeta(type):
    def __getitem__(self, item_count):
        """
        This hack enables the familiar array syntax: `type[count]`.
        For example, a 3-item array of type uint8_t might look like `uint8_t[3]`.
        """
        return _create_array(item_count, self)

    def __len__(self):
        """
        Enables the user to call `len(type)`.
        For example, `len(u32) == len(u32()) == 4`

        This only works for serializers with a parameterless constructor,
        but we have no user-facing serializers whose constructors require a parameter.
        """
        return len(self())


class Serializer(metaclass=SerializerMeta):
    """ The base type for Hydra's serializers. """

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
        Validate the given value using this formatters rules.

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

    def render(self, value, name):
        """ Returns a displayable string for the given value. """
        return '%s: %s' % (name, value)

    @classmethod
    def is_constant_size(cls):
        """ Indicates wether this type formatter emits constant-sized buffers. """
        return True

    def validate_assignment(self, value):
        """ Validates a python value to make sure it is a sensible choice for this field. """
        return True

    def get_actual_length(self, value):
        """ When used on variable length formatters, returns the actual serialized length of the given python value. """
        return len(self)

    def __len__(self):
        """ Returns the length (byte size) of the formatter's type. """
        raise NotImplementedError()

    def __getitem__(self, item_count):
        return _create_array(item_count, self)
