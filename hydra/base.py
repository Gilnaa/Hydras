"""
Contains the core classes of the framework.

:file: base.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
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
        """ Resolve settings dicionaries. """
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

        self.id = get_id()
        self.validator = validator
        self.default_value = default_value
        self.settings = settings or {}

    def resolve_settings(self, overrides=None):
        """ Resolves the flat settings for a single action on this formatter. """
        return HydraSettings.resolve(self.settings, overrides)

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

            if callable(self.validator):
                return self.validator(value)

        return True

    def values_equal(self, a, b):
        """ Determines whether the given two values are equal. """
        return a == b

    def render(self, value, name):
        """ Returns a displayable string for the given value. """
        return '%s: %s' % (name, value)

    def __len__(self):
        """ Returns the length (byte size) of the formatter's type. """
        raise NotImplementedError()


class Struct(object):
    """ A base class for the framework's structs. """

    settings = {}

    def __init__(self, **kwargs):
        """
        Creates a struct.

        :param kwargs:  May be used to set struct fields.
        """
        self._metadata = {'id': get_id(),
                          'length': 0,
                          'data_members': collections.OrderedDict(type(self).get_struct_fields())}

        # Initialize a copy of the data properties.
        for var_name, var_formatter in self._metadata['data_members'].items():
            self._metadata['length'] += len(var_formatter)

            # Accept a non-default value through the keyword arguments.
            if var_name in kwargs:
                setattr(self, var_name, kwargs[var_name])
            else:
                setattr(self, var_name, copy.deepcopy(var_formatter.default_value))

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

        fields = list(self._metadata['data_members'].items())
        if start is not None or end is not None:
            fields = Struct.extract_range(fields, start, end)

        output = b''
        for name, formatter in fields:
            output += formatter.format(vars(self)[name], settings)

        if not settings['dry_run']:
            self.after_serialize()

        return output

    @classmethod
    def extract_range(cls, fields, first=None, last=None, inclusive=True):
        """
        Extract a range from a list of fields.

        :param fields:      A list of tuples (name, formatter)
        :param first:       [Optional] The start of the range.
        :param last:        [Optional] The end of the range.
        :param inclusive:   [Optional] Determines whether the range includes the last field.
        :return:            A slice of the input.
        """
        start_index = 0
        end_index = len(fields) - 1

        if first is not None:
            matching = [(key, value) for key, value in fields if value.id == first.id]
            if len(matching) == 0:
                raise ValueError('Could not find the starting field.')

            start_index = fields.index(matching[0])

        if last is not None:
            matching = [(key, value) for key, value in fields if value.id == last.id]
            if len(matching) == 0:
                raise ValueError('Could not find the end field.')

            end_index = fields.index(matching[0])

        if start_index > end_index:
            raise ValueError('The starting index is greater than the ending index.')

        if inclusive:
            end_index += 1

        return fields[start_index : end_index]

    @classmethod
    def offsetof(cls, member):
        """ Calculate the offset of the given member in the struct. """
        fields = cls.extract_range(cls.get_struct_fields(), last=member, inclusive=False)

        return sum([len(value) for key, value in fields])

    @classmethod
    def get_struct_fields(cls):
        """ Return an ordered list of tuples, containing the struct members and their names."""
        fields = vars(cls).items()
        fields = list(filter(lambda var: isinstance(var[1], TypeFormatter), fields))
        fields.sort(key=lambda var: var[1].id)

        return fields

    @classmethod
    def get_struct_name(cls):
        return cls.__name__

    @classmethod
    def deserialize(cls, raw_data, settings=None):
        """ Deserialize the given raw data into an object. """
        settings = HydraSettings.resolve(cls.settings, settings)

        raw_data = string2bytes(raw_data)

        # Create a new struct object and set its properties.
        class_object = cls()

        if len(raw_data) < len(class_object):
            raise ValueError('The supplied raw data is too short for a struct of type "%s"' % cls.get_struct_name())

        for name, formatter in class_object._metadata['data_members'].items():
            data_piece = raw_data[:len(formatter)]
            vars(class_object)[name] = formatter.parse(data_piece, settings)
            raw_data = raw_data[len(formatter):]

        if settings['validate'] and not class_object.validate():
            raise ValueError('The deserialized data is invalid.')

        return class_object

    def before_serialize(self):
        """ A hook called on a 'wet' run before serialization. """
        pass

    def after_serialize(self):
        """ A hook called on a 'wet' run after serialization. """
        pass

    def validate(self):
        """ Determine the validity of the object's data. """
        for formatter_name, formatter in self._metadata['data_members'].items():
            value = vars(self)[formatter_name]
            if not formatter.validate(value):
                return False
        return True

    def __len__(self):
        """ Get the length of the struct. """
        return self._metadata['length']

    def __eq__(self, other):
        """ Equates two objects. """
        if type(other) != type(self):
            raise TypeError('Cannot equate struct of differing types.')

        for name, formatter in self._metadata['data_members'].items():
            if not formatter.values_equal(vars(self)[name], vars(other)[name]):
                return False

        return True

    def __ne__(self, other):
        """ Negatively equates two objects. """
        return not (self == other)

    def __setattr__(self, key, value):
        """ A validation of struct members using the dot-notation. """
        if key == '_metadata' or key in vars(type(self)):
            self.__dict__[key] = value
        else:
            raise KeyError('Assigned type is not part of the struct %s: %s' % (str(key), str(value)))

    def __repr__(self):
        """ Create a string representation of the struct's data. """
        def indent_text(text):
            lines = ['    ' + line for line in text.split('\n')]
            return '\n'.join(lines)

        fields = self.get_struct_fields()
        output = ''
        for name, formatter in fields:
            field_string = formatter.render(vars(self)[name], name)
            field_string = indent_text(field_string)
            output += '%s\n' % field_string

        return '{\n%s\n}' % indent_text(output)
