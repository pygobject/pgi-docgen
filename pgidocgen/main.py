# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import shutil

from .api import APIGenerator
from . import util


class MainGenerator(util.Generator):
    """Creates the sphinx environment and the index page"""

    THEME_DIR = "theme"
    STOCK_DIR = "stockicons"
    CLSIMG_DIR = "clsimages"
    EXT_DIR = "ext"
    CONF_IN = "conf.in.py"

    def __init__(self):
        self._api_gen = APIGenerator()

    def add_module(self, *args):
        self._api_gen.add_module(*args)

    def is_empty(self):
        self._api_gen.is_empty()

    def write(self, dir_, *args):
        os.mkdir(dir_)

        with open(os.path.join(dir_, "index.rst"), "wb") as h:
            h.write("""
Index
=====

.. toctree::
    :maxdepth: 1

""")

            gens = [self._api_gen]
            for gen in gens:
                if gen.is_empty():
                    continue
                gen.write(dir_)

                for n in gen.get_names():
                    h.write("    %s\n" % n)

        # copy the theme, conf.py
        dest_conf = os.path.join(dir_, "conf.py")
        shutil.copy(os.path.join("data", self.CONF_IN), dest_conf)

        theme_dest = os.path.join(dir_, self.THEME_DIR)
        shutil.copytree(os.path.join("data", self.THEME_DIR), theme_dest)

        ext_dest = os.path.join(dir_, self.EXT_DIR)
        shutil.copytree(os.path.join("data", self.EXT_DIR), ext_dest)

        stock_dest = os.path.join(dir_, self.STOCK_DIR)
        shutil.copytree(os.path.join("data", self.STOCK_DIR), stock_dest)

        clsimg_dest = os.path.join(dir_, self.CLSIMG_DIR)
        shutil.copytree(os.path.join("data", self.CLSIMG_DIR), clsimg_dest)
