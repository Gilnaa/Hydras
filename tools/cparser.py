#!/usr/bin/env python
"""
A utility parsing C/C++ files into Hydra definitions.

Requires the libclang python bindings.
Tested against version 3.8.

'clang` is not added to the dependencies because this tool is optional.

:file: cparser.py
:date: 09/06/2016
:authors:
    - Gilad Naaman <gilad.naaman@gmail.com>
"""

import sys
from clang.cindex import *
import collections

SIGNED_TYPES = [
    TypeKind.CHAR_S,
    TypeKind.SHORT,
    TypeKind.INT,
    TypeKind.LONG,
    TypeKind.LONGLONG
]

UNSIGNED_TYPES = [
    TypeKind.UCHAR,
    TypeKind.USHORT,
    TypeKind.UINT,
    TypeKind.ULONG,
    TypeKind.ULONGLONG
]

HYDRA_FLOAT = 'Float'
HYDRA_DOUBLE = 'Double'
UNSIGNED_HYDRA_TYPES = {
    8: 'UInt8',
    16: 'UInt16',
    32: 'UInt32',
    64: 'UInt64'
}
SIGNED_HYDRA_TYPES = {
    8: 'Int8',
    16: 'Int16',
    32: 'Int32',
    64: 'Int64'
}


def extract_type(node, cursor_kind):
    """ Extract recursively the structs from a given source node. """
    if node is None:
        return []

    children = node.get_children()
    structs = []
    for child in children:
        if child.kind == cursor_kind:
            structs.append(child)

        structs += extract_structs(child)

    return structs


def extract_structs(node):
    """ Extract recursively the structs from a given source node. """
    return extract_type(node, CursorKind.STRUCT_DECL)


def extract_enums(node):
    return extract_type(node, CursorKind.ENUM_DECL)


def resolve_type(field_type, struct_types, raw_type=False):
    """
    Resolve the Hydra type name for the given field type.

    :param field_type:		The type of the field, as given by libclang.
    :param struct_types:	A dict mapping fully-qualified-names -> `StructType`s
    :param raw_type:		If True, returns the name of the Hydra type without boilerplate.

    :return:	A string, the name of type.
    """
    if raw_type:
        template = '%s'
    else:
        template = '%s()'

    # Integral types
    if field_type.kind in SIGNED_TYPES:
        return template % SIGNED_HYDRA_TYPES[field_type.get_size() * 8]
    elif field_type.kind in UNSIGNED_TYPES:
        return template % UNSIGNED_HYDRA_TYPES[field_type.get_size() * 8]

    # Floating types.
    if field_type.kind == TypeKind.FLOAT:
        return template % HYDRA_FLOAT
    elif field_type.kind == TypeKind.DOUBLE:
        return template % HYDRA_DOUBLE

    if field_type.kind == TypeKind.ENUM:
        enum_type = struct_types[field_type.spelling]
        return template % enum_type.type_name

    if raw_type:
        template = '%s'
    else:
        template = 'NestedStruct(%s)'

    # Complex types.
    if field_type.kind == TypeKind.RECORD:
        struct_type = struct_types[field_type.spelling]
        return template % struct_type.type_name

    if field_type.kind == TypeKind.CONSTANTARRAY:
        element_type = resolve_type(field_type.get_array_element_type(), struct_types, raw_type=True)
        element_count = field_type.get_array_size()
        return 'Array(%u, %s)' % (element_count, element_type)

    raise ValueError()


class StructType(object):
    """ A class holding the data of one struct type. """

    def __init__(self, cursor):
        self.cursor = cursor
        self.type = cursor.type
        self.type_name = cursor.spelling

        self.fields = collections.OrderedDict()
        for field in self.type.get_fields():
            self.fields[field.spelling] = field.type
            if field.type.kind == TypeKind.TYPEDEF:
                self.fields[field.spelling] = field.type.get_canonical()

    def format(self, types, output):
        output.write("class %s(Struct):\n" % self.type_name)

        if self.cursor.brief_comment is not None:
            output.write('\t""" %s """\n\n' % self.cursor.brief_comment)

        for n, t in self.fields.items():
            output.write('\t%s = %s\n' % (n, resolve_type(t, types)))

        output.write('\n\n')


class EnumType(object):

    def __init__(self, cursor):
        self.cursor = cursor
        self.type = cursor.enum_type
        self.type_name = cursor.spelling

        self.literals = collections.OrderedDict()
        for literal in self.cursor.get_children():
            self.literals[literal.spelling] = literal.enum_value

    def format(self, types, output):
        output.write('class %s(EnumClass):\n' % self.type_name)

        if self.cursor.brief_comment is not None:
            output.write('\t""" %s """\n\n' % self.cursor.brief_comment)

        for n, l in self.literals.items():
            output.write('\t%s = Literal(%d)\n' % (n, l))

        output.write('\n\n')


class ParsedTranslationUnit(object):
    """ A class holding the data of one translation unit (e.g. *.cpp file)."""

    def __init__(self, file_name):
        index = Index.create()
        tu = index.parse(file_name)

        self.types = collections.OrderedDict()
        for e in extract_enums(tu.cursor):
            self.types[e.type.spelling] = EnumType(e)

        for s in extract_structs(tu.cursor):
            self.types[s.type.spelling] = StructType(s)

    def dump(self, output=sys.stdout):
        for c_type in self.types.values():
            c_type.format(self.types, output)


if __name__ == '__main__':
    ParsedTranslationUnit(sys.argv[1]).dump()
