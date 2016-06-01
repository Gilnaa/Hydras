# Hydra #

`Hydra` is python framework that aims to simplify construction of complicated binary data.

## Usage ##

Example usage:
```python
from hydra import *

MAX_SIZE = 128

class Header(Struct):
    opcode = Enum('Invalid', {'Invalid': 0, 'Data': 1})
    payload_length = uint32_t(0)

class DataMessage(Struct):
    header = NestedStruct(Header(opcode = 'Data'))
    payload = Array(MAX_SIZE)


msg = DataMessage()
msg.payload = 'Hello Hydra!'
msg.header.payload_length = len(msg.payload)

# Struct serialization
data = msg.serialize() # => '\x01\x00\x00\x00\x0c\x00\x00\x00Hello Hydra!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 . . .'

another_message = DataMessage.deserialize(data)

print(another_message == msg)
```

## Available types ##
 - Scalars:
    - Unsigned: `UInt8`, `UInt16`, `UInt32`, `UInt64`
    - Signed: `Int8`, `Int16`, `Int32`, `Int64`
    - Floating point: `Float`, `Double`
    - `Enum`
 - Complex:
    - `Array` (of either a scalar type or of a struct)
    - `NestedStruct`

A set of aliases is supplied to the scalar set, that looks a bit more like the `stdint.h` types. (`uint8_t`, etc.)

## Hooks ##
Two serialization hooks are called by the framework on a struct upon serialization:
 - `before_serialize`: Called before serialization. Can be used to prepare the object.
 - `after_serialize`: Called after a struct serialization.

By default, these hooks do nothing, but a developer sub-classing `Struct` can override them.
The call to these function can be disabled by settings `HydraSettings.dry_run` to `True`.

Example:
```python
class Header(Struct):
    opcode = Enum('Invalid', {'Invalid': 0, 'Data': 1})
    payload_length = uint32_t(0)

class DataMessage(Struct):
    header = NestedStruct(Header(opcode = 'Data'))
    payload = Array(MAX_SIZE)

    def before_serialize(self):
        self.header.payload_length = len(self.payload)
```

## Validation ##
Validation rules can be added to struct fields to define a "valid state".

This state is checked upon deserialization, and an exception is raised if the data is invalid.

This feature can be turned off by settings `HydraSettings.validate` to `False`.

An optional validation can also be checked during serialize time by setting `HydraSettings.validate_on_serialize` to `True`.

Example:
```python
class Header(Struct):
    opcode = Enum('Invalid', {'Invalid': 0, 'Data': 1})
    payload_length = uint32_t(0, validator=RangeValidator(0, MAX_SIZE))

class DataMessage(Struct):
    header = NestedStruct(Header(opcode = 'Data'))
    payload = Array(MAX_SIZE)

    def before_serialize(self):
        self.header.payload_length = len(self.payload)

```

## Endian ##
The endian-ness of fields or structs can be set and changed and overrided at multiple points.

```python
class Header(Struct):
    opcode = Enum('Invalid', {'Invalid': 0, 'Data': 1})
    payload_length = uint32_t(0, validator=RangeValidator(0, MAX_SIZE), endian=BigEndian)

class DataMessage(Struct):
    header = NestedStruct(Header(opcode = 'Data'))
    payload = Array(MAX_SIZE)

    def before_serialize(self):
        self.header.payload_length = len(self.payload)


DataMessage().serialize() # The payload_length field is now in big endian.
DataMessage().serialize(settings = {'endian': LittleEndian})  # The field is now forced to be little endian.

HydraSettings.endian = BigEndian
DataMessage().serialize() # Everyting is in big endian.
```