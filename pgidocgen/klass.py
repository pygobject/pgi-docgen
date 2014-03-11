# Copyright 2013,2014 Christoph Reiter
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
    """For GObjects an GInterfaces"""

    def __init__(self):
        self._classes = {}  # cls -> code
        self._ifaces = {}
        self._methods = {}  # cls -> code
        self._vfuncs = {}
        self._props = {}  # cls -> [prop]
        self._sigs = {}  # cls -> [sig]

    def add_class(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._classes[obj] = code

    def add_interface(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._ifaces[obj] = code

    def add_method(self, cls_obj, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        if cls_obj in self._methods:
            self._methods[cls_obj].append((obj, code))
        else:
            self._methods[cls_obj] = [(obj, code)]

    def get_method_count(self, cls):
        return len(self._methods.get(cls, []))

    def add_vfunc(self, cls_obj, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        if cls_obj in self._vfuncs:
            self._vfuncs[cls_obj].append((obj, code))
        else:
            self._vfuncs[cls_obj] = [(obj, code)]

    def _get_inheritance_list(self, cls, type_, ref_suffix):
        bases = []
        for base in self.get_mro(cls)[1:]:
            num = len(type_.get(base, []))
            if num:
                name = base.__module__ + "." + base.__name__
                bases.append(
                    ":ref:`%s (%d)<%s.%s>`" % (name, num, name, ref_suffix))

        if bases:
            return """

:Inherited: %s

""" % ", ".join(bases)

    def add_properties(self, cls, props):
        assert cls not in self._props

        if props:
            self._props[cls] = props

    def add_signals(self, cls, sigs):
        assert cls not in self._sigs

        if sigs:
            self._sigs[cls] = sigs

    def get_names(self):
        names = []
        if self._classes:
            names.append("classes/index.rst")
        if self._ifaces:
            names.append("interfaces/index.rst")
        return names

    def is_empty(self):
        return not bool(self._classes) and not bool(self._ifaces)

    def get_mro(self, cls):
        return [c for c in cls.__mro__ if
                c in self._classes or c in self._ifaces]

    def write(self, dir_, module_fileobj):
        if self._ifaces:
            self._write(module_fileobj, os.path.join(dir_, "interfaces"),
                        self._ifaces, True)

        if self._classes:
            self._write(module_fileobj, os.path.join(dir_, "classes"),
                        self._classes, False)

    def _write(self, module_fileobj, sub_dir, classes, is_interface):

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

        sorter_classes = classes.keys()
        ranks = {}
        while not check_order(sorter_classes):
            for cls in classes:
                ranks[cls] = ranks.get(cls, 0) + get_key(sorter_classes, cls)
            sorter_classes.sort(key=lambda x: ranks[x])

        def indent(c):
            return "\n".join(["    %s" % l for l in c.splitlines()])

        os.mkdir(sub_dir)

        index_handle = open(os.path.join(sub_dir, "index.rst"), "wb")
        if is_interface:
            index_handle.write(util.make_rest_title("Interfaces") + "\n\n")
        else:
            index_handle.write(util.make_rest_title("Classes") + "\n\n")

        # add classes to the index toctree
        index_handle.write(".. toctree::\n    :maxdepth: 1\n\n")
        for cls in sorted(classes, key=lambda x: x.__name__):
            index_handle.write("""\
    %s
""" % cls.__name__)

        # write the code
        for cls in sorter_classes:
            module_fileobj.write(classes[cls])

            # sort static methods first, then by name
            def sort_func(e):
                return util.is_normalmethod(e[0]), e[0].__name__

            methods = self._methods.get(cls, [])[:]
            methods.sort(key=sort_func)

            vfuncs = self._vfuncs.get(cls, [])[:]
            vfuncs.sort(key=sort_func)

            methods.extend(vfuncs)

            for obj, code in methods:
                module_fileobj.write(indent(code) + "\n")

        # create a new file for each class
        for cls in classes:
            h = open(os.path.join(sub_dir, cls.__name__) + ".rst", "wb")
            cls_name = cls.__module__ + "." + cls.__name__
            h.write(util.make_rest_title(cls_name, "=") + "\n")

            # special case classes which don't inherit from any GI class
            # and are defined in the overrides:
            # e.g. Gtk.TreeModelRow
            if not util.is_iface(cls) and not util.is_object(cls):
                h.write("""
.. autoclass:: %s
    :members:
    :undoc-members:

""" % cls_name)
                continue

            # INHERITANCE DIAGRAM

            h.write("""
.. inheritance-diagram:: %s
""" % cls_name)

            # subclasses
            subclasses = cls.__subclasses__()
            if subclasses:
                if is_interface:
                    h.write("\n:Implementations:\n")
                else:
                    h.write("\n:Subclasses:\n")
                refs = []
                for sub in subclasses:
                    sub_name = sub.__module__ + "." + sub.__name__
                    refs.append(":class:`%s`" % sub_name)
                refs = sorted(set(refs))
                h.write("    " + ", ".join(refs))
                h.write("\n\n")

            # IMAGE
            if os.path.exists("data/clsimages/%s.png" % cls_name):
                h.write("""

Example
-------

.. image:: ../../../clsimages/%s.png

""" % cls_name)

            # METHODS

            h.write("""

.. _%s.methods:

Methods
-------

""" % cls_name)

            methods_inherited = self._get_inheritance_list(
                cls, self._methods, "methods")
            h.write(methods_inherited or "")

            methods = self._methods.get(cls, [])

            if not methods and not methods_inherited:
                h.write("None\n\n")

            if methods:
                h.write(".. autosummary::\n\n")

            # sort static methods first, then by name
            def sort_func(e):
                return util.is_normalmethod(e[0]), e[0].__name__
            methods.sort(key=sort_func)
            for obj, code in methods:
                h.write("    " + cls_name + "." + obj.__name__ + "\n")

            # VFUNC

            h.write("""

.. _%s.vfuncs:

Virtual Methods
---------------

""" % cls_name)

            vfun_inherited = self._get_inheritance_list(
                cls, self._vfuncs, "vfuncs")
            h.write(vfun_inherited or "")

            methods = self._vfuncs.get(cls, [])

            if not methods and not vfun_inherited:
                h.write("None\n\n")

            if methods:
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

            prop_inherited = self._get_inheritance_list(
                cls, self._props, "props")
            h.write(prop_inherited or "")

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

            if lines:
                h.write('''
.. csv-table::
    :header: "Name", "Type", "Flags", "Short Description"
    :widths: 1, 1, 1, 100

%s
    ''' % lines)

            if not lines and not prop_inherited:
                h.write("None\n\n")

            # SIGNALS

            h.write("""
.. _%s.sigs:

Signals
-------
""" % cls_name)

            sig_inherited = self._get_inheritance_list(
                cls, self._sigs, "sigs")
            h.write(sig_inherited or "")

            if cls in self._sigs:
                self._sigs[cls].sort(key=lambda s: s.name)

            lines = []
            for sig in self._sigs.get(cls, []):
                rst_target = cls_name + ".signals." + sig.name
                name_ref = ":ref:`%s<%s>`" % (sig.name, rst_target)
                line = get_csv_line([name_ref, sig.short_desc])
                lines.append("    %s" % line)
            lines = "\n".join(lines)

            if lines:
                h.write('''
.. csv-table::
    :header: "Name", "Short Description"
    :widths: 30, 70

%s
''' % lines)

            if not lines and not sig_inherited:
                h.write("None\n\n")

            # FIELDS

            # fields aren't common with GObjects, so only print the
            # header when some are there
            if self.has_fields(cls):
                self.write_field_table(cls, h)

            h.write("""
Class Details
-------------
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

            # SIGNAL details

            if cls in self._sigs:
                h.write(util.make_rest_title("Signal Details", "-"))

            for sig in self._sigs.get(cls, []):
                rst_label = cls_name + ".signals." + sig.name
                data = """

.. _%s:

.. py:function:: %s

    :Signal Name: ``%s``
    :Flags: %s

%s

""" % (rst_label, sig.sig, sig.name, sig.flags_string, util.indent(sig.desc))

                h.write(data.encode("utf-8"))

            # PROPERTY details

            if cls in self._props:
                h.write(util.make_rest_title("Property Details", "-"))

            for p in self._props.get(cls, []):
                rest_target = cls_name + ".props." + p.attr_name
                data = """

.. py:data:: %s

    :Name: ``%s``
    :Type: %s
    :Flags: %s

%s

""" % (rest_target, p.name, p.type_desc, p.flags_string, util.indent(p.desc))

                h.write(data.encode("utf-8"))

            h.close()

        index_handle.close()
