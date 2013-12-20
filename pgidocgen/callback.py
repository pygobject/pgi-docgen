# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


class CallbackGenerator(util.Generator):

    def __init__(self, dir_, module_fileobj):
        self.path = os.path.join(dir_, "callbacks.rst")

        self._callbacks = {}
        self._module = module_fileobj

    def add_callback(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._callbacks[obj] = code

    def get_names(self):
        return [os.path.basename(self.path)]

    def is_empty(self):
        return not bool(self._callbacks)

    def write(self):
        funcs = self._callbacks.keys()
        funcs.sort(key=lambda x: x.__name__)

        handle = open(self.path, "wb")
        handle.write("""\
=========
Callbacks
=========

""")

        def get_name(func):
            return func.__module__ + "." + func.__name__

        if not funcs:
            handle.write("None\n\n")
        else:
            handle.write(".. autosummary::\n\n")

        for f in funcs:
            handle.write("    " + get_name(f) + "\n")

        handle.write("""\
Details
-------

""")

        for f in funcs:
            handle.write("""
.. autofunction:: %s

""" % get_name(f))

        for f in funcs:
            code = self._callbacks[f]
            self._module.write(code + "\n")

        handle.close()
