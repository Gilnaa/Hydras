from emitter_config import *


def generate_tabs(tab_level):
    return tab_level * EMITTER_SETTINGS['indentation']


def is_struct_derived(cls):
    if inspect.isclass(cls):
        return issubclass(cls, Struct) and cls is not Struct
    return is_struct_derived(type(cls))
