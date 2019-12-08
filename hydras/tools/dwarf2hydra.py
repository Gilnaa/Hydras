#!/usr/bin/env python3
"""
This script extracts DWARF symbols from an ELF files
and tries to reconstruct Hydras definitions from those symbols.

:file: dwarf2hydra.py
:date: 14/10/2019
:authors:
    - Gilad Naaman <gilad@naaman.io>
"""
import re
import os
import sys
import argparse

from elftools.dwarf.compileunit import CompileUnit
from elftools.elf.elffile import ELFFile
from elftools.dwarf.die import DIE
from typing import TextIO, List, Union
from collections import OrderedDict
from enum import IntEnum


autogen_comment = ['# This item has been automatically generated, see top of file',
                   '# noinspection PyPep8Naming']

TYPE_SETS = {
    'default': {
        'int': {1: 'i8', 2: 'i16', 4: 'i32', 8: 'i64'},
        'uint': {1: 'u8', 2: 'u16', 4: 'u32', 8: 'u64'},
        'float': {4: 'f32', 8: 'f64'}
    },
    'default_le': {
        'int': {1: 'i8_le', 2: 'i16_le', 4: 'i32_le', 8: 'i64_le'},
        'uint': {1: 'u8_le', 2: 'u16_le', 4: 'u32_le', 8: 'u64_le'},
        'float': {4: 'f32_le', 8: 'f64_le'}
    },
    'default_be': {
        'int': {1: 'i8_be', 2: 'i16_be', 4: 'i32_be', 8: 'i64_be'},
        'uint': {1: 'u8_be', 2: 'u16_be', 4: 'u32_be', 8: 'u64_be'},
        'float': {4: 'f32_be', 8: 'f64_be'}
    },
    'cstdint': {
        'int': {1: 'int8_t', 2: 'int16_t', 4: 'int32_t', 8: 'int64_t'},
        'uint': {1: 'uint8_t', 2: 'uint16_t', 4: 'uint32_t', 8: 'uint64_t'},
        'float': {4: 'float32_t', 8: 'float64_t'}
    },
    'cstdint_le': {
        'int': {1: 'int8_t_le', 2: 'int16_t_le', 4: 'int32_t_le', 8: 'int64_t_le'},
        'uint': {1: 'uint8_t_le', 2: 'uint16_t_le', 4: 'uint32_t_le', 8: 'uint64_t_le'},
        'float': {4: 'float32_t_le', 8: 'float64_t_le'}
    },
    'cstdint_be': {
        'int': {1: 'int8_t_be', 2: 'int16_t_be', 4: 'int32_t_be', 8: 'int64_t_be'},
        'uint': {1: 'uint8_t_be', 2: 'uint16_t_be', 4: 'uint32_t_be', 8: 'uint64_t_be'},
        'float': {4: 'float32_t_be', 8: 'float64_t_be'}
    },
}

flatten_arrays = False
chosen_type_set = None


def eprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def debug(*args, **kwargs):
    print('\x1b[32m\x1b[1m', file=sys.stderr, end='')
    print(*args, **kwargs, file=sys.stderr, end='')
    print('\x1b[0m', file=sys.stderr)


def info(*args, **kwargs):
    print('\x1b[34m\x1b[1m', file=sys.stderr, end='')
    print(*args, **kwargs, file=sys.stderr, end='')
    print('\x1b[0m', file=sys.stderr)


def warn(*args, **kwargs):
    print('\x1b[35m\x1b[1m', file=sys.stderr, end='')
    print(*args, **kwargs, file=sys.stderr, end='')
    print('\x1b[0m', file=sys.stderr)


def error(*args, **kwargs):
    print('\x1b[31m\x1b[1m', file=sys.stderr, end='')
    print(*args, **kwargs, file=sys.stderr, end='')
    print('\x1b[0m', file=sys.stderr)


