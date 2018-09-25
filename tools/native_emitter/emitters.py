from emitter_utils import *
from emitter_config import *


class Emitter(object):
    def emit(self, name, formatter, context, tab_level=0):
        pass

    def can_emit_for(self, member):
        pass


class ScalarEmitter(Emitter):
    def emit(self, name, formatter, context, tab_level=0):
        context.includes.add('stdint.h')
        return '%s%s %s;' % (generate_tabs(tab_level), SCALAR_LEXICON[type(formatter)], name)

    def can_emit_for(self, member):
        return type(member) in SCALAR_LEXICON.keys()


class StructEmitter(Emitter):
    def emit(self, name, formatter, context, tab_level=0):
        members = []
        for member_name, member_formatter in formatter.get_struct_fields():
            emitter = context.get_emitter_for(member_formatter)
            members.append(emitter.emit(member_name, member_formatter, context, tab_level + 1))

        code = EMITTER_SETTINGS['struct_style'].format(name=formatter.get_struct_name(), members='\n'.join(members))
        context.global_namespace[formatter.get_struct_name()] = code
        return code

    def can_emit_for(self, member):
        return is_struct_derived(member)


class NestedStructEmitter(Emitter):
    def emit(self, name, formatter, context, tab_level=0):
        obj = formatter.default_value
        context.get_emitter_for(obj).emit(name, obj, context)
        tabs = generate_tabs(tab_level)
        return '%s%s %s;' % (tabs, type(obj).__name__, name)

    def can_emit_for(self, member):
        return type(member) is NestedStruct


class ArrayEmitter(Emitter):
    def emit(self, name, formatter, context, tab_level=0):
        tabs = generate_tabs(tab_level)
        type_name = formatter.nested_struct_type
        if formatter.is_type_scalar:
            type_name = SCALAR_LEXICON[type_name]
        else:
            type_name = type_name.get_struct_name()
            # Make sure the type of the array gets generated as well.
            context.get_emitter_for(formatter.default_value[0]).emit(None, formatter.default_value[0], context)

        length = formatter.length

        return '%s%s %s[%d];' % (tabs, type_name, name, length)

    def can_emit_for(self, member):
        return type(member) is TypedArray


class BitFieldEmitter(Emitter):
    def emit(self, name, formatter, context, tab_level=0):
        boilerplate_tabs = generate_tabs(tab_level)
        if EMITTER_SETTINGS['inline_bitfield']:
            member_tabs = generate_tabs(tab_level)
        else:
            member_tabs = generate_tabs(tab_level + 1)

        fields = []
        for section_name, section in formatter.bits.items():
            field_string = '%s%s %s : %d;' % (member_tabs,
                                              EMITTER_SETTINGS['bitfield_section_type'],
                                              section_name,
                                              section.size)
            fields.append(field_string)

        fields = '\n'.join(fields)

        if EMITTER_SETTINGS['inline_bitfield']:
            return fields
        else:
            return EXPLICIT_BITFIELD_TEMPLATE.format(t=boilerplate_tabs, fields=fields, name=name)

    def can_emit_for(self, member):
        return type(member) is BitField


class PadEmitter(Emitter):
    def emit(self, name, formatter, context, tab_level=0):
        return '%s%s %s[%d]; // Spare' % (generate_tabs(tab_level),
                                          EMITTER_SETTINGS['padding_type'],
                                          name,
                                          formatter.length)

    def can_emit_for(self, member):
        return type(member) is Pad


class EnumEmitter(Emitter):
    def emit(self, name, formatter, context, tab_level=0):
        enum_name = 'E' + name.capitalize()
        tabs = generate_tabs(tab_level)

        enum_members = []
        for literal, value in formatter.items.items():
            enum_members.append(ENUM_LITERAL_TEMPLATE.format(t=tabs, name=literal, value=value))
        enum_members = '\n'.join(enum_members)

        context.global_namespace[enum_name] = ENUM_DEF_CXX.format(name=enum_name, members=enum_members)

        return "%s%s %s;" % (tabs, enum_name, name)

    def can_emit_for(self, member):
        return type(member) is Enum
