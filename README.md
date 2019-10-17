# Hydras #
[![Build Status](https://travis-ci.org/Gilnaa/Hydras.svg?branch=master)](https://travis-ci.org/Gilnaa/Hydras)

'*Hydras*' is a python library that allows the developer to create structured binary data according to simple rules,
somewhat similar to how C does it with a struct.

Why "Hydras"? `Hydra` was taken.

Hydras versions up to (and including) `v2.*` supported both Python2 and Python3.
Newer version dropped Python2 support entirely.

## Example ##
```python
from hydras import *


class Opcodes(EnumClass):
    KeepAlive = 3
    Data = 15

class Header(Struct):
    opcode = Opcodes(type_formatter=u8)
    data_length = u32

class DataPacket(Struct):
    # A nested structure. "DataLength = 128" sets the default DataLength value for `Header`s inside `DataPacket`s
    header = Header(opcode=Opcodes.Data, data_length=128)

    # Creates an array of bytes with a length of 128 bytes.
    payload = u8[128]

    # You can override the constructor, but you must keep an "overload" that receives no arguments.
    # Even without this being defined, the class could have been used the same: `DataPacket(payload=...)`
    # This constructor also sets the `data_length` property
    def __init__(self, payload=None, *args, **kwargs):
        # Must call the base ctor in order to initialize the data members
        super(DataPacket, self).__init__(*args, **kwargs)
        if payload is not None:
            self.payload = payload
            self.header.data_length = len(payload)

if __name__ == '__main__':
    packet = DataPacket()
    
    # You can transform the object into a byte string using the `serialize` method.
    zeroes = packet.serialize()  # => b'\x0f\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    
    # You can also modify the object naturally.
    packet.payload = bytes(range(128))
    saw_tooth = packet.serialize()  # => b'\x0f\x80\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f'

    # . . .

    # You can parse raw byte strings into an object using the deserialize class method.
    received_data = some_socket.recv(len(packet))
    parsed_packet = DataPacket.deserialize(received_data)
```

You can find more examples in the examples directory.

## How does it work? ##
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

## Validators ##
A validator object can be assigned to a struct data member to define validation rules.
When deserializing an object from binary data, the framework will validate the values
using the user-defined validation-rules.

If an invalid value is encountered, a ValueError is raised.

```python
class MeIsValidated(Struct):
    member = int8_t(0, validator=RangeValidator(-15, 15))

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

### Lambda Validators ###
The user can use a lambda expression (or any function) instead of a validator object as validation rule.

```python
class MeIsLambda(Struct):
    member = int8_t(0, validator=lambda value: value % 3 == 0)
```

## Hooks ##
A `Struct` derived class can implement hooks.
### before_serialize ###
This method will be called before a serialization is about to occur.

**Note**: This method will not be called if either `HydraSettings.dry_run` is True,
or `serialize` is called with `dry_run=True`

### after_serialize ###
This method will be called after a serialization has occurd.

**Note**: This method will not be called if either `HydraSettings.dry_run` is True,
or `serialize` is called with `dry_run=True`

### validate ###
Called after a de-serialization is completed.
If it returns a `False`y value, the `deserialize` raises an error.

If not overriden by the user in a custom Struct class, the method
will validate using the type formatters' validators.

The user can, of course, override the method to add custom validations,
and then invoke the original validate method.

**Note**: No errors will be raised if `HydraSettings.validate` is set to `False`.
