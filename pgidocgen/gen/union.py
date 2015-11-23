# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil
from .. import util


_main_template = genutil.get_template("""\
======
Unions
======

.. toctree::
    :maxdepth: 1

{% for union in unions %}
    {{ union.name }}
{% endfor %}

""")

_sub_template = genutil.get_template("""\
{{ "=" * union.fullname|length }}
{{ union.fullname }}
{{ "=" * union.fullname|length }}

.. _{{ union.fullname }}.fields:

Fields
------

{% if field_rows %}
.. csv-table::
    :header: "Name", "Type", "Access", "Description"
    :widths: 20, 1, 1, 100

    {% for row in field_rows %}
        {{ row|indent(4, False) }}
    {% endfor %}

{% else %}
None

{% endif %}


Methods
-------

{% if summary_rows %}
.. csv-table::
    :widths: 1, 100

    {% for row in summary_rows %}
        {{ row|indent(4, False) }}
    {% endfor %}

{% else %}
None

{% endif %}


Details
-------

.. class:: {{ union.fullname }}{{ union.signature }}

    {{ union.desc|indent(4, False) }}

    {% for method in union.get_methods(static=True) %}
    .. staticmethod:: {{ method.fullname }}{{ method.signature }}

        {{ method.desc|indent(8, False) }}

    {% endfor %}

    {% for method in union.get_methods(static=False) %}
    .. method:: {{ method.fullname }}{{ method.signature }}

        {{ method.desc|indent(8, False) }}

    {% endfor %}

""")


class UnionGenerator(genutil.Generator):

    def __init__(self):
        self._unions = set()

    def get_names(self):
        return ["unions/index"]

    def is_empty(self):
        return not bool(self._unions)

    def add_union(self, union):
        self._unions.add(union)

    def write(self, dir_):
        sub_dir = os.path.join(dir_, "unions")

        os.mkdir(sub_dir)

        unions = sorted(self._unions, key=lambda x: x.name)

        path = os.path.join(sub_dir, "index.rst")
        with open(path, "wb") as h:
            text = _main_template.render(unions=unions)
            h.write(text.encode("utf-8"))

        for union in unions:
            self._write_union(sub_dir, union)

    def _write_union(self, sub_dir, union):
        rst_path = os.path.join(sub_dir, union.name) + ".rst"

        methods = union.get_methods(static=True)
        methods += union.get_methods(static=False)

        summary_rows = []
        for func in methods:
            summary_rows.append(util.get_csv_line([
                "*static*" if func.is_static else "",
                ":py:func:`%s<%s>` %s" % (func.name, func.fullname,
                                          util.escape_rest(func.signature))]))

        field_rows = []
        for field in union.fields:
            field_rows.append(util.get_csv_line([
                field.name, field.type_desc, field.flags_string, field.desc]))

        with open(rst_path, "wb") as h:
            text = _sub_template.render(
                union=union,
                summary_rows=summary_rows,
                field_rows=field_rows)
            h.write(text.encode("utf-8"))
