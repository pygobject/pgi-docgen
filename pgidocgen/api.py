# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util
from .module import ModuleGenerator


class APIGenerator(util.Generator):
    """This is just a proxy for ModuleGenerator which adds a directory"""

    API_DIR = "api"

    def __init__(self):
        self._gen = ModuleGenerator()

    def add_module(self, namespace, version):
        self._gen.add_module(namespace, version)

    def is_empty(self):
        return self._gen.is_empty()

    def get_names(self):
        return ["%s/%s" % (self.API_DIR, n) for n in self._gen.get_names()]

    def write(self, dir_, *args):
        path = os.path.join(dir_, self.API_DIR)
        os.mkdir(path)
        self._gen.write(path)
