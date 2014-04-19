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

    def __init__(self, repo):
        self._classes = {}  # cls -> code
        self._ifaces = {}
        self._methods = {}  # cls -> [methods]
        self._props = {}  # cls -> [prop]
        self._sigs = {}  # cls -> [sig]
        self._py_class = set()

        self.repo = repo

    def add_class(self, obj, code, py_class=False):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._classes[obj] = code
        if py_class:
            self._py_class.add(obj)

    def add_interface(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._ifaces[obj] = code

    def add_methods(self, cls_obj, methods):
        assert cls_obj not in self._methods

        self._methods[cls_obj] = methods

    def _get_inheritance_list(self, cls, ref_suffix):
        if ref_suffix == "methods":
            cfunc = self.repo.get_method_count
        elif ref_suffix == "vfuncs":
            cfunc = self.repo.get_vfunc_count
        elif ref_suffix == "props":
            cfunc = self.repo.get_property_count
        elif ref_suffix == "sigs":
            cfunc = self.repo.get_signal_count
        elif ref_suffix == "fields":
            cfunc = self.repo.get_field_count
        else:
            assert 0

        bases = []
        for base in util.fake_mro(cls):
            if base is object or base is cls:
                continue
            num = cfunc(base)
            if num:
                name = base.__module__ + "." + base.__name__
                bases.append(
                    ":ref:`%s (%d)<%s.%s>`" % (name, num, name, ref_suffix))

        if bases:
            return """

:Inherited: %s

""" % ", ".join(bases)
        else:
            return

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
        if self._ifaces:
            names.append("interfaces/index.rst")
        if self._classes:
            names.append("classes/index.rst")
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
        for cls in classes:
            module_fileobj.write(classes[cls])

            methods = self._methods.get(cls, [])

            def method_sort_key(m):
                return not m.is_vfunc, not m.is_static, m.name

            for method in sorted(methods, key=method_sort_key):
                code = method.code
                if not isinstance(code, bytes):
                    code = code.encode("utf-8")
                module_fileobj.write(util.indent(code) + "\n")

        # create a new file for each class
        for cls in classes:
            h = open(os.path.join(sub_dir, cls.__name__) + ".rst", "wb")
            cls_name = cls.__module__ + "." + cls.__name__
            h.write(util.make_rest_title(cls_name, "=") + "\n")

            # special case classes which don't inherit from any GI class
            # and are defined in the overrides:
            # e.g. Gtk.TreeModelRow, GObject.ParamSpec
            if cls in self._py_class:
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

            # SUBCLASSES
            subclasses = []
            for sub in cls.__subclasses__():
                # don't include things we happened to import
                if sub not in self._classes and sub not in self._ifaces:
                    continue
                subclasses.append(sub)

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
            image_path = os.path.join(
                "data", "clsimages", "%s-%s" % (
                    self.repo.namespace, self.repo.version),
                "%s.png" % cls_name)
            if os.path.exists(image_path):
                h.write("""

Example
-------

.. image:: ../_clsimages/%s.png

""" % cls_name)

            # METHODS

            h.write("""

.. _%s.methods:

Methods
-------

""" % cls_name)

            methods_inherited = self._get_inheritance_list(cls, "methods")
            h.write(methods_inherited or "")

            methods = self._methods.get(cls, [])
            methods = [m for m in methods if not m.is_vfunc]

            if not methods and not methods_inherited:
                h.write("None\n\n")

            if methods:
                h.write(".. autosummary::\n\n")

            # sort static methods first, then by name
            def sort_func(m):
                return not m.is_static, m.name

            for method in sorted(methods, key=sort_func):
                h.write("    " + cls_name + "." + method.name + "\n")

            # VFUNC

            h.write("""

.. _%s.vfuncs:

Virtual Methods
---------------

""" % cls_name)

            vfun_inherited = self._get_inheritance_list(cls, "vfuncs")
            h.write(vfun_inherited or "")

            methods = self._methods.get(cls, [])
            methods = [m for m in methods if m.is_vfunc]

            if not methods and not vfun_inherited:
                h.write("None\n\n")

            if methods:
                h.write(".. autosummary::\n\n")

            # sort static methods first, then by name
            def sort_func(m):
                return not m.is_static, m.name

            for method in sorted(methods, key=sort_func):
                h.write("    " + cls_name + "." + method.name + "\n")

            # PROPERTIES

            if util.is_object(cls) or util.is_iface(cls):
                h.write("""
.. _%s.props:

Properties
----------
""" % cls_name)

                prop_inherited = self._get_inheritance_list(cls, "props")
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

                sig_inherited = self._get_inheritance_list(cls, "sigs")
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
            fields_inherited = self._get_inheritance_list(cls, "fields")
            self.write_field_table(cls, h, fields_inherited)

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
