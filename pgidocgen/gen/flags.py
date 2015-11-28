# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil


_template = genutil.get_template("""\
{% import '.genutil.UTIL' as util %}
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

    {{ util.render_info(entry.info)|indent(4, False) }}

    {% for value in entry.values %}
    .. attribute:: {{ value.name }}
        :annotation: = {{ value.value }}

        {{ util.render_info(value.info)|indent(8, False) }}

    {% endfor %}

    {% endfor %}
{% else %}
None

{% endif %}
""")


class FlagsGenerator(genutil.Generator):

    def __init__(self):
        self._flags = set()

    def add_flags(self, flags):
        self._flags.add(flags)

    def get_names(self):
        return ["flags"]

    def is_empty(self):
        return not bool(self._flags)

    def write(self, dir_):
        path = os.path.join(dir_, "flags.rst")

        flags = sorted(self._flags, key=lambda x: x.name)

        with open(path, "wb") as h:
            text = _template.render(entries=flags)
            h.write(text.encode("utf-8"))
