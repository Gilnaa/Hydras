#!/usr/bin/env python
"""
This example shows how to use and change various serialization settings.
"""

from hydras import *


class ControlPacket(Struct):
    first_member = u16(0xAABB)
    # You can control the endian settings of a single variable
    second_member = u16_be(0xCCDD)
    third_member = u16(0xEEFF)


if __name__ == '__main__':
    ctrl = ControlPacket()
    # When serializing the struct, you can see that the `second_member` is big endian.
    # The endian of all the rest is host-endian, which is usually little.
    ctrl.serialize()  # => b'\xBB\xAA\xCC\xDD\xFF\xEE'

    # You can pass new defaults to the serialize method. It will override the struct settings and HydraSettings,
    # but not the variable settings.
    ctrl.serialize(HydraSettings(target_endian=Endianness.BIG))  # => b'\xAA\xBB\xCC\xDD\xEE\xFF'

    # As said above, you cannot override the explicit settings of an individual.
    ctrl.serialize(HydraSettings(target_endian=Endianness.LITTLE))  # => b'\xBB\xAA\xCC\xDD\xFF\xEE'

    # Settings priorities (lowest to highest):
    #   - `HydraSettings` values.
    #   - Serialization specific settings.
    #   - Variable specific settings.
