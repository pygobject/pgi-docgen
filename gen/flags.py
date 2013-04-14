# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


class FlagsGenerator(util.Generator):

    def __init__(self, dir_, module_fileobj):
        self.path = os.path.join(dir_, "flags.rst")

        self._flags = {}
        self._module = module_fileobj

    def add_flags(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._flags[obj] = code

    def get_name(self):
        return os.path.basename(self.path)

    def is_empty(self):
        return not bool(self._flags)

    def write(self):
        classes = self._flags.keys()
        classes.sort(key=lambda x: x.__name__)

        handle = open(self.path, "wb")
        handle.write("""\
Flags
=====

""")

        for cls in classes:
            title = util.make_rest_title(cls.__name__, "-")
            handle.write("""
%s

.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
    :private-members:

""" % (title, cls.__module__ + "." + cls.__name__))

        for cls in classes:
            code = self._flags[cls]
            self._module.write(code + "\n")

        handle.close()
