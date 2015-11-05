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

    def __init__(self, repo):
        self.repo = repo

    def get_names(self):
        return ["mapping"]

    def is_empty(self):
        return False

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "mapping.rst")

        lines = []
        items = self.repo._types.iteritems()
        for key, values in sorted(items, key=lambda x: x[0].lower()):
            key = util.escape_rest(key)
            for value in values:
                if not value.startswith(self.repo.namespace + "."):
                    continue
                if self.repo.is_private(value):
                    continue
                value = util.escape_rest(value)
                line = util.get_csv_line([key, ":py:data:`%s`" % value])
                lines.append(line)

        with open(path, "wb") as h:
            text = _template.render(lines=lines)
            h.write(text.encode("utf-8"))
