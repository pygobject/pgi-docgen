# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from xml.dom import minidom

from . import util


class Namespace(object):

    _doms = {}
    _types = {}

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        key = namespace + version

        if key not in self._doms:
            self._doms[key] = self._parse_dom()
        self._dom = self._doms[key]

        if not key in self._types:
            self._types[key] = self._parse_types()
        self.types = self._types[key]

    def _parse_dom(self):
        print "Parsing GIR: %s-%s" % (self.namespace, self.version)
        return minidom.parse(self.get_path())

    def _parse_types(self):
        """Create a mapping of various C names to python names"""

        dom = self.get_dom()
        namespace = self.namespace
        types = {}

        def add(c_name, py_name):
            if c_name in types:
                old_count = types[c_name].count(".")
                new_count = py_name.count(".")
                # prefer static methods over functions
                if old_count > new_count:
                    return
                else:
                    assert types[c_name] == py_name, (types[c_name], py_name)

            # escape each potential attribute
            py_name = ".".join(
                map(util.escape_identifier,  py_name.split(".")))
            types[c_name] = py_name

        # {key of the to be replaces function: c def of the replacement}
        shadowed = {}

        # gtk_main -> Gtk.main
        # gtk_dialog_get_response_for_widget ->
        #     Gtk.Dialog.get_response_for_widget
        elements = dom.getElementsByTagName("function")
        elements += dom.getElementsByTagName("constructor")
        elements += dom.getElementsByTagName("method")
        for t in elements:
            shadows = t.getAttribute("shadows")
            local_name = t.getAttribute("name")
            c_name = t.getAttribute("c:identifier")
            assert c_name

            # Copy escaping from gi: Foo.break -> Foo.break_
            full_name = local_name
            parent = t.parentNode
            while parent.getAttribute("name"):
                full_name = parent.getAttribute("name") + "." + full_name
                parent = parent.parentNode

            if shadows:
                shadowed_name = ".".join(full_name.split(".")[:-1] + [shadows])
                shadowed_name = ".".join(
                    map(util.escape_identifier, shadowed_name.split(".")))
                shadowed[shadowed_name] = c_name

            add(c_name, full_name)

        # enums etc. GTK_SOME_FLAG_FOO -> Gtk.SomeFlag.FOO
        for t in dom.getElementsByTagName("member"):
            c_name = t.getAttribute("c:identifier")
            assert c_name
            class_name = t.parentNode.getAttribute("name")
            field_name = t.getAttribute("name").upper()
            local_name = namespace + "." + class_name + "." + field_name
            add(c_name, local_name)

        # classes
        elements = dom.getElementsByTagName("class")
        elements += dom.getElementsByTagName("interface")
        elements += dom.getElementsByTagName("enumeration")
        elements += dom.getElementsByTagName("bitfield")
        elements += dom.getElementsByTagName("callback")
        elements += dom.getElementsByTagName("union")
        elements += dom.getElementsByTagName("alias")
        for t in elements:
            # only top level
            if t.parentNode.tagName != "namespace":
                continue

            c_name = t.getAttribute("c:type")
            c_name = c_name or t.getAttribute("glib:type-name")

            # e.g. GObject _Value__data__union
            if not c_name:
                continue

            type_name = t.getAttribute("name")
            add(c_name, namespace + "." + type_name)

        # cairo_t -> cairo.Context
        for t in dom.getElementsByTagName("record"):
            c_name = t.getAttribute("c:type")
            assert c_name
            type_name = t.getAttribute("name")
            add(c_name, namespace + "." + type_name)

        # G_TIME_SPAN_MINUTE -> GLib.TIME_SPAN_MINUTE
        for t in dom.getElementsByTagName("constant"):
            c_name = t.getAttribute("c:type")
            if t.parentNode.tagName == "namespace":
                name = namespace + "." + t.getAttribute("name")
                add(c_name, name)

        # the keys we want to replace have should exist
        assert not (set(shadowed.keys()) - set(types.values()))

        # make c defs which are replaced point to the key of the replacement
        # so that: "gdk_threads_add_timeout_full" -> Gdk.threads_add_timeout
        for c_name, name in types.items():
            if name in shadowed:
                replacement = shadowed[name]
                types[replacement] = name

        if namespace == "GObject":
            # these come from overrides and aren't in the gir
            # e.g. G_TYPE_INT -> GObject.TYPE_INT
            from gi.repository import GObject
            type_keys = [k for k in dir(GObject) if k.startswith("TYPE_")]
            assert "TYPE_INT" in type_keys
            for key in type_keys:
                types["G_" + key] = "GObject." + key

            types["GBoxed"] = "GObject.GBoxed"

        return types

    def get_path(self):
        return "/usr/share/gir-1.0/%s-%s.gir" % (self.namespace, self.version)

    def get_dom(self):
        return self._dom

    def get_dependencies(self):
        dom = self.get_dom()
        deps = []
        for include in dom.getElementsByTagName("include"):
            name = include.getAttribute("name")
            version = include.getAttribute("version")
            deps.append((name, version))
        return deps
