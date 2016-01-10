# -*- coding: utf-8 -*-
# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .namespace import get_namespace
from .parser import docstring_to_rest
from .docobj import Module


class Repository(object):
    """Produces and provides information for documentation objects"""

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        self._ns = ns = get_namespace(namespace, version)

        # merge all type mappings and doc references
        self._types = {}
        loaded = [ns] + [get_namespace(*x) for x in ns.all_dependencies]
        self._namespaces = loaded

        # prefer our own types in case there are conflicts
        # (not sure if there can be..)
        for sub_ns in reversed(self._namespaces):
            self._types.update(sub_ns.types)

    def parse(self):
        """Returns a Module instance containing the whole documentation tree"""

        return Module.from_repo(self)

    def lookup_py_id(self, c_id):
        """Given a C identifier will return a Python identifier which
        exposes the underlying type/function/etc or None in case the C
        identifier isn't known.

        e.g. "GtkWidget" -> "Gtk.Widget"
        """

        for ns in self._namespaces:
            if c_id in ns.types:
                return ns.types[c_id][0]

    def lookup_gtkdoc_ref(self, doc_ref):
        """Given a gtk-doc reference will try to find an URL to external
        resources. If none is found returns None.

        e.g. "gtk-x11" ->
            "https://developer.gnome.org/gtk3/stable/gtk-x11.html#gtk-x11""
        """

        for ns in self._namespaces:
            if doc_ref in ns.doc_references:
                # We don't want to give out URLs for things we should
                # have locally.
                assert self.lookup_py_id(doc_ref) is None
                return ns.doc_references[doc_ref]

    def lookup_py_id_for_type_struct(self, struct_c_id):
        """Given a C identifier of a type struct returns the Python ID
        of the corresponding Python type. Returns None if none was found.

        e.g. GObjectClass -> GObject.Object
        """

        for ns in self._namespaces:
            if struct_c_id in ns.type_structs:
                return ns.type_structs[struct_c_id]

    def _lookup_docs(self, type_, name, current=None):
        source = self._ns.docs[type_]
        if name in source:
            return docstring_to_rest(self, current, source[name].docs)
        return u""

    def lookup_docs(self, type_, *args, **kwargs):
        docs = self._lookup_docs(type_, *args, **kwargs)
        if type_ == "all":
            shadowed = self._lookup_docs("all_shadowed", *args, **kwargs)
        else:
            shadowed = u""

        return docs, shadowed

    def lookup_meta(self, type_, fullname):
        source = self._ns.docs[type_]

        if fullname in source:
            docs, version_added, dep_version, dep = source[fullname]
            dep = docstring_to_rest(self, "", dep)
        else:
            version_added = dep_version = dep = u""

        return version_added, dep_version, dep

    def get_all_dependencies(self):
        """Returns a list of (namespace, version) tuples for all transitive
        dependencies.
        """

        return self._ns.all_dependencies

    def import_module(self):
        """Imports and returns the Python module.

        Can raise ImportError.
        """

        return self._ns.import_module()

    def get_source(self):
        return self._ns.source_map

    def get_types(self):
        return self._types

    def is_private(self, py_id):
        """Returns True if a Python type is considered private i.e. should
        not be included in the documentation in any way.

        e.g. is_private('Gtk.ViewportPrivate') -> True
        """

        return py_id in self._ns.private
