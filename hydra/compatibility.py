"""
Contains patches that enable the framework to work in both python 2 and 3.

:file: compatibility.py
:date: 05/02/2016
:authors:
    - Gilad Naaman <gilad.doom@gmail.com>
"""

import sys

if sys.version_info[0] == 2:
    pass
elif sys.version_info[0] == 3:
    xrange = range