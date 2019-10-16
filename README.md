# Hydras #
[![Build Status](https://travis-ci.org/Gilnaa/Hydras.svg?branch=master)](https://travis-ci.org/Gilnaa/Hydras)

'*Hydras*' is a python library that allows the developer to create structured binary data according to simple rules,
somewhat similar to how C does it with a struct.

Why "Hydras"? `Hydra` was taken.


## Example ##
```python
class Header(Struct):
  Opcode = uint8_t(4)       # The `opcode`'s default value will now be `4`
  DataLength = uint32_t()

class DataPacket(Struct):
  # A nested structure. "DataLength = 128" sets the default DataLength value for `Header`s inside `DataPacket`s
  Header = Header(DataLength=128)
  # Creates an array of bytes with a length of 128 bytes.
  Payload = Array(length = 128)

  # To override the constructor it must be able to override the default ctor (1 argument)
  def __init__(self, opcode=0):
    # Must call the base ctor
    super(DataPacket, self).__init__()
    self.Header.Opcode = opcode

if __name__ == '__main__':
  packet = DataPacket()
  # After you create the object, you can ignore the formatting rules, and assign the data directly to the properties.
  packet.Header.Opcode = DATAPACKET_OPCODE

  # You can transform the object into a byte string using the `serialize` method.
  data_to_send = packet.serialize() # => b'\x04\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00...'
  some_socket.send(data_to_send)

  packet.Payload = '\xFF' * 128
  data_to_send = packet.serialize() # => b'\x04\x80\x00\x00\x00\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF...'

  # . . .

  # You can parse raw byte strings into an object using the deserialize class method.
  received_data = some_socket.recv(len(packet))
  parsed_packet = DataPacket.deserialize(received_data)
```

You can find more examples in the examples directory.

## How does it work? ##
In the core of the library, there are two types of objects: `Serializer` and `Struct`.

`Serializer` is a formatting object, and can parse and format values of a specified type.
`Struct` is a structure object, which enables you to define rules for object serialization.

The developer can thus declare a class using the following notation:
```python
class <StructName>(Struct):
  <member_name> = <TypeClass>(<default_value>)
```
or
```python
class Message(Struct):
  TimeOfDay = uint64_t      # This creates a u64 formatter. Parentheses are optional.
  DataLength = uint8_t(128)   # A default value is optional

Message().serialize() #=> b'\x00\x00\x00\x00\x00\x00\x00\x00\x80'
```

The declared data members are in fact (due to python's syntax), static.
When a class object is created, the constructor (deep) copies each of the formatters' `default_value`s into an instance variable in the same name,
so some transparency is achieved by "tricking" the user into thinking no formatters are involved:
```
Class members:
  TimeOfDay:  uint64_t (default_value = 0)
  DataLength: uint8_t  (default_value = 128)
Object members:
  TimeOfDay:  0
  DataLength: 128
```

When the object is serialized, the object's data is cross-referenced with the class's formatters.
All of the integers are internally converted using python's `struct.pack` function.

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
