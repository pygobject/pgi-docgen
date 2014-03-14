# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import types
import inspect

from .klass import ClassGenerator
from .flags import FlagsGenerator
from .constants import ConstantsGenerator
from .function import FunctionGenerator
from .enum import EnumGenerator
from .repo import Repository
from .structures import StructGenerator
from .union import UnionGenerator
from .callback import CallbackGenerator
from .doap import get_project_summary
from . import util


def _import_dependency(fobj, namespace, version):
    """Import the module in the generated code"""

    fobj.write("import pgi\n")
    fobj.write("pgi.set_backend('ctypes,null')\n")
    fobj.write("pgi.require_version('%s', '%s')\n" % (namespace, version))
    fobj.write("from pgi.repository import %s\n" % namespace)

    # this needs to be synced with util.import_namespace
    if namespace in ("Clutter", "ClutterGst", "Gst", "Grl"):
        fobj.write("%s.init([])\n" % namespace)
    elif namespace in ("Gsf", "IBus"):
        fobj.write("%s.init()\n" % namespace)


class ModuleGenerator(util.Generator):

    def __init__(self):
        self._modules = []

    def get_names(self):
        names = []
        for namespace, version in self._modules:
            nick = "%s_%s" % (namespace, version)
            names.append(nick + "/index")
        return names

    def add_module(self, namespace, version):

        # XXX: we bind all attributes here so the class hierarchy is created
        # and cls.__subclasses__() works in each ModuleGenerator
        # even across namespaces
        mod = util.import_namespace(namespace, version)
        for key in dir(mod):
            getattr(mod, key, None)

        self._modules.append((namespace, version))

    def is_empty(self):
        return not bool(self._modules)

    def write(self, dir_, *args):
        for namespace, version in self._modules:
            nick = "%s_%s" % (namespace, version)
            sub_dir = os.path.join(dir_, nick)
            self._write(sub_dir, namespace, version)

    def _write(self, sub_dir, namespace, version):
        os.mkdir(sub_dir)
        module_path = os.path.join(sub_dir, namespace + ".py")
        module = open(module_path, "wb")

        # utf-8 encoded .py
        module.write("# -*- coding: utf-8 -*-\n")
        # for references to the real module
        _import_dependency(module, namespace, version)
        # basic deps
        _import_dependency(module, "GObject", "2.0")
        _import_dependency(module, "Gio", "2.0")
        _import_dependency(module, "GLib", "2.0")
        _import_dependency(module, "Atk", "1.0")

        mod = util.import_namespace(namespace, version)
        repo = Repository(namespace, version)

        for dep in repo.get_dependencies():
            _import_dependency(module, *dep)

        class_gen = ClassGenerator()
        flags_gen = FlagsGenerator()
        enums_gen = EnumGenerator()
        func_gen = FunctionGenerator()
        struct_gen = StructGenerator()
        union_gen = UnionGenerator()
        const_gen = ConstantsGenerator()
        cb_gen = CallbackGenerator()

        for key in dir(mod):
            if key.startswith("_"):
                continue
            obj = getattr(mod, key)

            # skip classes which are renamed
            if inspect.isclass(obj):
                if obj.__name__ != key:
                    print "Skipping %s: renamed class" % key
                    continue
                if obj.__module__.split(".")[-1] != namespace:
                    print "Skipping %s: originated from other namespace" % key
                    continue

            name = "%s.%s" % (namespace, key)

            if isinstance(obj, types.FunctionType):
                if hasattr(obj, "_is_callback"):
                    code = repo.parse_function(name, None, obj)
                    cb_gen.add_callback(obj, code)
                else:
                    code = repo.parse_function(name, None, obj)
                    if code:
                        func_gen.add_function(name, code)
            elif inspect.isclass(obj):
                if util.is_iface(obj) or util.is_object(obj):

                    code = repo.parse_class(name, obj)
                    if util.is_object(obj):
                        class_gen.add_class(obj, code)
                    else:
                        class_gen.add_interface(obj, code)

                    props = repo.parse_properties(obj)
                    class_gen.add_properties(obj, props)

                    sigs = repo.parse_signals(obj)
                    class_gen.add_signals(obj, sigs)

                    fields = repo.parse_fields(obj)
                    class_gen.add_fields(obj, fields)

                    for attr, attr_obj in util.iter_public_attr(obj):
                        # can fail for the base class
                        try:
                            if not util.is_method_owner(obj, attr):
                                continue
                        except NotImplementedError:
                            continue

                        if callable(attr_obj):
                            if not util.is_virtualmethod(attr_obj):
                                func_key = name + "." + attr
                                code = repo.parse_function(
                                    func_key, obj, attr_obj)
                                if code:
                                    class_gen.add_method(obj, attr_obj, code)
                            else:
                                func_key = name + "." + attr
                                code = repo.parse_function(
                                    func_key, obj, attr_obj)
                                if code:
                                    class_gen.add_vfunc(obj, attr_obj, code)

                elif util.is_flags(obj):
                    code = repo.parse_flags(name, obj)
                    flags_gen.add_flags(obj, code)
                elif util.is_enum(obj):
                    code = repo.parse_flags(name, obj)
                    enums_gen.add_enum(obj, code)
                elif util.is_struct(obj) or util.is_union(obj):
                    # Hide private structs
                    if repo.is_private(namespace + "." + obj.__name__):
                        continue

                    code = repo.parse_class(name, obj)

                    if util.is_struct(obj):
                        gen = struct_gen
                        struct_gen.add_struct(obj, code)
                    else:
                        gen = union_gen
                        union_gen.add_union(obj, code)

                    fields = repo.parse_fields(obj)
                    gen.add_fields(obj, fields)

                    for attr, attr_obj in util.iter_public_attr(obj):
                        try:
                            if not util.is_method_owner(obj, attr):
                                continue
                        except NotImplementedError:
                            continue

                        if callable(attr_obj):
                            func_key = name + "." + attr
                            code = repo.parse_function(func_key, obj, attr_obj)
                            if code:
                                gen.add_method(obj, attr_obj, code)
                else:
                    # classes not subclassing from any gobject base class

                    if util.is_paramspec(obj):
                        # param specs are special, treat it as a GObject
                        code = repo.parse_class(name, obj)
                        if code:
                            class_gen.add_class(obj, code)
                    else:
                        code = repo.parse_custom_class(name, obj)
                        if code:
                            class_gen.add_class(obj, code, py_class=True)
            else:
                code = repo.parse_constant(name)
                if code:
                    const_gen.add_constant(name, code)

        with open(os.path.join(sub_dir, "index.rst"),  "wb") as h:

            title = "%s %s" % (namespace, version)
            h.write(util.make_rest_title(title) + "\n\n")

            summary = get_project_summary(".", namespace, version)
            h.write(summary.encode("utf-8") + "\n\n")

            h.write(util.make_rest_title("API", "-") + "\n")

            h.write("""
.. toctree::
    :maxdepth: 1

""")

            gens = [func_gen, cb_gen, class_gen, struct_gen,
                    union_gen, flags_gen, enums_gen, const_gen]
            for gen in gens:
                if gen.is_empty():
                    continue
                for name in gen.get_names():
                    h.write("    %s\n" % name)
                gen.write(sub_dir, module)

        module.close()

        # make sure the generated code is valid python
        with open(module.name, "rb") as h:
            exec h.read() in {}
