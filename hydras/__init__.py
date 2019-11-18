"""
A catch-all file that imports the whole framework.

:file: __init__.py
:date: 27/08/2015
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""

# Core classes.
from .base import *
from .struct import *

# Serializers
from .scalars import *
from .enum import *

# Misc.
from .validators import *
