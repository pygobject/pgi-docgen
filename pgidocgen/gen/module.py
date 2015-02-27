# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import types
import inspect
import shutil
from urllib2 import urlopen, URLError, HTTPError

from .klass import ClassGenerator
from .flags import FlagsGenerator
from .constants import ConstantsGenerator
from .function import FunctionGenerator
from .enum import EnumGenerator
from .structures import StructGenerator
from .union import UnionGenerator
from .callback import CallbackGenerator
from .hierarchy import HierarchyGenerator
from .mapping import MappingGenerator
from . import genutil

from ..doap import get_project_summary
from ..namespace import get_namespace
from ..repo import Repository
from .. import util, BASEDIR


_template = genutil.get_template("""\
{{ "=" * title|length }}
{{ title }}
{{ "=" * title|length }}

{{ project_summary }}

API
---

.. toctree::
    :maxdepth: 1

    {% for name in names %}
    {{ name }}
    {% endfor %}

""")


def _import_dependency(fobj, namespace, version):
    """Import the module in the generated code"""

    fobj.write("import pgi\n")
    fobj.write("pgi.set_backend('ctypes,null')\n")
    fobj.write("pgi.require_version('%s', '%s')\n" % (namespace, version))
    fobj.write("from pgi.repository import %s\n" % namespace)

    # this needs to be synced with Namespace.import_module
    if namespace in ("Clutter", "ClutterGst", "Gst", "Grl"):
        fobj.write("%s.init([])\n" % namespace)
    elif namespace in ("Gsf", "IBus"):
        fobj.write("%s.init()\n" % namespace)


