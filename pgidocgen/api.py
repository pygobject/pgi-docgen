# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util
from .module import ModuleGenerator


class APIGenerator(util.Generator):
    API_DIR = "api"

    def __init__(self, dest):
        self._dest = dest
        self._modules = []

    def add_module(self, namespace, version):
        """Add a module: add_module('Gtk', '3.0')"""
        self._modules.append((namespace, version))

    def is_empty(self):
        return not self._modules

    def get_names(self):
        return ["api/%s" % n for n in self._names]

    def write(self):
        modules = sorted(self._modules, key=lambda x: x[0].lower())

        path = os.path.join(self._dest, self.API_DIR)
        os.mkdir(path)

        module_names = []
        for namespace, version in modules:
            gen = ModuleGenerator(path, namespace, version)
            gen.write()
            module_names.extend(gen.get_names())
        self._names = module_names
