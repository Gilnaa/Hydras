#!/usr/bin/env python

from emitters import *
from hydra import *
from argparse import ArgumentParser
from time import strftime
import imp
from os.path import abspath


class OutputContext(object):
    def __init__(self, source_name, emitters, structs):
        self.includes = set()
        self.global_namespace = collections.OrderedDict()
        self.emitters = emitters
        self.structs = structs
        self.source_name = source_name

    def get_emitter_for(self, member):
        for emitter in self.emitters:
            if emitter.can_emit_for(member):
                return emitter
        raise NotImplementedError("No emitter is implemented for type %s" % member)

    def generate(self):
        for s in self.structs:
            self.get_emitter_for(s).emit(None, s, self)

        include_string = ''
        if len(self.includes) > 0:
            includes = map(lambda inc: '#include <%s>' % inc, self.includes)
            include_string = '\n'.join(includes)

        structs_string = ''
        for s in self.global_namespace.values():
            structs_string += s

        output = FILE_HEADER.format(source_name=self.source_name,
                                    timestamp=strftime('%H:%M %d/%m/%Y'),
                                    includes=include_string,
                                    structs=structs_string)

        return output


def get_cli_args():
    parser = ArgumentParser(description="Translate Hydra structs into C structs.")
    parser.add_argument('input_file', help='A python module containing the modules')
    parser.add_argument('-o', '--output')

    args = parser.parse_args()
    input_file, output = (args.input_file, args.output)

    return input_file, output


def main():
    emitters = [StructEmitter(),
                ScalarEmitter(),
                NestedStructEmitter(),
                ArrayEmitter(),
                BitFieldEmitter(),
                PadEmitter(),
                EnumEmitter()]

    input_file, output = get_cli_args()
    mod = imp.load_source('a', input_file)
    structs = filter(is_struct_derived, vars(mod).values())

    context = OutputContext(abspath(input_file), emitters, structs)
    print context.generate()


if __name__ == '__main__':
    main()
