# -*- coding: utf-8 -*-
# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import jinja2

from .namespace import get_namespace
from .parser import docstring_to_rest
from .docobj import Module


class Repository(object):
    """Produces and provides information for documentation objects"""

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version
        self.missed_links = 0

        self._ns = ns = get_namespace(namespace, version)

        loaded = [ns] + [get_namespace(*x) for x in ns.all_dependencies]
        self._namespaces = loaded

        self._rst_env = jinja2.Environment(undefined=jinja2.StrictUndefined)

    def parse(self):
        """Returns a Module instance containing the whole documentation tree"""

        # import the right versions first so we don't have to pass the version
        # in from now on

        self.import_module()
        return Module.from_repo(self)

    def render_override_docs(self, text, **kwargs):
        return self._rst_env.from_string(text).render(**kwargs)

    def lookup_override_docs(self, fullname):
        for ns in self._namespaces:
            if fullname in ns.override_docs:
                return ns.override_docs[fullname]
        return u""

    def lookup_py_id(self, c_id, shadowed=True):
        """Given a C identifier will return a Python identifier which
        exposes the underlying type/function/etc or None in case the C
        identifier isn't known.

        if shadowed is True and the c_id is shadowed will return the
        Python id of the shadowing function instead.

        e.g. "GtkWidget" -> "Gtk.Widget"
        """

        py_id = self.lookup_all_py_id(c_id, shadowed)
        if py_id:
            return py_id[0]

    def lookup_all_py_id(self, c_id, shadowed=True):
        """Given a C identifier will return a list of Python identifier which
        expose the underlying type/function/etc or an empty list in case the C
        identifier isn't known or it isn't exposed in Python.

        e.g. "GtkWidget" -> ["Gtk.Widget"]
        """

        if shadowed:
            shadowed_c_id = self.get_shadowed(c_id)
            if shadowed_c_id is not None:
                c_id = shadowed_c_id

        for ns in self._namespaces:
            if c_id in ns.types:
                return ns.types[c_id]
        return []

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

    def _lookup_docs(self, type_, name, current_type=None, current_func=None):
        for ns in self._namespaces:
            source = ns.docs[type_]
            if name in source:
                return docstring_to_rest(self, source[name].docs,
                                         current_type, current_func)
        return u""

    def lookup_docs(self, type_, *args, **kwargs):
        docs = self._lookup_docs(type_, *args, **kwargs)
        if type_ == "all":
            shadowed = self._lookup_docs("all_shadowed", *args, **kwargs)
        else:
            shadowed = u""

        return docs, shadowed

    def lookup_meta(self, type_, fullname):
        for ns in self._namespaces:
            source = ns.docs[type_]

            if fullname in source:
                docs, version_added, dep_version, dep = source[fullname]
                dep = docstring_to_rest(self, dep)
                return version_added, dep_version, dep

        return u"", u"", u""

    def lookup_instance_param(self, py_id):
        """Returns the name of the instance parameter for the Python identifier
        or None.
        """

        for ns in self._namespaces:
            if py_id in ns.instance_params:
                return ns.instance_params[py_id]

    def get_shadowed(self, c_id):
        for ns in self._namespaces:
            if c_id in ns.shadow_map:
                return ns.shadow_map[c_id]

    def is_private(self, py_id):
        """Returns True if a Python type is considered private i.e. should
        not be included in the documentation in any way.

        e.g. is_private('Gtk.ViewportPrivate') -> True
        """

        for ns in self._namespaces:
            if py_id in ns.private:
                return True
        return False

    def get_all_dependencies(self):
        """Returns a list of (namespace, version) tuples for all transitive
        dependencies.
        """

        return self._ns.all_dependencies

    def get_dependencies(self):
        """Returns a list of (namespace, version) tuples for all direct
        dependencies.
        """

        return self._ns.dependencies

    def import_module(self):
        """Imports and returns the Python module.

        Can raise ImportError.
        """

        return self._ns.import_module()

    def get_source_map(self):
        """Returns a dict mapping C symbols to an external url showing
        the code of that symbol.

        e.g. "g_idle_add" ->
            https://gitlab.gnome.org/GNOME/glib/blob/2.46.2/glib/gmain.c#L5538
        """

        return self._ns.source_map

    def get_types(self):
        return self._ns.types
