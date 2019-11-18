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
from elftools.elf.elffile import ELFFile
from elftools.dwarf.die import DIE
from typing import TextIO, List
from collections import OrderedDict

# Type States
STATE_INITIAL = 0
STATE_IN_PROCESS = 1
STATE_FINALIZED = 2
flatten_arrays = False

autogen_comment = [ '# This struct has been automatically generated, see top of file\n',
                    '# noinspection PyPep8Naming\n' ]


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


class Type(object):
    def __init__(self, die: DIE):
        self.source_object = die
        self.name = None
        self.byte_size = None
        self.state = STATE_INITIAL

    def get_type_dependencies(self) -> List[int]:
        return []

    def finalize(self, types, finalization_order):
        if self.state == STATE_FINALIZED:
            return

        if self.state == STATE_IN_PROCESS:
            raise RuntimeError("Type cycle detected")

        self.state = STATE_IN_PROCESS
        self.do_finalize(types, finalization_order)
        if self not in finalization_order:
            finalization_order.append(self)
        self.state = STATE_FINALIZED

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

    def needs_to_generate_hydra(self) -> bool:
        return False

    def generate_hydras_definition(self, fp: TextIO):
        """
        Generates top-level definitions for this type if needed.
        :param fp: Output text stream
        """
        pass

    def is_pointer(self) -> bool:
        return False


class Primitive(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        self.name = die.attributes['DW_AT_name'].value.decode('utf-8')

        self.byte_size = die.attributes['DW_AT_byte_size'].value

    def __repr__(self):
        return self.name

    def get_hydras_type(self):
        if self.name == 'float':
            return 'f32'
        elif self.name == 'double':
            return 'f64'

        bitsize = self.byte_size * 8
        if 'unsigned' in self.name:
            return f'u{bitsize}'
        else:
            return f'i{bitsize}'

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

    def needs_to_generate_hydra(self) -> bool:
        return True

    def generate_hydras_definition(self, fp: TextIO):
        padding_counter = 0
        last_ending_offset = 0

        # Adding 2 empty lines in order to comply w/ PEP8
        fp.writelines(autogen_comment)
        fp.write(f'class {self.name}(Struct):\n')

        for offset, member_type, member_name in self.members:
            # Generate entries for compiler introduced padding
            if last_ending_offset < offset:
                fp.write(f'    _padding_{padding_counter} = uint8_t[{offset - last_ending_offset}]\n')
                padding_counter += 1
            last_ending_offset = offset + member_type.byte_size

            if member_type.is_pointer():
                fp.write(f'    # <POINTER> ({repr(member_type)})\n')

            # Output the member itself
            type_hint = f': List[{member_type.item_type.get_hydras_type()}]' if type(member_type) == Array else ''
            fp.write(f'    {member_name}{type_hint} = {member_type.get_hydras_type()}\n')

        # The compiler can also generate postfix padding.
        if last_ending_offset != self.byte_size:
            fp.write(f'    _padding_{padding_counter} = uint8_t[{self.byte_size - last_ending_offset}]\n')


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

    def needs_to_generate_hydra(self) -> bool:
        return True

    def generate_hydras_definition(self, fp: TextIO):
        # Adding 2 empty lines in order to comply w/ PEP8
        fp.write(f'class {self.name}(Enum):\n')

        for name, value in self.literals.items():
            # Output the member itself
            fp.write(f'    {name} = {value}\n')


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
        if self.state != STATE_FINALIZED:
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


class Typedef(Type):
    def __init__(self, die: DIE):
        super().__init__(die)

        self.name = die.attributes['DW_AT_name'].value.decode('utf-8')

        if 'DW_AT_type' in die.attributes:
            self.alias = die.attributes['DW_AT_type'].value
        else:
            # Probably `void`
            self.alias = None

    def do_finalize(self, types, finalization_order):
        if not self.needs_to_generate_hydra():
            self.byte_size = int(re.match(r'u?int(8|16|32|64)_t', self.name).group(1)) // 8
        elif self.alias is not None:
            self.alias = types[self.alias]
            self.alias.finalize(types, finalization_order)
            self.byte_size = self.alias.byte_size

    def get_type_dependencies(self):
        if not self.needs_to_generate_hydra():
            return []
        return [self.alias]

    def get_hydras_type(self):
        return self.name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if not self.needs_to_generate_hydra():
            return isinstance(other, Typedef) and other.name == self.name

        return isinstance(other, Typedef) and other.name == self.name and other.alias == self.alias

    def needs_to_generate_hydra(self) -> bool:
        # Skip generation of common Hydras typedefs
        return not bool(re.match(r'u?int(8|16|32|64)_t', self.name))

    def generate_hydras_definition(self, fp: TextIO):
        if not self.needs_to_generate_hydra():
            return

        if self.alias.is_pointer():
            fp.write(f'# <POINTER> ({repr(self.alias)})\n')
        fp.write(f'{self.name} = {self.alias.get_hydras_type()}\n')


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
        ptr_type = {4:  'u32', 8: 'u64'}[self.byte_size]
        return f'{ptr_type}'

    def is_pointer(self) -> bool:
        return True

    def __eq__(self, other):
        return isinstance(other, Pointer) and other.name == self.name and other.item_type == self.item_type

    def __repr__(self):
        if self.item_type is None:
            return 'void *'
        return f'{repr(self.item_type)} *'


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
        # debug(self.die.tag)
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
    # A mapping of `name: type` across all translation units.
    aggregated_types_by_name = {}
    # List of types by finalization order
    finalization_order = []

    for cu in elf.get_dwarf_info().iter_CUs():
        cu_name = cu.get_top_DIE().attributes['DW_AT_name'].value.decode('utf-8')
        info(f'Processing {cu_name}')

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
                    types[offset] = aggregated_types_by_name[typ.name]
                else:
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

            else:
                typ.finalize(types, finalization_order)

        # Update the aggregate
        for typ in types.values():
            aggregated_types_by_name[typ.name] = typ

    return finalization_order


def generate_hydra_file(structs, fp: TextIO):
    fp.write('# File was automatically generated using the dwarf2hydra.py tool.\n')
    fp.writelines([
            'from hydras import *\n',
            'from typing import List\n'
        ])

    last_generated_type = None
    for struct in structs:
        if not struct.needs_to_generate_hydra():
            continue

        # If anything was generated from the last struct, insert 2 line-feeds to conform to PEP8 ...
        # ... unless both of them are typedefs.
        if not (isinstance(struct, Typedef) and isinstance(last_generated_type, Typedef)):
            fp.write('\n\n')

        struct.generate_hydras_definition(fp)

        last_generated_type = struct


def main():
    global flatten_arrays
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
    args = args.parse_args()

    whitelist_re = re.compile('|'.join(map('(?:{0})'.format, args.whitelist)))

    flatten_arrays = args.flatten_arrays
    with open(args.input_file, 'rb') as f:
        elf = ELFFile(f)
        if not elf.has_dwarf_info():
            error("Object file has no dwarf info!")
            sys.exit(1)

        output = sys.stdout
        if args.output is not None:
            output = open(args.output, 'w')

        generate_hydra_file(parse_dwarf_info(elf, whitelist_re, True), output)


if __name__ == '__main__':
    main()