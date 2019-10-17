"""
A catch-all file that imports the whole framework.

:file: __init__.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

# Core classes.
from .base import *

# Type formatters.
from .scalars import *
from .vectors import *
from .enum_class import *
from .bitfield import *
from .union import *

# Misc.
from .validators import *

# Aliases / shorthand
u8 = uint8_t
u16 = uint16_t
u32 = uint32_t
u64 = uint64_t
i8 = int8_t
i16 = int16_t
i32 = int32_t
i64 = int64_t

VLA = VariableArray
