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

Float = f32
Double = f64

VLA = VariableArray
