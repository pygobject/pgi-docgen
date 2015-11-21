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
import json
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
from ..girdata import get_source_to_url_func, get_project_version
from ..repo import Repository
from .. import util


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


def get_hierarchy(type_seq):
    """Returns for a sequence of classes a recursive dict including
    all their sub classes.
    """

    def first_mro(obj):
        l = [obj]
        bases = util.fake_bases(obj)
        if bases[0] is not object:
            l.extend(first_mro(bases[0]))
        return l

    tree = {}
    for type_ in type_seq:
        current = tree
        for base in reversed(first_mro(type_)):
            if base not in current:
                current[base] = {}
            current = current[base]
    return tree


def to_names(hierarchy):

    def get_name(cls):
        return cls.__module__ + "." + cls.__name__

    return sorted(
            [(get_name(k), to_names(v)) for (k, v) in hierarchy.iteritems()])


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

    def write(self, dir_):
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
            self._write(sub_dir, namespace, version)

    def _write(self, sub_dir, namespace, version):
        if os.path.exists(sub_dir):
            print "skipping %s-%s, already exists" % (namespace, version)
            return

        os.mkdir(sub_dir)
        dir_ = sub_dir

        repo = Repository(namespace, version)
        mod = repo.import_module()
        lib_version = get_project_version(mod)

        class_gen = ClassGenerator()
        flags_gen = FlagsGenerator()
        enums_gen = EnumGenerator()
        func_gen = FunctionGenerator()
        struct_gen = StructGenerator()
        union_gen = UnionGenerator()
        const_gen = ConstantsGenerator()
        cb_gen = CallbackGenerator()
        hier_gen = HierarchyGenerator()
        map_gen = MappingGenerator(repo)

        hierarchy_classes = set()
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

                if util.is_callback(obj):
                    func = repo.parse_function(namespace, obj)
                    cb_gen.add_callback(func)
                else:
                    func = repo.parse_function(namespace, obj)
                    func_gen.add_function(func)
            elif inspect.isclass(obj):
                if util.is_object(obj) or util.is_iface(obj):
                    klass = repo.parse_class(obj)
                    if not klass.is_interface:
                        hierarchy_classes.add(obj)
                    class_gen.add_class(klass)
                elif util.is_flags(obj):
                    flags = repo.parse_flags(obj)
                    flags_gen.add_flags(obj, flags)
                elif util.is_enum(obj):
                    enum = repo.parse_enum(obj)
                    enums_gen.add_enum(obj, enum)
                elif util.is_struct(obj):
                    struct = repo.parse_structure(obj)
                    # Hide private structs
                    if repo.is_private(struct.fullname):
                        continue
                    struct_gen.add_struct(struct)
                elif util.is_union(obj):
                    union = repo.parse_union(obj)
                    union_gen.add_union(union)
                else:
                    # don't include GError
                    if not issubclass(obj, BaseException):
                        hierarchy_classes.add(obj)

                    # classes not subclassing from any gobject base class
                    if util.is_fundamental(obj):
                        klass = repo.parse_class(obj)
                        class_gen.add_class(klass)
                    else:
                        klass = repo.parse_pyclass(obj)
                        class_gen.add_pyclass(klass)
            else:
                const = repo.parse_constant(namespace, key, obj)
                const_gen.add_constant(const)

        hierarchy = to_names(get_hierarchy(hierarchy_classes))
        hier_gen.set_hierarchy(hierarchy)

        with open(os.path.join(sub_dir, "index.rst"),  "wb") as h:

            title = "%s %s" % (namespace, version)
            if lib_version:
                title += " (%s)" % lib_version
            project_summary = get_project_summary(namespace)
            names = []
            gens = [func_gen, cb_gen, class_gen, hier_gen, struct_gen,
                    union_gen, flags_gen, enums_gen, const_gen, map_gen]
            for gen in gens:
                if gen.is_empty():
                    continue
                for name in gen.get_names():
                    names.append(name)
                gen.write(sub_dir)

            text = _template.render(
                title=title, project_summary=project_summary, names=names)
            h.write(text.encode("utf-8"))

        # for sphinx.ext.linkcode
        url_map = {}
        func = get_source_to_url_func(namespace, lib_version)
        if func:
            source = repo.get_source()
            for key, value in source.iteritems():
                url_map[key] = func(value)

        conf_path = os.path.join(dir_, "_pgi_docgen_conf.py")
        deps = ["-".join(d) for d in repo.get_all_dependencies()]
        with open(conf_path, "wb") as conf:
            conf.write("DEPS = %r\n" % deps)
            conf.write("SOURCEURLS = %r\n" % url_map)

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
        shutil.copy(
            os.path.join(util.BASEDIR, "data", self.CONF_IN), dest_conf)

        theme_dest = os.path.join(dir_, "_" + self.THEME_DIR)
        shutil.copytree(
            os.path.join(util.BASEDIR, "data", self.THEME_DIR), theme_dest)

        ext_dest = os.path.join(dir_, "_" + self.EXT_DIR)
        shutil.copytree(
            os.path.join(util.BASEDIR, "data", self.EXT_DIR), ext_dest)

        module_id = "%s-%s" % (namespace, version)
        clsimg_src = os.path.join(
            util.BASEDIR, "data", self.CLSIMG_DIR, module_id)
        if os.path.exists(clsimg_src):
            clsimg_dest = os.path.join(dir_, "_" + self.CLSIMG_DIR)
            shutil.copytree(clsimg_src, clsimg_dest)
