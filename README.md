# Hydras

[![Build Status](https://travis-ci.org/Gilnaa/Hydras.svg?branch=master)](https://travis-ci.org/Gilnaa/Hydras)

'*Hydras*' is a python library that allows the developer to create structured binary data according to simple rules,
somewhat similar to how C does it with a struct.

Why "Hydras"? `Hydra` was taken.

Hydras versions up to (and including) `v2.*` supported both Python2 and Python3.
Newer version dropped Python2 support entirely.

## Roadmap

This a list of features we want to implement before releasing Hydras 3.0

* Add a bitfield-implementation
* Enum as bit-flags

Contributions are welcome.

## Example

The 'examples' directory is old, not informative, and in pretty bad shape, but the CI does make sure
that the code there is working.

Instead, here's 

```python
from hydras import *


class Opcodes(Enum, underlying_type=u8):
    KEEP_ALIVE = 3
    DATA = 15

class Header(Struct):
    opcode = Opcodes
    data_length = u32

class DataPacket(Struct):
    # A nested structure. "data_length = 128" sets the default DataLength value for `Header`s inside `DataPacket`s
    header = Header(dict(opcode=Opcodes.DATA, 
                         data_length=128))

    # Creates an array of bytes with a length of 128 bytes.
    payload = u8[128]

    # You can override the constructor, but you must keep an "overload" that receives no arguments.
    # Even without this being defined, the class could have been used the same: `DataPacket(payload=...)`
    # This constructor also sets the `data_length` property
    def __init__(self, initial_values: dict = None):
        # Must call the base ctor in order to initialize the data members
        super(DataPacket, self).__init__(initial_values)
        
        if 'payload' in initial_values:
            self.header.data_length = len(payload)

if __name__ == '__main__':
    packet = DataPacket()

    # You can transform the object into a byte string using the `serialize` method.
    zeroes = packet.serialize()  # => b'\x0f\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    # Alternatively,
    zeroes = bytes(packet)

    # You can also modify the object naturally.
    packet.payload = bytes(range(128))
    saw_tooth = packet.serialize()  # => b'\x0f\x80\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f'

    # . . .

    # You can parse raw byte strings into an object using the deserialize class method.
    received_data = some_socket.recv(len(packet))
    parsed_packet = DataPacket.deserialize(received_data)
```

You can find more examples in the examples directory.

## How does it work?

In the core of the library, there are two types of objects: `Serializer` and `Struct`.

`Serializer` is an object that can convert between common python objects (e.g. `int` and `float`) and to and from `bytes`.
`Serializer`s are mostly supplied by the library, but can also be written by the user.

A simple example of a `Serializer` is `u8`; a more complex example is `EnumClass` which requires more user involvement.

`Struct` is an aggregate of named members, where each has a concrete type associated with it (which is either a `Serializer` or another `Struct`).

`Struct`s are always defined by the user.

The developer can thus declare a struct using the following notation:

```python
class <StructName>(Struct):
    <member_name> = <StructType|SerializerType>(<default_value>)
```

For example:

```python
class Message(Struct):
  TimeOfDay = u64          # This creates a u64 formatter. Parentheses are optional.
  DataLength = u8(128)     # A default value is optional

Message().serialize() #=> b'\x00\x00\x00\x00\x00\x00\x00\x00\x80'
```

## Types

### Primitive Types

"Primitive" types are integers and floating-point numbers, and are named similarly to Rust's primitive types.

Integers come in signed and unsigned variants with bitsizes of 8, 16, 32, 64: `u8, i8, u16, etc...`

Floating point are named `f32` and `f64`.

When serializing, the endianness of a primitive is set to that of the "target" arch (as configured by the user); 
the user can instead specify field-specific endianness by using the `_be` or `_le` variants (e.g. `u32_be`).

### Enums

Enums are closed sets of named values. By default they are serialized as if their underlying type is `u32` 

```python
from hydras import *


class MyEnum(Enum):
    a = 1
    b = auto()
    c = 10
    d = auto()

class SmallerEnum(Enum, underlying_type=u8):
    a = 1
    b = auto()
    c = 10
    d = auto()

class MyStruct(Struct):
    e = MyEnum
    se = SmallerEnum(SmallerEnum.c)

if __name__ == '__main__':
    print(MyStruct().serialize())  # => b'\x01\x00\x00\x00\x0C'
```

### Arrays

An array can be created by appending a `[size]` or `[min_size:max_size]` to another type.
The type of a `serializer[size]` expression is itself a serializer type.

The python-value of an array can be either `list` or a `tuple`; if the value is shorter than
that of the array, it will be padded with zeroes on serialization.

When the type of the array is u8, the python value can also be `bytes` and `bytearray`. 

For example:

```python
from hydras import *
class Foo(Struct):
    # Fixed length-arrays
    byte_array = u8[32]
    array_with_uniform_default_value = u16(57)[4]
    array_with_nonuniform_default_value = u16[4]([1, 2, 3, 4])


if __name__ == '__main__':
    f = Foo()
    f.byte_array = b'123'  # This will be padded with zeroes
```

If the default value of the array is a `bytes` or `bytearray` object, Hydras will deserialize to that type.

```python
from hydras import *
class Bar(Struct):
    byte_array = u8[4](default_value=bytearray())


if __name__ == '__main__':
    print(Bar.deserialize(b'\x00\x11\x22\x33').byte_array)
    # => bytearray(b'\x00\x11\x22\x33')
```

Variable-length arrays can be created by giving a slice as the size of the array.

```python
# Variable-length array with at least 5 members
u8[5:]
# Variable-length array with up to 5 members (inclusive)
u8[:5]
# Variable-length array with between 6 and 8 members
u8[6:8]
# Unbound array
u8[:]
```

Variable-length arrays, being VSTs (read more below), must be placed last in a struct.
When deserializing, the tail of the buffer will be given to the array to parse. 
The tail must match the VLA's size specification or an error will be raised.

### Variable-length types

Variable-length types (VST) can only be placed as the last member of a struct. 

The most basic variable-length type is a VLA (Variable-length array; seen above).
A struct whose last member is a VST is also a VST.

### Mixins ###
With `Mixin`s, you can copy one struct's fields into another, losing the first structs identity.
You can also prefix the the implanted fields' names with a constant string.
```python
class Aggregate(Struct):
    version = u8

class Struct1(Struct):
    magic = u32
    _ag = Mixin(Aggregate)

class Struct2(Struct):
    magic = u32
    version = u16
    _ag = Mixin(Aggregate, prefix='agg_')

assert list(Struct1._hydras_members()) == ['magic', 'version']
assert list(Struct2._hydras_members()) == ['magic', 'version', 'agg_version']
``` 

## Endianness

Integral fields not suffixed with `_be` or `_le` will take the endianness of the "target".
The target endian by default is the same as that of the host machine, but can be configured by modifying `HydraSettings`
or by specifying serialization-time settings.

## Validators

A validator object can be assigned to a struct data member to define validation rules.
When deserializing an object from binary data, the framework will validate the values
using the user-defined validation-rules.

If an invalid value is encountered, a ValueError is raised.

```python
class MeIsValidated(Struct):
    member = i8(0, validator=RangeValidator(-15, 15))

...

MeIsValidated.deserialize('\x10')  # => ValueError: The deserialized data is invalid.
```

There are a few built-in validators defined for the following rules:

- RangeValidator: Range check
- ExactValueValidator: Exact value check
- BitSizeValidator: Bit-Length check
- CustomValidator: Lambda validation (receives a user function.)
- TrueValidator & FalseValidator: Dummy validators (always true / always false)

More validators can be defined by subclassing the Validator class.

### Lambda Validators

The user can use a lambda expression (or any function) instead of a validator object as validation rule.

```python
class MeIsLambda(Struct):
    member = i8(0, validator=lambda value: value % 3 == 0)
```

Note that the default value must pass the validation, otherwise the construction will fail.

## Hooks

A `Struct` derived class can implement hooks.

### before_serialize

This method will be called before a serialization is about to occur.

**Note**: This method will not be called if either `HydraSettings.dry_run` is True,
or `serialize` is called with `dry_run=True`

### after_serialize

This method will be called after a serialization has occurd.

**Note**: This method will not be called if either `HydraSettings.dry_run` is True,
or `serialize` is called with `dry_run=True`

### validate

Called after a de-serialization is completed.
If it returns a `False`y value, the `deserialize` raises an error.

If not overriden by the user in a custom Struct class, the method
will validate using the type formatters' validators.

The user can, of course, override the method to add custom validations,
and then invoke the original validate method.

**Note**: No errors will be raised if `HydraSettings.validate` is set to `False`.
