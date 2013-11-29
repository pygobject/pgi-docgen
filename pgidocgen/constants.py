# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from .util import Generator


class ConstantsGenerator(Generator):

    def __init__(self, dir_, module_fileobj):
        self.path = os.path.join(dir_, "constants.rst")

        self._consts = {}
        self._module = module_fileobj

    def add_constant(self, name, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._consts[name] = code

    def get_names(self):
        return [os.path.basename(self.path)]

    def is_empty(self):
        return not bool(self._consts)

    def write(self):
        names = self._consts.keys()
        names.sort()

        handle = open(self.path, "wb")
        handle.write("""\
Constants
=========

""")

        for name in names:
            handle.write("""
.. autodata:: %s

""" % name)

        for name in names:
            code = self._consts[name]
            self._module.write(code + "\n")

        handle.close()
