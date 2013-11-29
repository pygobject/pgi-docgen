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

        # classes and aliases: GtkFooBar -> Gtk.FooBar
        for t in dom.getElementsByTagName("type"):
            local_name = t.getAttribute("name")
            c_name = t.getAttribute("c:type").rstrip("*")
            types[c_name] = local_name

        # gtk_main -> Gtk.main
        for t in dom.getElementsByTagName("function"):
            local_name = t.getAttribute("name")
            # Copy escaping from gi: Foo.break -> Foo.break_
            local_name = util.escape_keyword(local_name)
            namespace = t.parentNode.getAttribute("name")
            c_name = t.getAttribute("c:identifier")
            name = namespace + "." + local_name
            types[c_name] = name

        # gtk_dialog_get_response_for_widget ->
        #     Gtk.Dialog.get_response_for_widget
        elements = dom.getElementsByTagName("constructor")
        elements += dom.getElementsByTagName("method")
        for t in elements:
            local_name = t.getAttribute("name")
            # Copy escaping from gi: Foo.break -> Foo.break_
            local_name = util.escape_keyword(local_name)
            owner = t.parentNode.getAttribute("name")
            c_name = t.getAttribute("c:identifier")
            name = namespace + "." + owner + "." + local_name
            types[c_name] = name

        # enums etc. GTK_SOME_FLAG_FOO -> Gtk.SomeFlag.FOO
        for t in dom.getElementsByTagName("member"):
            parent = t.parentNode
            if parent.tagName == "bitfield" or parent.tagName == "enumeration":
                c_name = t.getAttribute("c:identifier")
                class_name = parent.getAttribute("name")
                field_name = t.getAttribute("name").upper()
                local_name = namespace + "." + class_name + "." + field_name
                types[c_name] = local_name

        # cairo_t -> cairo.Context
        for t in dom.getElementsByTagName("record"):
            c_name = t.getAttribute("c:type")
            type_name = t.getAttribute("name")
            types[c_name] = type_name

        # G_TIME_SPAN_MINUTE -> GLib.TIME_SPAN_MINUTE
        for t in dom.getElementsByTagName("constant"):
            c_name = t.getAttribute("c:type")
            if t.parentNode.tagName == "namespace":
                name = namespace + "." + t.getAttribute("name")
                types[c_name] = name

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
