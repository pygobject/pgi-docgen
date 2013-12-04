# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


class ClassGenerator(util.Generator):
    """Base class for GObjects an GInterfaces"""

    DIR_NAME = ""
    HEADLINE = ""

    def __init__(self, dir_, module_fileobj):
        self._sub_dir = os.path.join(dir_, self.DIR_NAME)
        self.path = os.path.join(self._sub_dir, "index.rst")

        self._classes = {}  # cls -> code
        self._methods = {}  # cls -> code
        self._props = {}  # cls -> code
        self._sigs = {}  # cls -> code

        self._module = module_fileobj

    def add_class(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._classes[obj] = code

    def add_method(self, cls_obj, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        if cls_obj in self._methods:
            self._methods[cls_obj].append((obj, code))
        else:
            self._methods[cls_obj] = [(obj, code)]

    def add_properties(self, cls, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._props[cls] = code

    def add_signals(self, cls, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._sigs[cls] = code

    def get_names(self):
        return [os.path.join(self.DIR_NAME, "index.rst")]

    def is_empty(self):
        return not bool(self._classes)

    def write(self):
        classes = self._classes.keys()

        # try to get the right order, so all bases are defined
        # this probably isn't right...
        def check_order(cls):
            for c in cls:
                for b in util.merge_in_overrides(c):
                    if b in cls and cls.index(b) > cls.index(c):
                        return False
            return True

        def get_key(cls, c):
            i = 0
            for b in util.merge_in_overrides(c):
                if b not in cls:
                    continue
                if cls.index(b) > cls.index(c):
                    i += 1
            return i

        ranks = {}
        while not check_order(classes):
            for cls in classes:
                ranks[cls] = ranks.get(cls, 0) + get_key(classes, cls)
            classes.sort(key=lambda x: ranks[x])

        def indent(c):
            return "\n".join(["    %s" % l for l in c.splitlines()])

        os.mkdir(self._sub_dir)

        index_handle = open(self.path, "wb")
        index_handle.write(util.make_rest_title(self.HEADLINE) + "\n\n")

        # add classes to the index toctree
        index_handle.write(".. toctree::\n    :maxdepth: 1\n\n")
        for cls in sorted(classes, key=lambda x: x.__name__):
            index_handle.write("""\
    %s
""" % cls.__name__)

        # write the code
        for cls in classes:
            self._module.write(self._classes[cls])
            methods = self._methods.get(cls, [])

            # sort static methods first, then by name
            def sort_func(e):
                return not util.method_is_static(e[0]), e[0].__name__
            methods.sort(key=sort_func)
            for obj, code in methods:
                self._module.write(indent(code) + "\n")

        # create a new file for each class
        for cls in classes:
            h = open(os.path.join(self._sub_dir, cls.__name__) + ".rst", "wb")
            name = cls.__module__ + "." + cls.__name__
            title = name
            h.write(util.make_rest_title(title, "=") + "\n")

            h.write("""
.. inheritance-diagram:: %s
""" % name)

            h.write("""
Methods
-------

""")

            methods = self._methods.get(cls, [])
            if not methods:
                h.write("None\n\n")
            else:
                h.write(".. autosummary::\n\n")

            # sort static methods first, then by name
            def sort_func(e):
                return not util.method_is_static(e[0]), e[0].__name__
            methods.sort(key=sort_func)
            for obj, code in methods:
                h.write("    " + cls.__module__ + "." + cls.__name__ +
                        "." + obj.__name__ + "\n")

            h.write("""
Properties
----------
""")
            h.write(self._props.get(cls, "") or "None\n\n")

            h.write("""
Signals
-------
""")
            h.write(self._sigs.get(cls, "") or "None\n\n")

            h.write("""
Details
-------
""")

            if util.is_base(cls):
                h.write("""
.. autoclass:: %s
    :members:
    :undoc-members:
""" % name)
            else:
                h.write("""
.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
""" % name)

            h.close()

        index_handle.close()


class GObjectGenerator(ClassGenerator):
    DIR_NAME = "classes"
    HEADLINE = "Classes"


class InterfaceGenerator(ClassGenerator):
    DIR_NAME = "interfaces"
    HEADLINE = "Interfaces"
