"""
Contains the core classes of the framework.

:file: base.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

import copy
import collections
from .utils import *
from .validators import *

# `struct` endian definitions
BigEndian = '>'
LittleEndian = '<'
NativeEndian = '='


class HydraSettings(object):
    """ Contains global default settings. """

    # Determines whether the serialize hooks will be called.
    dry_run = False

    # Determines whether the validate hook will be checked.
    validate = True

    # Determines whether the object will be validated on serialize.
    validate_on_serialize = False

    # The endian to use.
    endian = NativeEndian

    # Determines whether the size of the bitfield's fields will be enforced.
    enforce_bitfield_size = True

    # Determines whether parsed enum literals have to be part of the enum.
    strong_enum_literals = True

    # When True, renders enum values as integers instead of strings.
    render_enums_as_integers = False

    # When True and `render_enums_as_integers == False`, renders enum literals as "EnumName.LiteralName"
    full_enum_names = True

    __snapshot_stack__ = []

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

    @classmethod
    def push(cls):
        """ Take a snapshot of HydraSettings and save it in the snapshot stack. """
        cls.__snapshot_stack__.append(cls.snapshot())

    @classmethod
    def pop(cls):
        """ Restores the settings of the latest snapshot. """
        cls.update(cls.__snapshot_stack__.pop())


class TypeFormatter(object):
    """ The base type for Hydra's formatters. """

    def __init__(self, default_value, validator=None, settings=None):
        """
        Creates a new formmater.

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

    def format(self, value, settings=None):
        """ When implemented in derived classes, returns the byte representation of the give value. """
        raise NotImplementedError()

    def parse(self, raw_data, settings=None):
        """ When implemented in derived classes, parses the raw data. """
        raise NotImplementedError()

    def validate(self, value):
        """
        Validate the given value using this formatters rules.

        :param value:   The value to format.
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

    def is_constant_size(self):
        """ Indicates wether this type formatter emits constant-sized buffers. """
        return True

    def validate_assignment(self, value):
        """ Validates a python value to make sure it is a sensible choice for this field. """
        pass

    def get_actual_length(self, value):
        """ When used on variable length formatters, returns the actual serialized length of the given python value. """
        return len(self)

    def __len__(self):
        """ Returns the length (byte size) of the formatter's type. """
        raise NotImplementedError()


class StructMeta(with_metaclass(Preparable, type)):
    def __new__(cls, name, bases, attributes):

        if not hasattr(cls, '_metadata') or cls._metadata['name'] != name:
            metadata = {
                'name': name,
                'length': 0,
                'members': tuple((k, v) for k, v in attributes.items() if issubclass(get_as_type(v), TypeFormatter))
            }

            # Ensure that only the last member can be a VLA
            for member_name, formatter in metadata['members'][:-1]:
                if not formatter.is_constant_size():
                    raise TypeError("Only the last member of a struct can be variable length.")

            # Initialize a copy of the data properties.
            metadata['length'] = sum(len(get_as_value(v)) for _, v in metadata['members'])

            setattr(cls, '_metadata', metadata)
        attributes.update({'_metadata': cls._metadata})
        return super(StructMeta, cls).__new__(cls, name, bases, attributes)

    def __len__(cls):
        return getattr(cls, '_metadata')['length']

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()


class StructBase(with_metaclass(StructMeta, object)):
    pass