class CodeOutput:
    def __init__(self, fp: TextIO):
        self.fp = fp
        self.last_item_was_typedef = False

    def write_struct(self, lines: List[str]):
        self.fp.write('\n\n')
        self.last_item_was_typedef = False

        for l in lines:
            self.fp.write(l)
            self.fp.write('\n')

    def write_typedef(self, lines: List[str]):
        if not self.last_item_was_typedef:
            self.fp.write('\n\n')
            self.last_item_was_typedef = True

        for l in lines:
            self.fp.write(l)
            self.fp.write('\n')


class TypeState(IntEnum):
    INITIAL = 0
    IN_PROCESS = 1
    FINALIZED = 2
    GENERATED = 3


class Type(object):

    def __init__(self, die: DIE):
        self.source_object = die
        self.name = None
        self.byte_size = None
        self.state = TypeState.INITIAL

    def get_type_dependencies(self) -> Union[List[int], List['Type']]:
        return []

    def finalize(self, types, finalization_order):
        if self.state == TypeState.FINALIZED:
            return

        if self.state == TypeState.IN_PROCESS:
            raise RuntimeError("Type cycle detected")

        self.state = TypeState.IN_PROCESS
        self.do_finalize(types, finalization_order)
        if self not in finalization_order:
            finalization_order.append(self)
        self.state = TypeState.FINALIZED

    def do_finalize(self, types, finalization_order):
        pass

    def get_location(self):
        node = self.source_object
        while node is not None and node.tag != 'DW_TAG_compile_unit':
            node = node.get_parent()

        if node is None:
            return None

        comp_dir = node.attributes['DW_AT_comp_dir'].value
        file_name = node.attributes['DW_AT_name'].value
        file_name = os.path.join(comp_dir, file_name)
        return file_name

    def get_hydras_type(self):
        pass

    def generate_hydras_definition(self, fp: CodeOutput):
        """
        Recursively generate hydras definitions for data types
        :param fp: Output text stream
        """
        if self.state == TypeState.GENERATED:
            return
        else:
            assert self.state == TypeState.FINALIZED

        dependencies = sorted(self.get_type_dependencies(), key=lambda d: d.get_sorting_key())
        for dependency in dependencies:
            dependency.generate_hydras_definition(fp)

        self.do_generate_hydras_definition(fp)
        self.state = TypeState.GENERATED

    def do_generate_hydras_definition(self, fp: CodeOutput):
        pass

    def is_pointer(self) -> bool:
        return False

    def get_sorting_key(self):
        return self.name


