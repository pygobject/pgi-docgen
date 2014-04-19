# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


def get_hierarchy(type_seq):

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


def to_rest_listing(hier):

    def get_reference(obj):
        return ":class:`%s`" % (obj.__module__ + "." + obj.__name__)

    lines = []
    for cls, children in sorted(hier.items(), key=repr):
        lines.append("* " + get_reference(cls))
        subs = to_rest_listing(children)
        if subs:
            lines.append("")
            lines.append(util.indent(subs, 2))
            lines.append("")

    return "\n".join(lines)


class HierarchyGenerator(util.Generator):

    def __init__(self):
        self._classes = set()

    def get_names(self):
        return ["hierarchy"]

    def is_empty(self):
        return not bool(self._classes)

    def add_class(self, class_obj):

        self._classes.add(class_obj)

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "hierarchy.rst")
        hierarchy = get_hierarchy(self._classes)

        with open(path, "wb") as handle:
            handle.write("""
Hierarchy
=========

%s
""" % to_rest_listing(hierarchy))