class Struct(StructBase):
    """ A base class for the framework's structs. """

    settings = {}

    def __init__(self, **kwargs):
        """
        Creates a struct.

        :param kwargs:  May be used to set struct fields.
        """
        super(Struct, self).__init__()

        # Initialize a copy of the data properties.
        for var_name, var_formatter in self._metadata['members']:
            # Accept a non-default value through the keyword arguments.
            if var_name in kwargs:
                setattr(self, var_name, kwargs[var_name])
            else:
                setattr(self, var_name, copy.deepcopy(var_formatter.default_value))

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def extract_range(cls, fields, first=None, last=None, inclusive=True):
        import sys
        """
        Extract a range from a list of fields.

        :param fields:      A list of tuples (name, formatter)
        :param first:       [Optional] The start of the range.
        :param last:        [Optional] The end of the range.
        :param inclusive:   [Optional] Determines whether the range includes the last field.
        :return:            A slice of the input.
        """
        if first is None:
            start_index = 0
        else:
            if not isinstance(first, (str,)):
                raise ValueError('first must be a field name')

            try:
                start_index = indexof(lambda v: v[0] == first, fields)
            except ValueError:
                raise ValueError("Could not find `{}' in `{}'".format(first, cls.get_name()))

        if last is None:
            end_index = len(fields) - 1
        else:
            if not isinstance(last, (str,)):
                raise ValueError('last must be a field name')

            try:
                end_index = indexof(lambda v: v[0] == last, fields)
            except ValueError:
                raise ValueError("Could not find `{}' in `{}'".format(last, cls.get_name()))

        if start_index > end_index:
            raise ValueError('The starting index is greater than the ending index.')

        if inclusive:
            end_index += 1

        return fields[start_index:end_index]

    @classmethod
    def offsetof(cls, member):
        """ Calculate the offset of the given member in the struct. """
        return sum(len(v) for _, v in cls.extract_range(cls._metadata['members'], last=member, inclusive=False))

    def serialize(self, settings=None, start=None, end=None):
        """
        Serialize this struct into a byte string.

        :param settings:    [Optional] Serialization settings overrides.
        :param start:       [Optional] A reference to the first desired field to serialize.
        :param end:         [Optional] A reference to the last desired field to serialize.
        :return: A byte-string representing the struct.
        """
        settings = HydraSettings.resolve(self.settings, settings)

        if not settings['dry_run']:
            self.before_serialize()

        if settings['validate_on_serialize'] and not self.validate():
            raise ValueError("The serialized data is invalid.")

        if start is not None or end is not None:
            fields = type(self).extract_range(self._metadata['members'], start, end)
        else:
            fields = self._metadata['members']

        output = b''.join(formatter.format(vars(self)[name], settings) for name, formatter in fields)

        if not settings['dry_run']:
            self.after_serialize()

        return output

    @classmethod
    def deserialize(cls, raw_data, settings=None):
        """ Deserialize the given raw data into an object. """
        settings = HydraSettings.resolve(settings, cls.settings)

        raw_data = string2bytes(raw_data)

        # Create a new struct object and set its properties.
        class_object = cls()

        if len(raw_data) < len(class_object):
            raise ValueError('The supplied raw data is too short for a struct of type "%s"' % cls.get_name())

        for name, formatter in class_object._metadata['members']:
            if formatter.is_constant_size():
                data_piece = raw_data[:len(formatter)]
                raw_data = raw_data[len(formatter):]
            else:
                data_piece = raw_data
                raw_data = []

            vars(class_object)[name] = formatter.parse(data_piece, settings)

        if settings['validate'] and not class_object.validate():
            raise ValueError('The deserialized data is invalid.')

        return class_object

    ###################
    #      Hooks      #
    ###################
    def before_serialize(self):
        """ A hook called on a 'wet' run before serialization. """
        pass

    def after_serialize(self):
        """ A hook called on a 'wet' run after serialization. """
        pass

    def validate(self):
        """ Determine the validity of the object's data. """
        for formatter_name, formatter in self._metadata['members']:
            value = vars(self)[formatter_name]
            if not formatter.validate(value):
                raise ValueError('Field \'{}\' got an invalid value: {}.'.format(formatter_name, value))
        return True

    ###################
    #    Operators    #
    ###################

    def __len__(self):
        """ Get the length of the struct. """
        length = self._metadata['length']

        name, last_member = self._metadata['members'][-1]
        if not last_member.is_constant_size():
            length -= len(last_member)
            length += last_member.get_actual_length(vars(self)[name])

        return length

    def __eq__(self, other):
        """ Equates two objects. """
        if type(other) != type(self):
            raise TypeError('Cannot equate struct of differing types.')

        for name, formatter in self._metadata['members']:
            if not formatter.values_equal(vars(self)[name], vars(other)[name]):
                return False

        return True

    def __ne__(self, other):
        """ Negatively equates two objects. """
        return not (self == other)

    def __setattr__(self, key, value):
        """ A validation of struct members using the dot-notation. """
        if key == '_metadata' or key in vars(type(self)):
            formatter = vars(type(self))[key]
            formatter.validate_assignment(value)
            self.__dict__[key] = value
        else:
            raise KeyError('Assigned type is not part of the struct %s: %s' % (str(key), str(value)))

    def __repr__(self):
        """ Create a string representation of the struct's data. """
        def indent_text(text):
            lines = ['    ' + line for line in text.split('\n')]
            return '\n'.join(lines)

        output = ''
        for name, formatter in self._metadata['members']:
            field_string = formatter.render(vars(self)[name], name)
            output += '%s\n' % indent_text(field_string)

        output = output.strip('\n')
        return '%s {\n%s\n}' % (type(self).get_name(), indent_text(output))
    
    def __iter__(self):
        for key, _ in self._metadata['members']:
            value = getattr(self, key)
            if issubclass(type(value), Struct):
                yield key, dict(value)
            elif type(value) in (list, tuple):
                if len(value) == 0:
                    yield key, []
                elif issubclass(type(value[0]), Struct):
                    yield key, [dict(d) for d in value]
                else:
                    yield key, list(value)
            else:
                yield key, value
