from .base import *
from .base import _create_array


class StructMetadata(object):
    name = None
    size = 0
    members: collections.OrderedDict = None
    is_constant_size = True


class StructMeta(type):
    HYDRAS_METAATTR = '__hydras_metadata'

    def __new__(mcs, name, bases, attributes):
        if not hasattr(mcs, mcs.HYDRAS_METAATTR):
            members = collections.OrderedDict()

            # Marks that a VST base has been detected and that no other base should
            # be considered valid afterwards.
            last_base = None
            # Likewise, the same handling is done for VST members
            last_member = None

            for base in bases:
                if not issubclass(type(base), StructMeta):
                    raise TypeError('Hydras structs can only derive other structs')

                if last_base is not None and len(base._hydras_members()) > 0:
                    raise TypeError('When deriving a variable-length struct, it must be last in the inheritance list')

                if not base.is_constant_size():
                    last_base = base

                for member_name, formatter in base._hydras_members().items():
                    if member_name in members:
                        raise TypeError('Name-clash detected')
                    members[member_name] = formatter

            for member_name, value in attributes.items():
                fmt = None
                if issubclass(type(value), Serializer):
                    fmt = value
                elif inspect.isclass(value) and issubclass(value, Serializer):
                    fmt = value()
                # We want to check if `value` is either a subclass of `Struct` or an instance of such type
                # but `Struct` is not a valid identifier at this point.
                elif issubclass(type(value), StructMeta) or issubclass(type(type(value)), StructMeta):
                    fmt = NestedStruct[value]()

                if fmt is not None:
                    if last_base is not None or last_member is not None:
                        raise TypeError('...')
                    elif member_name in members:
                        raise TypeError('Name-clash detected')

                    if not fmt.is_constant_size:
                        last_member = fmt
                    members[member_name] = fmt

            # Initialize a copy of the data properties.
            metadata = StructMetadata()
            metadata.name = name
            metadata.size = sum(m.byte_size for m in members.values())
            metadata.members = members
            metadata.is_constant_size = last_base is None and last_member is None

            attributes.update({mcs.HYDRAS_METAATTR: metadata})

        return super(StructMeta, mcs).__new__(mcs, name, bases, attributes)

    def __len__(cls):
        return getattr(cls, cls.HYDRAS_METAATTR).size

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()

    def __getitem__(cls, item_count):
        return _create_array(item_count, cls)


class Struct(metaclass=StructMeta):
    """ A base class for the framework's structs. """

    def __init__(self, **kwargs):
        """
        Creates a struct.

        :param kwargs:  May be used to set struct fields.
        """
        super(Struct, self).__init__()

        # Initialize a copy of the data properties.
        for var_name, var_formatter in self._hydras_members().items():
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
    def _hydras_members(cls) -> collections.OrderedDict:
        return cls._hydras_metadata().members

    @classmethod
    def is_constant_size(cls):
        return cls._hydras_metadata().is_constant_size

    def serialize(self, settings: Dict[str, Any] = None):
        """
        Serialize this struct into a byte string.

        :param settings:    [Optional] Serialization settings overrides.
        :return: A byte-string representing the struct.
        """
        settings = HydraSettings.resolve(settings)

        if not settings['dry_run']:
            self.before_serialize()

        output = b''.join(formatter.format(getattr(self, name), settings)
                          for name, formatter in self._hydras_members().items())

        if not settings['dry_run']:
            self.after_serialize()

        return output

    @classmethod
    def deserialize(cls, raw_data, settings=None):
        """ Deserialize the given raw data into an object. """
        settings = HydraSettings.resolve(settings)

        # Create a new struct object and set its properties.
        class_object = cls()

        if len(raw_data) < len(class_object):
            raise ValueError('The supplied raw data is too short for a struct of type "%s"' % cls.get_name())

        for name, serializer in cls._hydras_members().items():
            if serializer.is_constant_size:
                data_piece = raw_data[:serializer.byte_size]
                raw_data = raw_data[serializer.byte_size:]
            else:
                data_piece = raw_data
                raw_data = []

            setattr(class_object, name, serializer.parse(data_piece, settings))

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
        for formatter_name, formatter in self._hydras_members().items():
            value = getattr(self, formatter_name)
            if not formatter.validate(value):
                raise ValueError('Field \'{}\' got an invalid value: {}.'.format(formatter_name, value))
        return True

    ###################
    #    Operators    #
    ###################

    def __len__(self):
        """ Get the length of the struct. """
        length = self._hydras_metadata().size

        if not self.is_constant_size():
            name, last_member = next(reversed(self._hydras_members().items()))
            length -= last_member.byte_size
            length += last_member.get_actual_length(getattr(self, name))

        return length

    def __eq__(self, other):
        """ Equates two objects. """
        if type(other) != type(self):
            raise TypeError('Cannot equate struct of differing types.')

        for name, formatter in self._hydras_members().items():
            if not formatter.values_equal(getattr(self, name), getattr(other, name)):
                return False

        return True

    def __ne__(self, other):
        """ Negatively equates two objects. """
        return not (self == other)

    def __setattr__(self, key, value):
        """ A validation of struct members using the dot-notation. """
        if hasattr(self, key):
            formatter = self._hydras_members()[key]
            if not formatter.validate(value):
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
        for name, formatter in self._hydras_members().items():
            field_string = formatter.render(getattr(self, name), name)
            output += '%s\n' % indent_text(field_string)

        output = output.strip('\n')
        return '%s {\n%s\n}' % (type(self).get_name(), indent_text(output))

    def __iter__(self):
        """ Support conversion to dict """
        for key in self._hydras_members():
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


class NestedStructMetadata(SerializerMetadata):
    __slots__ = ('struct', )

    def __init__(self, struct):
        self.struct = struct
        super(NestedStructMetadata, self).__init__(len(struct))

    def is_constant_size(self) -> bool:
        return self.struct.is_constant_size()


class NestedStructMeta(SerializerMeta):
    def __getitem__(cls, struct_type_or_object):
        if not issubclass(get_as_type(struct_type_or_object), Struct):
            raise TypeError("struct_type_or_object should be either a Struct class or a Struct object.")

        return type(get_type_name(cls), (cls,), {
            SerializerMeta.METAATTR: NestedStructMetadata(get_as_value(struct_type_or_object))
        })


class NestedStruct(Serializer, metaclass=NestedStructMeta):
    """
    A serializer that wraps structs.
    This is an implementation detail and should not be directly used by the user.
    """

    @property
    def struct(self):
        return self.__hydras_metadata__.struct

    def __init__(self, *args, **kwargs):
        """
        Initialize this NestedStruct object.

        :param struct_type_or_object:   The type of the NestedStruct or Struct object.
        """

        super(NestedStruct, self).__init__(copy.deepcopy(self.struct), *args, **kwargs)

    def format(self, value, settings=None):
        return value.serialize(settings)

    def parse(self, raw_data, settings=None):
        return self.struct.deserialize(raw_data, settings)

    def validate(self, value):
        return isinstance(value, get_as_type(self.struct)) and value.validate()

    def validate(self, value) -> bool:
        return value.validate()

    def __len__(self):
        return len(self.default_value)

    def __repr__(self):
        return '<{} ({})>'.format(type(self).__name__, self.struct)
