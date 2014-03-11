# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


class FlagsGenerator(util.Generator):

    def __init__(self, dir_):
        self.path = os.path.join(dir_, "flags.rst")

        self._flags = {}

    def add_flags(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._flags[obj] = code

    def get_names(self):
        return [os.path.basename(self.path)]

    def is_empty(self):
        return not bool(self._flags)

    def write(self, module_fileobj):
        classes = self._flags.keys()
        classes.sort(key=lambda x: x.__name__)

        handle = open(self.path, "wb")

        handle.write("""
=====
Flags
=====

""")

        if not classes:
            handle.write("None\n\n")

        for cls in classes:
            handle.write("* :class:`" + cls.__module__ + "." + cls.__name__ + "`\n")

        handle.write("""
Details
-------

""")

        for cls in classes:
            if util.is_base(cls):
                handle.write("""
.. autoclass:: %s
    :members:
    :undoc-members:
    :private-members:

""" % (cls.__module__ + "." + cls.__name__))
            else:
                handle.write("""
.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
    :private-members:

""" % (cls.__module__ + "." + cls.__name__))

        for cls in classes:
            code = self._flags[cls]
            module_fileobj.write(code + "\n")

        handle.close()
