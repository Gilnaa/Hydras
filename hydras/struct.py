from .base import *
from .utils import *

__all__ = ('Struct', 'NestedStruct', 'Mixin')


class EmptyFieldValueType:
    pass


EMPTY_FIELD = EmptyFieldValueType()


class StructMetadata(object):
    name = None
    size = 0
    members: collections.OrderedDict = None
    is_constant_size = True


class Mixin:
    def __init__(self, typ, prefix=''):
        self.typ = typ
        self.prefix = prefix


class StructMeta(type):
    HYDRAS_METAATTR = '_hydras_metadata'
    _hydras_metadata: StructMetadata

    def __new__(mcs, name, bases, attributes):
        if not hasattr(mcs, mcs.HYDRAS_METAATTR):
            members = collections.OrderedDict()

            # Marks that a VST base has been detected and that no other base should
            # be considered valid afterwards.
            last_base = None
            # Likewise, the same handling is done for VST members
            last_member = None

            hydras_bases = [b for b in bases if isinstance(b, StructMeta)]
            if len(hydras_bases) > 1:
                raise TypeError('Multiple inheritance of Hydras structs is prohibited.')

            for base in hydras_bases:
                if last_base is not None and len(base._hydras_metadata.members) > 0:
                    raise TypeError('When deriving a variable-length struct, it must be last in the inheritance list')

                if not base.is_constant_size():
                    last_base = base

                for member_name, formatter in base._hydras_metadata.members.items():
                    if member_name in members:
                        raise TypeError('Name-clash detected')
                    members[member_name] = formatter

            for member_name, value in attributes.items():
                fmt = ()
                if issubclass(type(value), Serializer):
                    fmt = [(member_name, value)]
                elif inspect.isclass(value) and issubclass(value, Serializer):
                    fmt = [(member_name, value())]
                # We want to check if `value` is either a subclass of `Struct` or an instance of such type
                # but `Struct` is not a valid identifier at this point.
                elif issubclass(type(value), StructMeta) or issubclass(type(type(value)), StructMeta):
                    fmt = [(member_name, NestedStruct[value]())]
                elif isinstance(value, Mixin):
                    typ = value.typ
                    fmt = [(value.prefix + _name, _fmt) for _name, _fmt in typ._hydras_metadata.members.items()]

                for _name, _fmt in fmt:
                    if last_base is not None or last_member is not None:
                        raise TypeError('...')
                    elif _name in members:
                        raise TypeError('Name-clash detected')

                    if not _fmt.is_constant_size:
                        last_member = _fmt
                    members[_name] = _fmt

            # Initialize a copy of the data properties.
            metadata = StructMetadata()
            metadata.name = name
            metadata.size = sum(m.byte_size for m in members.values())
            metadata.members = members
            metadata.is_constant_size = last_base is None and last_member is None

            attributes.update({
                mcs.HYDRAS_METAATTR: metadata,
            })

        return super(StructMeta, mcs).__new__(mcs, name, bases, attributes)

    def __len__(cls):
        return cls._hydras_metadata.size

    def __prepare__(cls, bases, **kwargs):
        return collections.OrderedDict()

    def __getitem__(cls, item_count):
        return create_array(item_count, NestedStruct[cls]())

    def __repr__(self):
        return f'{get_type_name(self)}'


