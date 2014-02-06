# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util
from .fields import FieldsMixin
from .util import get_csv_line


class ClassGenerator(util.Generator, FieldsMixin):
    """Base class for GObjects an GInterfaces"""

    DIR_NAME = ""
    HEADLINE = ""

    def __init__(self, dir_, module_fileobj):
        self._sub_dir = os.path.join(dir_, self.DIR_NAME)
        self.path = os.path.join(self._sub_dir, "index.rst")

        self._classes = {}  # cls -> code
        self._methods = {}  # cls -> code
        self._props = {}  # cls -> [prop]
        self._sigs = {}  # cls -> [sig]

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

    def add_properties(self, cls, props):
        assert cls not in self._props

        if props:
            self._props[cls] = props

    def add_signals(self, cls, sigs):
        assert cls not in self._sigs

        if sigs:
            self._sigs[cls] = sigs

    def get_names(self):
        return [self.DIR_NAME + "/index.rst"]

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
                return util.is_normalmethod(e[0]), e[0].__name__
            methods.sort(key=sort_func)
            for obj, code in methods:
                self._module.write(indent(code) + "\n")

        # create a new file for each class
        for cls in classes:
            h = open(os.path.join(self._sub_dir, cls.__name__) + ".rst", "wb")
            cls_name = cls.__module__ + "." + cls.__name__
            h.write(util.make_rest_title(cls_name, "=") + "\n")

            # INHERITANCE DIAGRAM

            h.write("""
.. inheritance-diagram:: %s
""" % cls_name)

            # subclasses
            subclasses = cls.__subclasses__()
            if subclasses:
                h.write("\n:Subclasses:\n")
                refs = []
                for sub in subclasses:
                    sub_name = sub.__module__ + "." + sub.__name__
                    refs.append(":class:`%s`" % sub_name)
                refs = sorted(set(refs))
                h.write("    " + ", ".join(refs))
                h.write("\n\n")

            # METHODS

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
                return util.is_normalmethod(e[0]), e[0].__name__
            methods.sort(key=sort_func)
            for obj, code in methods:
                h.write("    " + cls_name + "." + obj.__name__ + "\n")

            # PROPERTIES

            h.write("""
.. _%s.props:

Properties
----------
""" % cls_name)

            # sort props by name
            if cls in self._props:
                self._props[cls].sort(key=lambda p: p.name)

            lines = []
            for p in self._props.get(cls, []):
                fstr = p.flags_string
                rst_target = cls_name + ".props." + p.attr_name
                name = ":py:data:`%s<%s>`" % (p.name, rst_target)
                line = get_csv_line([name, p.type_desc, fstr, p.short_desc])
                lines.append("    %s" % line)
            lines = "\n".join(lines)

            if not lines:
                h.write("None\n\n")
            else:
                h.write('''
.. csv-table::
    :header: "Name", "Type", "Flags", "Short Description"
    :widths: 1, 1, 1, 100

%s
    ''' % lines)

            # SIGNALS

            h.write("""
.. _%s.sigs:

Signals
-------
""" % cls_name)

            if cls in self._sigs:
                self._sigs[cls].sort(key=lambda s: s.name)

            lines = []
            for sig in self._sigs.get(cls, []):
                rst_target = cls_name + ".signals." + sig.name
                name_ref = ":ref:`%s<%s>`" % (sig.name, rst_target)
                line = get_csv_line([name_ref, sig.short_desc])
                lines.append("    %s" % line)
            lines = "\n".join(lines)

            if not lines:
                h.write("None\n\n")
            else:
                h.write('''
.. csv-table::
    :header: "Name", "Short Description"
    :widths: 30, 70

%s
''' % lines)

            # fields aren't common with GObjects, so only print the
            # header when some are there
            if self.has_fields(cls):
                self.write_field_table(cls, h)

            h.write("""
Details
-------
""")

            if util.is_base(cls):
                h.write("""
.. autoclass:: %s
    :members:
    :undoc-members:
""" % cls_name)
            else:
                h.write("""
.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
""" % cls_name)

            if cls in self._sigs:
                h.write(util.make_rest_title("Signal Details", "-"))

            for sig in self._sigs.get(cls, []):
                rst_label = cls_name + ".signals." + sig.name
                h.write("""

.. _%s:

.. py:function:: %s(...)
    :noindex:

    :Parameters: %s
    :Return Value: %s

%s
""" % (rst_label, sig.name, sig.params, sig.ret, util.indent(sig.desc)))

            if cls in self._props:
                h.write(util.make_rest_title("Property Details", "-"))

            for p in self._props.get(cls, []):
                rest_target = cls_name + ".props." + p.attr_name
                h.write("""

.. py:data:: %s

    :Name: ``%s``
    :Type: %s
    :Flags: %s
%s
""" % (rest_target, p.name, p.type_desc, p.flags_string, util.indent(p.desc)))

            h.close()

        index_handle.close()


class GObjectGenerator(ClassGenerator):
    DIR_NAME = "classes"
    HEADLINE = "Classes"


class InterfaceGenerator(ClassGenerator):
    DIR_NAME = "interfaces"
    HEADLINE = "Interfaces"