class ModuleGenerator(genutil.Generator):

    THEME_DIR = "theme"
    CLSIMG_DIR = "clsimages"
    EXT_DIR = "ext"
    CONF_IN = "conf.in.py"

    def __init__(self):
        self._modules = []

    def get_names(self):
        names = []
        for namespace, version in self._modules:
            nick = "%s_%s" % (namespace, version)
            names.append(nick + "/index")
        return names

    def add_module(self, namespace, version):
        self._modules.append((namespace, version))

    def is_empty(self):
        return not bool(self._modules)

    def write(self, dir_, target_, devhelp=False):
        try:
            os.mkdir(dir_)
        except OSError:
            pass

        def get_to_write(dir_, namespace, version):
            """Returns a list of modules to write.

            Traverses the dependencies and stops if a module
            build directory is found, skipping it and all its deps.
            """

            mods = []
            nick = "%s-%s" % (namespace, version)
            sub_dir = os.path.join(dir_, nick)
            if os.path.exists(sub_dir):
                return mods
            mods.append((namespace, version))

            ns = get_namespace(namespace, version)
            for dep in ns.get_dependencies():
                mods.extend(get_to_write(dir_, *dep))

            return mods

        mods = []
        for namespace, version in self._modules:
            mods.extend(get_to_write(dir_, namespace, version))
        mods = set(mods)

        for namespace, version in mods:
            nick = "%s-%s" % (namespace, version)
            sub_dir = os.path.join(dir_, nick)
            self._write(sub_dir, target_, namespace, version, devhelp)

    def _write(self, sub_dir, target_, namespace, version, devhelp):
        if os.path.exists(sub_dir):
            print "skipping %s-%s, already exists" % (namespace, version)
            return

        os.mkdir(sub_dir)
        dir_ = sub_dir
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

        repo = Repository(namespace, version)
        mod = repo.import_module()

        for dep in repo.get_dependencies():
            _import_dependency(module, *dep)

        class_gen = ClassGenerator(repo)
        flags_gen = FlagsGenerator()
        enums_gen = EnumGenerator()
        func_gen = FunctionGenerator()
        struct_gen = StructGenerator()
        union_gen = UnionGenerator()
        const_gen = ConstantsGenerator()
        cb_gen = CallbackGenerator()
        hier_gen = HierarchyGenerator()
        map_gen = MappingGenerator(repo)

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

                if obj.__module__.split(".")[-1] != namespace:
                    print "Skipping %s: originated from other namespace" % key
                    continue

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
                        hier_gen.add_class(obj)
                        class_gen.add_class(obj, code)
                    else:
                        class_gen.add_interface(obj, code)

                    props = repo.parse_properties(obj)
                    class_gen.add_properties(obj, props)

                    props = repo.parse_child_properties(obj)
                    class_gen.add_child_properties(obj, props)

                    props = repo.parse_style_properties(obj)
                    class_gen.add_style_properties(obj, props)

                    sigs = repo.parse_signals(obj)
                    class_gen.add_signals(obj, sigs)

                    fields = repo.parse_fields(obj)
                    class_gen.add_fields(obj, fields)

                    methods = repo.parse_methods(obj)
                    class_gen.add_methods(obj, methods)

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
                    # don't include GError
                    if not issubclass(obj, BaseException):
                        hier_gen.add_class(obj)

                    # classes not subclassing from any gobject base class
                    if util.is_fundamental(obj):
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
            project_summary = get_project_summary(".", namespace, version)
            names = []
            gens = [func_gen, cb_gen, class_gen, hier_gen, struct_gen,
                    union_gen, flags_gen, enums_gen, const_gen, map_gen]
            for gen in gens:
                if gen.is_empty():
                    continue
                for name in gen.get_names():
                    names.append(name)
                gen.write(sub_dir, module)

            text = _template.render(
                title=title, project_summary=project_summary, names=names)
            h.write(text.encode("utf-8"))

        module.close()

        # make sure the generated code is valid python
        with open(module.name, "rb") as h:
            exec h.read() in {}

        conf_path = os.path.join(dir_, "_pgi_docgen_conf.py")
        deps = ["-".join(d) for d in repo.get_all_dependencies()]
        with open(conf_path, "wb") as conf:
            conf.write("""
DEPS = %r
TARGET = %r
DEVHELP_PREFIX = %r
""" % (deps, os.path.abspath(target_), devhelp and "python-" or ""))

        # make sure the generated config
        with open(conf_path, "rb") as h:
            exec h.read() in {}

        # download external objects.inv for intersphinx and cache them in
        # SOURCE/_intersphinx
        extern_intersphinx = {
            "python": "http://docs.python.org/2.7",
            "cairo": "http://cairographics.org/documentation/pycairo/2",
        }

        isph_path = os.path.join(os.path.dirname(sub_dir), "_intersphinx")
        try:
            os.mkdir(isph_path)
        except OSError:
            pass

        for name, url in extern_intersphinx.items():
            inv_path = os.path.join(isph_path, name + ".inv")
            if os.path.exists(inv_path):
                continue

            try:
                inv_url = url + "/objects.inv"
                print "..loading %r" % inv_url
                h = urlopen(inv_url)
                with open(inv_path, "wb") as f:
                    f.write(h.read())
            except (HTTPError, URLError) as e:
                print "ERROR: %r" % e

        # copy the theme, conf.py
        dest_conf = os.path.join(dir_, "conf.py")
        shutil.copy(os.path.join(BASEDIR, "data", self.CONF_IN), dest_conf)

        theme_dest = os.path.join(dir_, "_" + self.THEME_DIR)
        shutil.copytree(
            os.path.join(BASEDIR, "data", self.THEME_DIR), theme_dest)

        ext_dest = os.path.join(dir_, "_" + self.EXT_DIR)
        shutil.copytree(os.path.join(BASEDIR, "data", self.EXT_DIR), ext_dest)

        module_id = "%s-%s" % (namespace, version)
        clsimg_src = os.path.join(BASEDIR, "data", self.CLSIMG_DIR, module_id)
        if os.path.exists(clsimg_src):
            clsimg_dest = os.path.join(dir_, "_" + self.CLSIMG_DIR)
            shutil.copytree(clsimg_src, clsimg_dest)
