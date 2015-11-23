# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil


_template = genutil.get_template("""\
=====
Flags
=====

{% if entries %}
    {% for entry in entries %}
* :class:`{{ entry.fullname }}`
    {% endfor %}

{% else %}
None

{% endif %}

Details
-------

{% if entries %}
    {% for entry in entries %}
.. class:: {{ entry.fullname }}()

    Bases: :class:`GObject.GFlags`

    {{ entry.desc|indent(4, False) }}

    {% for value in entry.values %}
    .. attribute:: {{ value.name }}
        :annotation: = {{ value.value }}

        {{ value.desc|indent(8, False) }}

    {% endfor %}

    {% endfor %}
{% else %}
None

{% endif %}
""")


class FlagsGenerator(genutil.Generator):

    def __init__(self):
        self._flags = {}

    def add_flags(self, flags):
        self._flags[flags.fullname] = flags

    def get_names(self):
        return ["flags"]

    def is_empty(self):
        return not bool(self._flags)

    def write(self, dir_):
        path = os.path.join(dir_, "flags.rst")

        flags = self._flags.values()
        flags.sort(key=lambda x: x.name)

        with open(path, "wb") as h:
            text = _template.render(entries=flags)
            h.write(text.encode("utf-8"))
