"""
Contains the core classes of the framework.

:file: base.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

import copy
import collections
from typing import Any, Dict, Type, Union as TypeUnion

from .utils import *
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
    from .vectors import Array, VariableArray

    assert isinstance(size, (int, slice)), 'Expected an int or a slice for array size'

    if isinstance(size, int):
        return Array(size, underlying_type)
    elif isinstance(size, slice):
        assert size.step is None, 'Cannot supply step as array size'
        return VariableArray(size.start, size.stop, underlying_type)


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

    def is_constant_size(self):
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


class StructMetadata(object):
    name = None
    size = 0
    members = ()


class StructMeta(type):
    HYDRAS_METAATTR = '__hydras_metadata'

    def __new__(cls, name, bases, attributes):
        if not hasattr(cls, cls.HYDRAS_METAATTR):
            members = []
            for member_name, fmt in attributes.items():
                if issubclass(type(fmt), Serializer):
                    members.append((member_name, fmt))
                elif inspect.isclass(fmt) and issubclass(fmt, Serializer):
                    members.append((member_name, fmt()))
                    attributes[member_name] = fmt()
                # We want to check if `fmt` is either a subclass of `Struct` or an instance of such type
                # but `Struct` is not a valid identifier at this point.
                elif issubclass(type(fmt), StructMeta) or issubclass(type(type(fmt)), StructMeta):
                    members.append((member_name, NestedStruct(fmt)))
                    attributes[member_name] = NestedStruct(fmt)

            inherited_members = []
            inherits_vla = False

            for base in bases:
                if not issubclass(type(base), StructMeta):
                    raise TypeError('Hydras structs can only derive other structs')

                if not base._hydras_is_constant_size():
                    if len(members) > 0:
                        raise TypeError('Cannot declare fields when deriving a variable-length struct.')
                    if inherits_vla:
                        raise TypeError('Cannot derive more than one variable-length Struct')
                    inherits_vla = True
                elif inherits_vla:
                    raise TypeError('When deriving a variable-length struct, it must be last in the inheritance list')

                inherited_members.extend(base._hydras_members())

            members = tuple(inherited_members + members)

            # Ensure that only the last member can be a VLA
            for member_name, field in members[:-1]:
                if not field.is_constant_size():
                    raise TypeError("Only the last member of a struct can be variable length.")

            # Initialize a copy of the data properties.
            metadata = StructMetadata()
            metadata.name = name
            metadata.size = sum(len(v) for _, v in members)
            metadata.members = members

            attributes.update({cls.HYDRAS_METAATTR: metadata})

        return super(StructMeta, cls).__new__(cls, name, bases, attributes)

    def __len__(cls):
        return getattr(cls, cls.HYDRAS_METAATTR).size

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()

    def __getitem__(self, item_count):
        return _create_array(item_count, self)


class Struct(metaclass=StructMeta):
    """ A base class for the framework's structs. """

    def __init__(self, **kwargs):
        """
        Creates a struct.

        :param kwargs:  May be used to set struct fields.
        """
        super(Struct, self).__init__()

        # Initialize a copy of the data properties.
        for var_name, var_formatter in self._hydras_members():
            # Accept a non-default value through the keyword arguments.
            if var_name in kwargs:
                setattr(self, var_name, kwargs[var_name])
            else:
                setattr(self, var_name, copy.deepcopy(var_formatter.default_value))

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def _hydras_metadata(cls) -> StructMetadata:
        return getattr(cls, StructMeta.HYDRAS_METAATTR, None)

    @classmethod
    def _hydras_members(cls):
        return cls._hydras_metadata().members

    @classmethod
    def _hydras_is_constant_size(cls):
        if len(cls._hydras_members()) == 0:
            return True
        _, serializer = cls._hydras_members()[-1]
        return serializer.is_constant_size()

    def serialize(self, settings: Dict[str, Any] = None):
        """
        Serialize this struct into a byte string.

        :param settings:    [Optional] Serialization settings overrides.
        :param start:       [Optional] A reference to the first desired field to serialize.
        :param end:         [Optional] A reference to the last desired field to serialize.
        :return: A byte-string representing the struct.
        """
        settings = HydraSettings.resolve(settings)

        if not settings['dry_run']:
            self.before_serialize()

        output = b''.join(formatter.format(getattr(self, name), settings)
                          for name, formatter in self._hydras_members())

        if not settings['dry_run']:
            self.after_serialize()

        return output

    @classmethod
    def deserialize(cls, raw_data, settings=None):
        """ Deserialize the given raw data into an object. """
        settings = HydraSettings.resolve(settings)

        raw_data = string2bytes(raw_data)

        # Create a new struct object and set its properties.
        class_object = cls()

        if len(raw_data) < len(class_object):
            raise ValueError('The supplied raw data is too short for a struct of type "%s"' % cls.get_name())

        for name, formatter in cls._hydras_members():
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
        for formatter_name, formatter in self._hydras_members():
            value = vars(self)[formatter_name]
            if not formatter.validate(value):
                raise ValueError('Field \'{}\' got an invalid value: {}.'.format(formatter_name, value))
        return True

    ###################
    #    Operators    #
    ###################

    def __len__(self):
        """ Get the length of the struct. """
        length = self._hydras_metadata().size

        if not self._hydras_is_constant_size():
            name, last_member = self._hydras_members()[-1]
            length -= len(last_member)
            length += last_member.get_actual_length(vars(self)[name])

        return length

    def __eq__(self, other):
        """ Equates two objects. """
        if type(other) != type(self):
            raise TypeError('Cannot equate struct of differing types.')

        for name, formatter in self._hydras_members():
            if not formatter.values_equal(vars(self)[name], vars(other)[name]):
                return False

        return True

    def __ne__(self, other):
        """ Negatively equates two objects. """
        return not (self == other)

    def __setattr__(self, key, value):
        """ A validation of struct members using the dot-notation. """
        if hasattr(self, key):
            formatter = getattr(type(self), key)
            if not formatter.validate_assignment(value):
                raise ValueError(f'Invalid value assigned to field "{key}"')
            self.__dict__[key] = value
        else:
            raise KeyError('Assigned type is not part of the struct %s: %s' % (str(key), str(value)))

    def __repr__(self):
        """ Create a string representation of the struct's data. """
        def indent_text(text):
            lines = ['    ' + line for line in text.split('\n')]
            return '\n'.join(lines)

        output = ''
        for name, formatter in self._hydras_members():
            field_string = formatter.render(vars(self)[name], name)
            output += '%s\n' % indent_text(field_string)

        output = output.strip('\n')
        return '%s {\n%s\n}' % (type(self).get_name(), indent_text(output))

    def __iter__(self):
        """ Support conversion to dict """
        for key, _ in self._hydras_members():
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

    def __getitem__(self, item_count):
        """
        This hack enables the familiar array syntax: `type()[count]`.
        For example, a 3-item array of type uint16_t might look like `uint16_t(default_value=5)[3]`.
        """
        return _create_array(item_count, self)


class NestedStruct(Serializer):
    """
    A serializer that wraps structs.
    This is an implementation detail and should not be directly used by the user.
    """

    def __init__(self, struct_type_or_object, *args, **kwargs):
        """
        Initialize this NestedStruct object.

        :param struct_type_or_object:   The type of the NestedStruct or Struct object.
        """
        default_value = None
        if issubclass(get_as_type(struct_type_or_object), Struct):
            self.nested_object_type = get_as_type(struct_type_or_object)
            default_value = get_as_value(struct_type_or_object)
        else:
            raise TypeError("struct_type_or_object should be either a Struct class or a Struct object.")

        super(NestedStruct, self).__init__(default_value, *args, **kwargs)

    def format(self, value, settings=None):
        return value.serialize(settings)

    def parse(self, raw_data, settings=None):
        return self.nested_object_type.deserialize(raw_data, settings)

    def validate_assignment(self, value):
        return True

    def validate(self, value) -> bool:
        return value.validate()

    def __len__(self):
        return len(self.default_value)

    def __repr__(self):
        return '<{} ({})>'.format(type(self).__name__, self.nested_object_type)
