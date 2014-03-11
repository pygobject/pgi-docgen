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


class ModuleGenerator(util.Generator):

    def __init__(self, dir_, namespace, version):
        # create the basic package structure
        self.namespace = namespace
        self.version = version

        nick = "%s_%s" % (namespace, version)
        self._index_name = nick + "/index"
        self._module_path = os.path.join(dir_, nick)

    def get_names(self):
        return [self._index_name]

    def _add_dependency(self, module, name, version):
        """Import the module in the generated code"""
        module.write("import pgi\n")
        module.write("pgi.set_backend('ctypes,null')\n")
        module.write("pgi.require_version('%s', '%s')\n" % (name, version))
        module.write("from pgi.repository import %s\n" % name)

    def write(self, *args):

        namespace, version = self.namespace, self.version

        os.mkdir(self._module_path)
        module_path = os.path.join(self._module_path, namespace + ".py")
        module = open(module_path, "wb")

        # utf-8 encoded .py
        module.write("# -*- coding: utf-8 -*-\n")
        # for references to the real module
        self._add_dependency(module, namespace, version)
        # basic deps
        self._add_dependency(module, "GObject", "2.0")
        self._add_dependency(module, "Gio", "2.0")
        self._add_dependency(module, "GLib", "2.0")
        self._add_dependency(module, "Atk", "1.0")

        mod = util.import_namespace(namespace, version)
        repo = Repository(namespace, version)

        for dep in repo.get_dependencies():
            self._add_dependency(module, *dep)

        class_gen = ClassGenerator(self._module_path)
        flags_gen = FlagsGenerator(self._module_path)
        enums_gen = EnumGenerator(self._module_path)
        func_gen = FunctionGenerator(self._module_path)
        struct_gen = StructGenerator(self._module_path)
        union_gen = UnionGenerator(self._module_path)
        const_gen = ConstantsGenerator(self._module_path)
        cb_gen = CallbackGenerator(self._module_path)

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

                    code = repo.parse_class(name, obj, add_bases=True)
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

                    code = repo.parse_class(name, obj, add_bases=True)

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
                    # classes defined in overrides
                    code = repo.parse_class(name, obj)
                    if code:
                        class_gen.add_class(obj, code)
            else:
                code = repo.parse_constant(name)
                if code:
                    const_gen.add_constant(name, code)

        with open(os.path.join(self._module_path, "index.rst"),  "wb") as h:

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
                gen.write(module)

        module.close()

        # make sure the generated code is valid python
        with open(module.name, "rb") as h:
            exec h.read() in {}
