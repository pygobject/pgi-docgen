# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
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

from ..namespace import get_namespace
from ..repo import Repository


_template = genutil.get_template("""\
{{ "=" * title|length }}
{{ title }}
{{ "=" * title|length }}

{% if ps %}
{% if ps.name %}
:Parent Project:
    {{ ps.name|erest|indent(4, False) }}
{% endif %}
{% if ps.description %}
:Description:
    {{ ps.description|erest|indent(4, False) }}
{% endif %}
{% if ps.homepage %}
:Homepage:
    `{{ ps.homepage|erest }} <{{ ps.homepage }}>`__
{% endif %}
{% if ps.bugtracker %}
:Bug Tracker:
    `{{ ps.bugtracker|erest }} <{{ ps.bugtracker }}>`__
{% endif %}
{% if ps.repositories %}
:Repositories:
    {% for name, url in ps.repositories %}
    | `{{ name|erest }} <{{ url }}>`__
    {% endfor %}
{% endif %}
{% if ps.mailinglists %}
:Mailing Lists:
    {% for name, url in ps.mailinglists %}
    | `{{ name|erest }} <{{ url }}>`__
    {% endfor %}
{% endif %}
{% endif %}

API
---

.. toctree::
    :maxdepth: 1

    {% for name in names %}
    {{ name }}
    {% endfor %}

""")


class ModuleGenerator(object):

    def __init__(self, namespace, version):
        self._namespace = namespace
        self._version = version

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

        mods = set(get_to_write(dir_, self._namespace, self._version))
        for namespace, version in mods:
            nick = "%s-%s" % (namespace, version)
            sub_dir = os.path.join(dir_, nick)
            self._write(sub_dir, namespace, version)

    def _write(self, sub_dir, namespace, version):
        if os.path.exists(sub_dir):
            print "%s-%s: skipping, already exists" % (namespace, version)
            return

        print "%s-%s: building..." % (namespace, version)

        os.mkdir(sub_dir)
        dir_ = sub_dir

        module = Repository(namespace, version).parse()

        class_gen = ClassGenerator()
        for klass in module.classes:
            class_gen.add_class(klass)
        for klass in module.pyclasses:
            class_gen.add_pyclass(klass)

        flags_gen = FlagsGenerator()
        for flags in module.flags:
            flags_gen.add_flags(flags)

        enums_gen = EnumGenerator()
        for enum in module.enums:
            enums_gen.add_enum(enum)

        func_gen = FunctionGenerator()
        for func in module.functions:
            func_gen.add_function(func)

        struct_gen = StructGenerator("structs", "Structures")
        for struct in module.structures:
            struct_gen.add_struct(struct)

        class_struct_gen = StructGenerator("class-structs", "Class Structures")
        for struct in module.class_structures:
            class_struct_gen.add_struct(struct)

        iface_struct_gen = StructGenerator("iface-structs",
                                           "Interface Structures")
        for struct in module.iface_structures:
            iface_struct_gen.add_struct(struct)

        union_gen = UnionGenerator()
        for union in module.unions:
            union_gen.add_union(union)

        const_gen = ConstantsGenerator()
        for const in module.constants:
            const_gen.add_constant(const)

        cb_gen = CallbackGenerator()
        for callback in module.callbacks:
            cb_gen.add_callback(callback)

        hier_gen = HierarchyGenerator()
        hier_gen.set_hierarchy(module.hierarchy)

        map_gen = MappingGenerator()
        map_gen.set_mapping(module.symbol_mapping)

        with open(os.path.join(sub_dir, "index.rst"),  "wb") as h:

            title = "%s %s" % (namespace, version)
            if module.library_version:
                title += " (%s)" % module.library_version
  
            names = []
            gens = [func_gen, cb_gen, class_gen, hier_gen, struct_gen,
                    class_struct_gen, iface_struct_gen,
                    union_gen, flags_gen, enums_gen, const_gen, map_gen]
            for gen in gens:
                if gen.is_empty():
                    continue
                for name in gen.get_names():
                    names.append(name)
                gen.write(sub_dir)

            text = _template.render(
                title=title, ps=module.project_summary, names=names)
            h.write(text.encode("utf-8"))

        conf_path = os.path.join(dir_, "conf_data.py")
        deps = ["-".join(d) for d in module.dependencies]
        with open(conf_path, "wb") as conf:
            conf.write("DEPS = %r\n" % deps)
            # for sphinx.ext.linkcode
            conf.write("SOURCEURLS = %r\n" % module.symbol_mapping.source_map)
            # for the sidebar index
            conf.write("LIB_VERSION = %r\n" % module.library_version)

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
                h = urlopen(inv_url)
                with open(inv_path, "wb") as f:
                    f.write(h.read())
            except (HTTPError, URLError) as e:
                print "ERROR: %r" % e

        data_dir = genutil.get_data_dir()

        # copy the theme, conf.py
        dest_conf = os.path.join(dir_, "conf.py")
        shutil.copy(os.path.join(data_dir, "conf.in.py"), dest_conf)

        theme_dest = os.path.join(dir_, "_theme")
        shutil.copytree(os.path.join(data_dir, "theme"), theme_dest)

        ext_dest = os.path.join(dir_, "_ext")
        shutil.copytree(os.path.join(data_dir, "ext"), ext_dest)
