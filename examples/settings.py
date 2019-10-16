#!/usr/bin/env python
"""
This example shows how to use and change various serialization settings.
"""

from hydras import *


class ControlPacket(Struct):
    first_member = uint16_t(0xAABB)
    # You can control the endian settings of a single variable
    second_member = uint16_t(0xCCDD, endian=BigEndian)
    third_member = uint16_t(0xEEFF)


if __name__ == '__main__':
    ctrl = ControlPacket()
    # When serializing the struct, you can see that the `second_member` is big endian.
    # The endian of all the rest is NativeEndian, which is usually little.
    ctrl.serialize()  # => b'\xBB\xAA\xCC\xDD\xFF\xEE'

    # You can pass new defaults to the serialize method. It will override the struct settings and NativeSettings,
    # but not the variable settings.
    ctrl.serialize({'endian': BigEndian})  # => b'\xAA\xBB\xCC\xDD\xEE\xFF'

    # As said above, you cannot override the explicit settings of an individual.
    ctrl.serialize({'endian': LittleEndian})  # => b'\xBB\xAA\xCC\xDD\xFF\xEE'

    # You can also set global struct settings like this:
    #   class ControlPacket(Struct):
    #       settings = {'endian': BigEndian}
    #       first_member = ...
    #
    # If you use struct-wise settings like this, though, you cannot
    # have a struct member with this name. `settings` *is* a viable name
    # for a variable, but using it as such will prevent you from using struct-settings.

    # Settings priorities (lowest to highest):
    #   - `NativeSettings` values.
    #   - Struct settings
    #   - Serialization specific settings.
    #   - Variable specific settings.

    # Available settings, apart from `endian`:
    #   - `dry_run`:    Determines whether the de/serialization procedure will call the appropriate hooks.
    #   - `validate`:   Determines whether the `deserialize` method should call the `validate` hook.
