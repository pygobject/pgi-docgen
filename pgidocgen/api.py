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

    def __init__(self):
        self._modules = []

    def add_module(self, namespace, version):
        """Add a module: add_module('Gtk', '3.0')"""

        # XXX: we bind all attributes here so the class hierarchy is created
        # and cls.__subclasses__() works in each ModuleGenerator
        # even across namespaces
        mod = util.import_namespace(namespace, version)
        for key in dir(mod):
            getattr(mod, key, None)

        self._modules.append((namespace, version))

    def is_empty(self):
        return not self._modules

    def get_names(self):
        modules = sorted(self._modules, key=lambda x: x[0].lower())
        module_names = []
        for namespace, version in modules:
            gen = ModuleGenerator(namespace, version)
            module_names.extend(gen.get_names())
        return ["api/%s" % n for n in module_names]

    def write(self, dir_, *args):
        modules = sorted(self._modules, key=lambda x: x[0].lower())

        path = os.path.join(dir_, self.API_DIR)
        os.mkdir(path)

        for namespace, version in modules:
            gen = ModuleGenerator(namespace, version)
            gen.write(path)
