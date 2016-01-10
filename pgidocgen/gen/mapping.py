# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil

from .. import util


_template = genutil.get_template("""\
==============
Symbol Mapping
==============

{% for line in lines %}
    {% if loop.index0 is divisibleby(80) or loop.first %}

.. csv-table::
    :header: "C", "Python"
    :widths: 1, 99

    {% endif %}
    {{ line }}
{% endfor %}

""")


class MappingGenerator(genutil.Generator):

    def __init__(self):
        self._mapping = None

    def set_mapping(self, mapping):
        self._mapping = mapping

    def get_names(self):
        return ["mapping"]

    def is_empty(self):
        return not bool(self._mapping)

    def write(self, dir_):
        path = os.path.join(dir_, "mapping.rst")

        lines = []
        for key, url, value in self._mapping.symbol_map:
            value = util.escape_rest(value)
            if url:
                key = "`%s <%s>`__" % (util.escape_rest(key), url)
            else:
                key = util.escape_rest(key)
            line = util.get_csv_line(
                [key, ":py:data:`%s`" % value if value else ""])
            lines.append(line)

        with open(path, "wb") as h:
            text = _template.render(lines=lines)
            h.write(text.encode("utf-8"))
