# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


class StructGenerator(util.Generator):
    def __init__(self, dir_, module_fileobj):
        self._sub_dir = os.path.join(dir_, "structs")
        self.path = os.path.join(self._sub_dir, "index.rst")

        self._structs = {}
        self._module = module_fileobj

    def get_name(self):
        return os.path.join("structs", "index.rst")

    def is_empty(self):
        return not bool(self._structs)

    def add_struct(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")
        self._structs[obj] = code

    def write(self):
        os.mkdir(self._sub_dir)

        structs = self._structs.keys()

        # write the code
        for cls in structs:
            self._module.write(self._structs[cls])

        index_handle = open(self.path, "wb")
        index_handle.write(util.make_rest_title("Structures") + "\n\n")

        # add classes to the index toctree
        index_handle.write(".. toctree::\n    :maxdepth: 1\n\n")
        for cls in sorted(structs, key=lambda x: x.__name__):
            index_handle.write("""\
    %s
""" % cls.__name__)

        for cls in structs:
            h = open(os.path.join(self._sub_dir, cls.__name__) + ".rst", "wb")
            name = cls.__module__ + "." + cls.__name__
            title = name
            h.write(util.make_rest_title(title, "=") + "\n")

            h.write("""
.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
""" % name)

            h.close()

        index_handle.close()
