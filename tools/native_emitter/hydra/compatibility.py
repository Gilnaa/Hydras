"""
Contains patches that enbale the framework to work in both python2 and python3.

:file: compatability.py
:date: 05/02/2016
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

import sys
import platform
import inspect
from collections import OrderedDict
from functools import wraps

is_py3 = sys.version_info.major >= 3

if is_py3:
    xrange = range

if not is_py3:
    int_types = (int, long)
else:
    int_types = (int,)

def with_metaclass(meta, *bases):
    class metaclass(meta):
        def __new__(cls, name, _, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temp_class', (), {})


class Preparable(type):
    if not is_py3:
        if platform.python_implementation().lower() not in ('cpython', 'pypy'):
            raise RuntimeError(
                'The following hack was not tested for your interpreter')

        def __new__(cls, name, bases, attributes):
            try:
                constructor = attributes['__new__']
            except KeyError:
                return type.__new__(cls, name, bases, attributes)

            def preparing_ctor(cls, name, bases, attributes):
                try:
                    cls.__prepare__
                except AttributeError:
                    return constructor(cls, name, bases, attributes)
                namespace = cls.__prepare__.im_func(name, bases)
                defining_frame = sys._getframe(1)
                for constant in reversed(defining_frame.f_code.co_consts):
                    if inspect.iscode(constant) and constant.co_name == name:
                        def get_index(attrname, _names=constant.co_names):
                            try:
                                return _names.index(attrname)
                            except ValueError:
                                return 0
                        namespace.update(sorted(
                            attributes.items(),
                            key=lambda i: get_index(i[0]))
                        )
                        break
                return constructor(cls, name, bases, namespace)
            attributes['__new__'] = wraps(constructor)(preparing_ctor)
            return type.__new__(cls, name, bases, attributes)
