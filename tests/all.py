#!/usr/bin/env python
"""
Runs all the tests of this library.

:file: all.py
:date: 30/08/2015
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

import unittest
from ScalarsTests import *
from StructTests import *
from VectorTests import *
from EnumTests import *
from BitFieldTests import *
from ValidationTests import *
from Python3Tests import *
from OffsetTests import *
from VLATests import *

if __name__ == '__main__':
    unittest.main()
