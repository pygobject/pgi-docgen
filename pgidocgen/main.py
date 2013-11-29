# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import shutil

from .tutorial import TutorialGenerator, AboutGenerator
from .api import APIGenerator
from . import util


class MainGenerator(util.Generator):
    """Creates the sphinx environment and the index page"""

    THEME_DIR = "theme"
    EXT_DIR = "ext"
    CONF_IN = "conf.in.py"

    def __init__(self, dest, tutorial=False):
        self._dest = dest
        self._modules = []
        self._tutorial = tutorial

        self._tutorial_gen = TutorialGenerator(dest)
        self._api_gen = APIGenerator(dest)
        self._about_gen = AboutGenerator(dest)

    def add_module(self, *args):
        self._api_gen.add_module(*args)

    def is_empty(self):
        if self._tutorial:
            return self._tutorial_gen.is_empty() and self._api_gen.is_empty()
        else:
            return self._api_gen.is_empty()

    def write(self):
        os.mkdir(self._dest)

        with open(os.path.join(self._dest, "index.rst"), "wb") as h:
            h.write("""
Python GObject Introspection Documentation
==========================================

.. toctree::
    :maxdepth: 2

""")

            gens = []
            gens.append(self._about_gen)
            if self._tutorial:
                gens.append(self._tutorial_gen)
            gens.append(self._api_gen)

            for gen in gens:
                if gen.is_empty():
                    continue
                gen.write()

                for n in gen.get_names():
                    h.write("    %s\n" % n)

        # copy the theme, conf.py
        dest_conf = os.path.join(self._dest, "conf.py")
        shutil.copy(os.path.join("data", self.CONF_IN), dest_conf)

        theme_dest = os.path.join(self._dest, self.THEME_DIR)
        shutil.copytree(os.path.join("data", self.THEME_DIR), theme_dest)

        ext_dest = os.path.join(self._dest, self.EXT_DIR)
        shutil.copytree(os.path.join("data", self.EXT_DIR), ext_dest)
