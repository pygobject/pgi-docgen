# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


class FunctionGenerator(util.Generator):

    def __init__(self, dir_):
        self.path = os.path.join(dir_, "functions.rst")

        self._funcs = {}

    def get_names(self):
        return [os.path.basename(self.path)]

    def is_empty(self):
        return not bool(self._funcs)

    def add_function(self, name, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._funcs[name] = code

    def write(self, module_fileobj):

        handle = open(self.path, "wb")
        handle.write("""
Functions
=========
""")

        handle.write(".. autosummary::\n\n")
        for name, code in sorted(self._funcs.items()):
            handle.write("    %s\n" % name)

        handle.write("""
Details
-------
""")

        for name, code in sorted(self._funcs.items()):
            module_fileobj.write(code)
            handle.write(".. autofunction:: %s\n\n" % name)

        handle.close()
