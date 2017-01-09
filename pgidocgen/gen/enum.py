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
Enums
=====

{% if enums %}
    {% for enum in enums %}
* :class:`{{ enum.fullname }}`
    {% endfor %}

{% else %}
None

{% endif %}

Details
-------

{% if enums %}
    {% for enum in enums %}
.. class:: {{ enum.fullname }}{{ enum.signature }}

    {% if enum.base %}
    Bases: :class:`{{ enum.base }}`
    {% endif %}

    {{ util.render_info(enum.info)|indent(4, False) }}

    {% for method in enum.get_methods(static=True) %}
    .. classmethod:: {{ method.name }}{{ method.signature }}

        {{ method.signature_desc|indent(8, False) }}

        {{ util.render_info(method.info)|indent(8, False) }}

    {% endfor %}

    {% for method in enum.get_methods(static=False) %}
    .. method:: {{ method.name }}{{ method.signature }}

        {{ method.signature_desc|indent(8, False) }}

        {{ util.render_info(method.info)|indent(8, False) }}

    {% endfor %}

    {% for value in enum.values %}
    .. attribute:: {{ value.name }}
        :annotation: = {{ value.value }}

        {{ util.render_info(value.info)|indent(8, False) }}

    {% endfor %}

    {% endfor %}
{% else %}
None

{% endif %}
""")


class EnumGenerator(genutil.Generator):

    def __init__(self):
        self._enums = set()

    def add_enum(self, enum):
        self._enums.add(enum)

    def get_names(self):
        return ["enums"]

    def is_empty(self):
        return not bool(self._enums)

    def write(self, dir_):
        path = os.path.join(dir_, "enums.rst")

        enums = sorted(self._enums, key=lambda x: x.name)

        with open(path, "wb") as h:
            text = _template.render(enums=enums)
            h.write(text.encode("utf-8"))