class Struct(metaclass=StructMeta):
    """ A base class for the framework's structs. """
    _hydras_metadata: StructMetadata

    def __init__(self, initial_values: dict = None):
        """
        Creates a struct.

        :param kwargs:  May be used to set struct fields.
        """
        super(Struct, self).__init__()

        initial_values = initial_values or {}

        # Initialize a copy of the data properties.
        for var_name, var_formatter in self._hydras_metadata.members.items():
            # Accept a non-default value through the keyword arguments.
            if var_name in initial_values:
                setattr(self, var_name, initial_values[var_name])
            else:
                # Calling super's __setattr__ in order to avoid validation on empty value
                super().__setattr__(var_name, EMPTY_FIELD)

    @classmethod
    def _hydras_metadata(cls) -> StructMetadata:
        return getattr(cls, StructMeta.HYDRAS_METAATTR, None)

    @classmethod
    def _hydras_members(cls) -> collections.OrderedDict:
        return cls._hydras_metadata.members

    @classmethod
    def is_constant_size(cls):
        return cls._hydras_metadata.is_constant_size

    def serialize(self, settings: HydraSettings = None):
        """
        Serialize this struct into a byte string.

        :param settings:    [Optional] Serialization settings overrides.
        :return: A byte-string representing the struct.
        """
        output = bytearray(len(self))
        self.serialize_into(memoryview(output), 0, settings)
        return bytes(output)

    def serialize_into(self, storage: memoryview, offset: int, settings: HydraSettings = None):
        settings = settings or HydraSettings()

        if not settings.dry_run:
            self.before_serialize()

        for name, formatter in self._hydras_metadata.members.items():
            value = getattr(self, name)
            offset = formatter.serialize_into(storage, offset, value, settings)

        if not settings.dry_run:
            self.after_serialize()

        return offset

    @classmethod
    def deserialize(cls, raw_data, settings=None):
        """ Deserialize the given raw data into an object. """
        settings = HydraSettings.resolve(settings)

        # Create a new struct object and set its properties.
        class_object = cls()

        assert isinstance(raw_data, (bytes, bytearray, memoryview))
        if not isinstance(raw_data, memoryview):
            raw_data = memoryview(raw_data)

        if len(raw_data) < len(class_object):
            raise ValueError('The supplied raw data is too short for a struct of type "%s"' % get_type_name(cls))

        for name, serializer in cls._hydras_metadata.members.items():
            if serializer.is_constant_size:
                data_piece = raw_data[:serializer.byte_size]
                raw_data = raw_data[serializer.byte_size:]
            else:
                data_piece = raw_data
                raw_data = []

            try:
                value = serializer.deserialize(data_piece, settings)
            except Exception as e:
                raise ValidationError(data_piece, name, class_object, e)

            # Call base setattr in order to avoid validation
            super(Struct, class_object).__setattr__(name, value)

        if settings.validate:
            class_object.validate()

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
        for field_name, formatter in self._hydras_metadata.members.items():
            value = getattr(self, field_name)
            try:
                formatter.validate(value)
            except Exception as e:
                raise ValidationError(value, field_name, self, e)

    ###################
    #    Operators    #
    ###################

    def __len__(self):
        """ Get the length of the struct. """
        length = self._hydras_metadata.size

        if not self.is_constant_size():
            name, last_member = next(reversed(self._hydras_metadata.members.items()))
            length -= last_member.byte_size
            length += last_member.get_actual_length(getattr(self, name))

        return length

    def __bytes__(self):
        return self.serialize()

    def __eq__(self, other):
        """ Equates two objects. """
        if type(other) != type(self):
            raise TypeError('Cannot equate struct of differing types.')

        for name, formatter in self._hydras_metadata.members.items():
            if not formatter.values_equal(getattr(self, name), getattr(other, name)):
                return False

        return True

    def __ne__(self, other):
        """ Negatively equates two objects. """
        return not (self == other)

    def __setattr__(self, key, value):
        """ A validation of struct members using the dot-notation. """
        if HydraSettings.validate and key in self._hydras_metadata.members:
            self._hydras_metadata.members[key].validate(value)

        super(Struct, self).__setattr__(key, value)

    def __getattribute__(self, key):
        value = super().__getattribute__(key)
        if isinstance(value, EmptyFieldValueType):
            value = self._hydras_metadata.members[key].get_initial_value()
            setattr(self, key, value)
        return value

    def __iter__(self):
        """ Support conversion to dict """
        for key in self._hydras_metadata.members:
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
        return create_array(item_count, NestedStruct[self]())

    def __repr__(self):
        lines = (f"'{name}': {repr(getattr(self, name))}" for name in self._hydras_metadata.members)
        params = ', '.join(lines)
        return f'{get_type_name(self)}({{{params}}})'

    def render_lines(self, options: RenderOptions = None) -> List[str]:
        options = options or RenderOptions()
        lines = [
            f'{get_type_name(self)} {{'
        ]

        for name, serializer in self._hydras_metadata.members.items():
            lines.extend(options.indent + sub_line
                         for sub_line in serializer.render_lines(name,
                                                                 getattr(self, name),
                                                                 options))

        lines.append('}')
        return lines

    def render(self, options: RenderOptions = None) -> str:
        return '\n'.join(self.render_lines(options))

    def __str__(self):
        return self.render()


class NestedStructMetadata(SerializerMetadata):
    __slots__ = ('struct', )

    def __init__(self, struct):
        self.struct = struct
        super(NestedStructMetadata, self).__init__(len(struct))

    def is_constant_size(self) -> bool:
        return self.struct.is_constant_size()


class NestedStructMeta(SerializerMeta):
    _hydras_metadata: NestedStructMetadata

    def __getitem__(cls, struct_type_or_object):
        if not issubclass(get_as_type(struct_type_or_object), Struct):
            raise TypeError("struct_type_or_object should be either a Struct class or a Struct object.")

        return type(get_type_name(cls), (cls,), {
            SerializerMeta.METAATTR: NestedStructMetadata(get_as_value(struct_type_or_object))
        })

    def __repr__(self):
        # This impl is not accurate and will result in invalid representations,
        # but this will most likely be used for debugging purposes.
        return f'NestedStruct[{get_type_name(self._hydras_metadata.struct)}]'


class NestedStruct(Serializer, metaclass=NestedStructMeta):
    """
    A serializer that wraps structs.
    This is an implementation detail and should not be directly used by the user.
    """

    __slots__ = ()
    _hydras_metadata: NestedStructMetadata

    @property
    def struct(self):
        return self._hydras_metadata.struct

    def __init__(self, *args, **kwargs):
        """
        Initialize this NestedStruct object.

        :param struct_type_or_object:   The type of the NestedStruct or Struct object.
        """

        super(NestedStruct, self).__init__(copy.deepcopy(self.struct), *args, **kwargs)

    def serialize(self, value, settings=None):
        return value.serialize(settings)

    def get_initial_value(self):
        return copy.deepcopy(self.struct)

    def serialize_into(self, storage: memoryview, offset: int, value, settings: HydraSettings = None) -> int:
        return value.serialize_into(storage, offset, settings)

    def deserialize(self, raw_data, settings=None):
        return self.struct.deserialize(raw_data, settings)

    def validate(self, value):
        value.validate()

    def render_lines(self, name: str, value: Struct, options: RenderOptions = None) -> List[str]:
        lines = value.render_lines(options)
        if name is not None:
            lines[0] = f'{name}: {lines[0]}'
        return lines

    def __len__(self):
        return len(self.default_value)

    def __repr__(self):
        # This impl is not accurate and will result in invalid representations,
        # but this will most likely be used for debugging purposes.
        return f'NestedStruct[{get_type_name(self._hydras_metadata.struct)}]()'
