# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil


_template = genutil.get_template("""\
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


class HierarchyGenerator(genutil.Generator):

    _FILENAME = "hierarchy"

    def __init__(self):
        self._hierarchy = []

    def get_names(self):
        return [self._FILENAME]

    def is_empty(self):
        return not bool(self._hierarchy)

    def set_hierarchy(self, hierarchy):
        self._hierarchy = hierarchy

    def write(self, dir_):
        path = os.path.join(dir_, "%s.rst" % self._FILENAME)

        with open(path, "wb") as h:
            text = _template.render(names=self._hierarchy)
            h.write(text.encode("utf-8"))
