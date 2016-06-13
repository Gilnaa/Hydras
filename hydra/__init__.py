"""
A catch-all file that imports the whole framework.

:file: __init__.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
"""

# Core classes.
from .base import *

# Type formatters.
from .scalars import *
from .vectors import *
from .enums import *
from .enum_class import *
from .bitfield import *

# Misc.
from .validators import *

# Aliases
uint8_t = UInt8
uint16_t = UInt16
uint32_t = UInt32
uint64_t = UInt64

int8_t = Int8
int16_t = Int16
int32_t = Int32
int64_t = Int64
