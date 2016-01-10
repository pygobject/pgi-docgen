# -*- coding: utf-8 -*-
# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .namespace import get_namespace
from .overrides import parse_override_docs
from .parser import docstring_to_rest
from .docobj import Module


class Repository(object):
    """Takes gi objects and gives documentation objects"""

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        self._ns = ns = get_namespace(namespace, version)
        self._docs = ns.docs

        # merge all type mappings and doc references
        self._types = {}
        self._refs = {}
        self._type_structs = {}
        loaded = [ns] + [get_namespace(*x) for x in ns.all_dependencies]
        # prefer our own types in case there are conflicts
        # (not sure if there can be..)
        for sub_ns in reversed(loaded):
            self._types.update(sub_ns.types)
            self._refs.update(sub_ns.doc_references)
            self._type_structs.update(sub_ns.type_structs)

        # remove all references which look like C types, we handle them
        # separately and link the API doc version instead
        for k, v in self._refs.items():
            if k in self._types:
                del self._refs[k]

        self._overrides_docs = parse_override_docs(namespace, version)

    def _fix_docs(self, d, current=None):
        return docstring_to_rest(self, current, d or u"")

    def _lookup_docs(self, source, name, current=None):
        source = self._docs[source]
        if name in source:
            docs = source[name][0]
            return self._fix_docs(docs, current)
        return u""

    def parse(self):
        return Module.from_repo(self)

    def get_types(self):
        return self._types

    def get_docrefs(self):
        return self._refs

    def get_type_structs(self):
        return self._type_structs

    def lookup_override_docs(self, fullname):
        return self._overrides_docs.get(fullname, u"")

    def lookup_docs(self, type_, *args, **kwargs):
        docs = self._lookup_docs(type_, *args, **kwargs)
        if type_ == "all":
            shadowed = self._lookup_docs("all_shadowed", *args, **kwargs)
        else:
            shadowed = u""

        return docs, shadowed

    def lookup_meta(self, type_, fullname):
        source = self._docs[type_]

        if fullname in source:
            docs, version_added, dep_version, dep = source[fullname]
            dep = self._fix_docs(dep)
        else:
            version_added = dep_version = dep = u""

        return version_added, dep_version, dep

    def get_all_dependencies(self):
        return self._ns.all_dependencies

    def import_module(self):
        return self._ns.import_module()

    def get_source(self):
        return self._ns.source_map

    def is_private(self, name):
        """is_private('Gtk.ViewportPrivate')"""

        assert "." in name

        return name in self._ns.private
