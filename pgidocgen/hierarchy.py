# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


_template = util.get_template("""\
=========
Hierarchy
=========

{% for name, children in names recursive %}
{{ ""|indent(loop.depth0 * 2, true) }}* :class:`{{ name }}`
{% if children %}

{{ loop(children) }}
{% endif %}
{% endfor %}

{% if not names %}
None
{% endif %}

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


class HierarchyGenerator(util.Generator):

    _FILENAME = "hierarchy"

    def __init__(self):
        self._classes = set()

    def get_names(self):
        return [self._FILENAME]

    def is_empty(self):
        return not bool(self._classes)

    def add_class(self, class_obj):

        self._classes.add(class_obj)

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "%s.rst" % self._FILENAME)
        hierarchy = get_hierarchy(self._classes)
        names = to_names(hierarchy)

        with open(path, "wb") as h:
            text = _template.render(names=names)
            h.write(text.encode("utf-8"))