class Primitive(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        self.name = die.attributes['DW_AT_name'].value.decode('utf-8')
        self.byte_size = die.attributes['DW_AT_byte_size'].value

    def __repr__(self):
        return self.get_hydras_type()

    def get_hydras_type(self):
        if self.name in ['float', 'double']:
            type_set = chosen_type_set['float']
        elif 'unsigned' in self.name:
            type_set = chosen_type_set['uint']
        else:
            type_set = chosen_type_set['int']

        return type_set[self.byte_size]

    def __eq__(self, other):
        return isinstance(other, Primitive) and \
               other.byte_size == self.byte_size and \
               other.name == self.name


class Struct(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        self.name = None
        if 'DW_AT_name' in die.attributes:
            self.name = die.attributes['DW_AT_name'].value.decode('utf-8')

        self.byte_size = 0
        if 'DW_AT_byte_size' in die.attributes:
            self.byte_size = die.attributes['DW_AT_byte_size'].value

        self.members = []
        for c in die.iter_children():
            if c.tag not in ['DW_TAG_member', 'DW_TAG_inheritance']:
                continue

            member_offset = c.attributes['DW_AT_data_member_location'].value
            type_num = c.attributes['DW_AT_type'].value
            if 'DW_AT_name' in c.attributes:
                member_name = c.attributes['DW_AT_name'].value.decode('utf-8') if c.tag == 'DW_TAG_member' else '<base>'
            else:
                member_name = '<unnamed>'
            self.members.append((member_offset, type_num, member_name))

    def do_finalize(self, types, finalization_order):
        new_members = []

        for offset, type_num, member_name in self.members:
            types[type_num].finalize(types, finalization_order)
            new_members.append((offset, types[type_num], member_name))

        self.members = new_members

    def get_type_dependencies(self):
        return (type_num for _, type_num, _ in self.members)

    def __str__(self):
        return self.name

    def __repr__(self):
        if len(self.members) == 0:
            return self.name

        return self.name + '(%s)' % ', '.join(map(lambda m: str(m[1]), self.members))

    def get_hydras_type(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Struct) and \
               other.byte_size == self.byte_size and \
               other.members == self.members and \
               other.name == self.name

    def do_generate_hydras_definition(self, fp: CodeOutput):
        padding_counter = 0
        last_ending_offset = 0
        byte_type = chosen_type_set['uint'][1]

        # Adding 2 empty lines in order to comply w/ PEP8
        struct_lines = autogen_comment.copy()
        struct_lines.append(f'class {self.name}(Struct):')

        for offset, member_type, member_name in self.members:
            # Generate entries for compiler introduced padding
            if last_ending_offset < offset:
                struct_lines.append(f'    _padding_{padding_counter} = {byte_type}[{offset - last_ending_offset}]')
                padding_counter += 1
            last_ending_offset = offset + member_type.byte_size

            if member_type.is_pointer():
                struct_lines.append(f'    # <POINTER> ({repr(member_type)})')

            # Output the member itself
            type_hint = f': List[{member_type.item_type.get_hydras_type()}]' if type(member_type) == Array else ''
            struct_lines.append(f'    {member_name}{type_hint} = {member_type.get_hydras_type()}')

        # The compiler can also generate postfix padding.
        if last_ending_offset != self.byte_size:
            struct_lines.append(f'    _padding_{padding_counter} = {byte_type}[{self.byte_size - last_ending_offset}]')

        fp.write_struct(struct_lines)


class EnumType(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        self.name = '<unnamed-enum>'
        if 'DW_AT_name' in die.attributes:
            self.name = die.attributes['DW_AT_name'].value.decode('utf-8')

        self.literals = OrderedDict()
        for lit in die.iter_children():
            assert lit.tag == 'DW_TAG_enumerator'
            name = lit.attributes['DW_AT_name'].value.decode('utf-8')
            value = lit.attributes['DW_AT_const_value'].value
            self.literals[name] = value

        if 'DW_AT_type' in die.attributes:
            self.item_type = die.attributes['DW_AT_type'].value
        else:
            # Probably `void`
            assert False, 'TODO'

    def get_type_dependencies(self):
        return [self.item_type]

    def do_finalize(self, types, finalization_order):
        if self.item_type is not None:
            self.item_type = types[self.item_type]
            self.item_type.finalize(types, finalization_order)
            self.byte_size = self.item_type.byte_size

    def __repr__(self):
        return self.name

    def get_hydras_type(self):
        return f'{self.name}'

    def __eq__(self, other):
        return isinstance(other, EnumType) and \
               other.name == self.name and \
               other.item_type == self.item_type and \
               other.literals == self.literals

    def do_generate_hydras_definition(self, fp: CodeOutput):
        enum_lines = autogen_comment.copy()
        enum_lines.append(f'class {self.name}(Enum, underlying_type={self.item_type.get_hydras_type()}):')

        for name, value in self.literals.items():
            # Output the member itself
            enum_lines.append(f'    {name} = {value}')

        fp.write_struct(enum_lines)


class UnionType(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        self.name = '<unnamed-union>'
        if 'DW_AT_name' in die.attributes:
            self.name = die.attributes['DW_AT_name'].value.decode('utf-8')

        self.byte_size = die.attributes['DW_AT_byte_size'].value

        self.variants = OrderedDict()
        for variant in die.iter_children():
            assert variant.tag == 'DW_TAG_member'
            name = variant.attributes['DW_AT_name'].value.decode('utf-8')
            value = variant.attributes['DW_AT_type'].value
            self.variants[name] = value

    def do_finalize(self, types, finalization_order):
        for name, variant in self.variants.items():
            types[variant].finalize(types, finalization_order)
            self.variants[name] = types[variant]

    def get_type_dependencies(self):
        return self.variants.values()

    def __repr__(self):
        return self.name

    def get_hydras_type(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, UnionType) and \
               other.name == self.name and \
               other.variants == self.variants


class Array(Type):
    def __init__(self, die: DIE):
        global flatten_arrays
        super().__init__(die)

        self.item_type = die.attributes['DW_AT_type'].value

        self.dimensions = []
        self.is_vla = False
        for c in die.iter_children():
            if 'DW_AT_upper_bound' in c.attributes:
                dimension = c.attributes['DW_AT_upper_bound'].value + 1

                if flatten_arrays and len(self.dimensions) > 0:
                    self.dimensions[0] = self.dimensions[0] * dimension
                else:
                    self.dimensions.append(dimension)
            else:
                assert self.is_vla is False
                self.is_vla = True

    def do_finalize(self, types, finalization_order):
        self.item_type = types[self.item_type]
        self.item_type.finalize(types, finalization_order)
        self.byte_size = self.item_type.byte_size
        for d in self.dimensions:
            self.byte_size *= d

    def get_type_dependencies(self):
        return [self.item_type]

    def __repr__(self):
        if self.state != TypeState.FINALIZED:
            return "<abstract array type>"

        base_type = repr(self.item_type)

        for d in self.dimensions:
            base_type += f'[{d}]'

        return base_type

    def get_hydras_type(self):
        t = self.item_type.get_hydras_type()
        for d in self.dimensions[::-1]:
            t = f'{t}[{d}]'

        if self.is_vla:
            t = f'{t}[:]'

        return t

    def __eq__(self, other):
        return isinstance(other, Array) and other.dimensions == self.dimensions and other.item_type == self.item_type

    def is_pointer(self) -> bool:
        return self.item_type.is_pointer()

    def get_sorting_key(self):
        return self.item_type.get_sorting_key()


class Typedef(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        self.name = die.attributes['DW_AT_name'].value.decode('utf-8')
        self.category = None

        if 'DW_AT_type' in die.attributes:
            self.alias = die.attributes['DW_AT_type'].value
        else:
            # Probably `void`
            self.alias = None

    def do_finalize(self, types, finalization_order):
        matches = self._match_primitive_type()
        if matches:
            self.byte_size = int(matches.group(2)) // 8
            self.category = matches.group(1)
        elif self.alias is not None:
            self.alias = types[self.alias]
            self.alias.finalize(types, finalization_order)
            self.byte_size = self.alias.byte_size

    def get_type_dependencies(self):
        if self._match_primitive_type():
            return []
        return [self.alias]

    def get_hydras_type(self):
        if self._match_primitive_type():
            return chosen_type_set[self.category][self.byte_size]

        return self.name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if self._match_primitive_type():
            return isinstance(other, Typedef) and other.name == self.name

        return isinstance(other, Typedef) and other.name == self.name and other.alias == self.alias

    def do_generate_hydras_definition(self, fp: CodeOutput):
        if self._match_primitive_type():
            return

        typedef_lines = []
        if self.alias.is_pointer():
            typedef_lines.append(f'# <POINTER> ({repr(self.alias)})')
        typedef_lines.append(f'{self.name} = {self.alias.get_hydras_type()}')
        fp.write_typedef(typedef_lines)

    def _match_primitive_type(self):
        return re.match(r'(float|u?int)(8|16|32|64)_t', self.name)


class Pointer(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        self.byte_size = die.attributes['DW_AT_byte_size'].value
        if 'DW_AT_type' in die.attributes:
            self.item_type = die.attributes['DW_AT_type'].value
        else:
            # Probably `void`
            self.item_type = None

    def do_finalize(self, types, finalization_order):
        if self.item_type is not None:
            types[self.item_type].finalize(types, finalization_order)
            self.item_type = types[self.item_type]

    def get_type_dependencies(self):
        return [self.item_type]

    def get_hydras_type(self):
        return chosen_type_set['uint'][self.byte_size]

    def is_pointer(self) -> bool:
        return True

    def __eq__(self, other):
        return isinstance(other, Pointer) and other.name == self.name and other.item_type == self.item_type

    def __repr__(self):
        if self.item_type is None:
            return 'void *'
        return f'{self.item_type.get_hydras_type()} *'

    def get_sorting_key(self):
        return self.item_type.get_sorting_key()


class ConstType(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        if 'DW_AT_type' in die.attributes:
            self.item_type = die.attributes['DW_AT_type'].value
        else:
            # Probably `void`
            self.item_type = None

    def do_finalize(self, types, finalization_order):
        if self.item_type is not None:
            types[self.item_type].finalize(types, finalization_order)
            self.item_type = types[self.item_type]
        self.byte_size = self.item_type.byte_size

    def get_type_dependencies(self):
        return [self.item_type]

    def get_hydras_type(self):
        return self.item_type.get_hydras_type()

    def __eq__(self, other):
        return isinstance(other, ConstType) and other.name == self.name and other.item_type == self.item_type

    def __repr__(self):
        if self.item_type is None:
            return 'const void'
        return f'const {repr(self.item_type)}'

    def is_pointer(self) -> bool:
        return self.item_type.is_pointer()

    def get_sorting_key(self):
        return self.item_type.get_sorting_key()


class FunctionPointer(Type):
    def __init__(self, die: DIE):
        super().__init__(die)
        self.die = die

        self.parameters = []
        for child in die.iter_children():
            if child.tag != 'DW_TAG_formal_parameter':
                continue
            self.parameters.append(die.attributes['DW_AT_type'].value)

    def get_type_dependencies(self) -> List[int]:
        return self.parameters

    def do_finalize(self, types, finalization_order):
        self.parameters = [types[offset] for offset in self.parameters]
        for typ in self.parameters:
            typ.finalize(types, finalization_order)

    def __repr__(self):
        return f'void ({", ".join(self.parameters)})'

    def get_hydras_type(self):
        return None

    def is_pointer(self) -> bool:
        return True


class UnsupportedType(Type):
    def __init__(self, die: DIE):
        super().__init__(die)
        self.die = die

    def do_finalize(self, types, finalization_order):
        pass

    def get_hydras_type(self):
        return None


TAG_TYPE_MAPPING = {
    'DW_TAG_structure_type': Struct,
    'DW_TAG_class_type': Struct,
    'DW_TAG_base_type': Primitive,
    'DW_TAG_typedef': Typedef,
    'DW_TAG_array_type': Array,
    'DW_TAG_pointer_type': Pointer,
    'DW_TAG_const_type': ConstType,
    'DW_TAG_enumeration_type': EnumType,
    'DW_TAG_union_type': UnionType,
    'DW_TAG_subroutine_type': FunctionPointer,
}


def parse_dwarf_info(elf, whitelist_re, skip_duplicated_symbols):
    def _get_cu_name(cu: CompileUnit) -> str:
        return cu.get_top_DIE().attributes['DW_AT_name'].value.decode('utf-8')

    # A mapping of `name: type` across all translation units.
    aggregated_types_by_name = {}
    # List of types by finalization order
    finalization_order = []

    for cu in elf.get_dwarf_info().iter_CUs():
        info(f'Processing {_get_cu_name(cu)}')

        # First, we must collect all DIEs into this dictionary so that code
        # from here-on-out will be able to index into it.
        dies = {die.offset - cu.cu_offset: die for die in cu.iter_DIEs()}
        types = {}

        # Collect all top-level nodes that are whitelisted and make sure that
        # all of their dependencies are processed as well.
        pred = lambda die: 'DW_AT_name' in die.attributes and \
                           whitelist_re.match(die.attributes['DW_AT_name'].value.decode('utf-8'))

        type_deps_to_process = {offset for offset, die in dies.items() if pred(die)}
        processed_types = set()
        while len(type_deps_to_process) > 0:
            offset = type_deps_to_process.pop()
            if offset in processed_types:
                continue
            processed_types.add(offset)

            die = dies[offset]
            types[offset] = TAG_TYPE_MAPPING.get(die.tag, UnsupportedType)(die)
            type_deps_to_process.update(types[offset].get_type_dependencies())

        for offset, typ in types.items():
            # When the same symbol is defined in multiple Translation-Units,
            # we perform either of the following:
            #  - Parse both definitions and make sure they are the same
            #  - Parse only once and reuse the same definition.
            if typ.name is not None and typ.name in aggregated_types_by_name:
                if skip_duplicated_symbols:
                    # debug(f'Replacing offset {offset} with cached type {typ.name}. '
                    #       f'(OID={id(typ)},NID={id(aggregated_types_by_name[typ.name])})')
                    types[offset] = aggregated_types_by_name[typ.name]
                else:
                    # TODO: This implementation is broken because
                    #       `finalize` still modifies `types` and it can create duplicates.
                    # We still finalize the type so we could check it,
                    # but we provide an empty list for the initialization order
                    # so we could avoid duplicates
                    typ.finalize(types, [])
                    if typ != aggregated_types_by_name[typ.name]:
                        error(f'Conflicting definitions for type `{typ.name}`')
                        info(f'First occurrence:')
                        eprint(repr(typ))
                        info(f'Second occurrence:')
                        eprint(repr(aggregated_types_by_name))
                        sys.exit(1)

        for offset, typ in types.items():
            typ.finalize(types, finalization_order)

        # Update the aggregate
        for typ in types.values():
            aggregated_types_by_name[typ.name] = typ

    return finalization_order


def generate_hydra_file(structs, whitelist_re, fp: TextIO):
    fp.writelines([
            '# File was automatically generated using the dwarf2hydra.py tool.\n'
            'from hydras import *\n',
            'from typing import List\n'
        ])

    structs = filter(lambda s: s.name is not None and whitelist_re.match(s.name), structs)
    structs = sorted(structs, key=lambda x: x.name)
    fp = CodeOutput(fp)
    for struct in structs:
        struct.generate_hydras_definition(fp)


def main():
    global flatten_arrays, chosen_type_set
    args = argparse.ArgumentParser(description='Parses an ELF file with DWARF debug symbols and generates Hydra '
                                               'definitions for the selected structs.'
                                               ''
                                               'If no whitelist patterns are specified, no structs will be printed.')
    args.add_argument('input_file', help='Path to the input ELF file.')
    args.add_argument('--whitelist', help='A regex pattern used to choose structs for generation.'
                                          'May be specified multiple times.',
                      type=str, action='append', default=[])
    args.add_argument('--flatten-arrays', help='Treat C matrices as long one dimensional arrays.', action='store_true')
    args.add_argument('-o', '--output', help='Name of output file.')
    args.add_argument('--type-set', help='Choose which type-set to use for primitives',
                      default='default', choices=TYPE_SETS.keys())
    args = args.parse_args()

    whitelist_re = re.compile('|'.join(map('(?:{0})'.format, args.whitelist)))

    chosen_type_set = TYPE_SETS[args.type_set]
    flatten_arrays = args.flatten_arrays

    with open(args.input_file, 'rb') as f:
        elf = ELFFile(f)
        if not elf.has_dwarf_info():
            error("Object file has no dwarf info!")
            sys.exit(1)

        output = sys.stdout
        if args.output is not None:
            output = open(args.output, 'w')

        structs = parse_dwarf_info(elf, whitelist_re, True)
        generate_hydra_file(structs, whitelist_re, output)


if __name__ == '__main__':
    main()
