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
{{ "=" * title|length }}
{{ title }}
{{ "=" * title|length }}

.. toctree::
    :maxdepth: 1

{% for struct in structures %}
    {{ struct.name }}
{% endfor %}

""")

_sub_template = genutil.get_template("""\
{% import '.genutil.UTIL' as util %}
{{ "=" * struct.fullname|length }}
{{ struct.fullname }}
{{ "=" * struct.fullname|length }}

.. _{{ struct.fullname }}.fields:

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

.. _{{ struct.fullname }}.methods:

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

.. class:: {{ struct.fullname }}{{ struct.signature }}

    {{ util.render_info(struct.info)|indent(4, False) }}

    {% for method in struct.get_methods(static=True) %}
    .. staticmethod:: {{ method.fullname }}{{ method.signature }}

        {{ method.signature_desc|indent(8, False) }}

        {{ util.render_info(method.info)|indent(8, False) }}

    {% endfor %}

    {% for method in struct.get_methods(static=False) %}
    .. method:: {{ method.fullname }}{{ method.signature }}

        {{ method.signature_desc|indent(8, False) }}

        {{ util.render_info(method.info)|indent(8, False) }}

    {% endfor %}

""")


class StructGenerator(genutil.Generator):

    def __init__(self, key, title):
        self._key = key
        self._title = title
        self._structs = set()

    def get_names(self):
        return ["%s/index" % self._key]

    def is_empty(self):
        return not bool(self._structs)

    def add_struct(self, struct):
        self._structs.add(struct)

    def write(self, dir_):
        sub_dir = os.path.join(dir_, self._key)

        os.mkdir(sub_dir)

        structs = sorted(self._structs, key=lambda x: x.name)

        path = os.path.join(sub_dir, "index.rst")
        with open(path, "wb") as h:
            text = _main_template.render(structures=structs, title=self._title)
            h.write(text.encode("utf-8"))

        for struct in structs:
            self._write_struct(sub_dir, struct)

    def _write_struct(self, sub_dir, struct):
        rst_path = os.path.join(sub_dir, struct.name) + ".rst"

        methods = struct.get_methods(static=True)
        methods += struct.get_methods(static=False)

        summary_rows = []
        for func in methods:
            summary_rows.append(util.get_csv_line([
                "*static*" if func.is_static else "",
                ":py:obj:`%s<%s>` %s" % (func.name, func.fullname,
                                         util.escape_rest(func.signature))]))

        field_rows = []
        for field in struct.fields:
            field_rows.append(util.get_csv_line([
                field.name, field.type_desc, field.flags_string,
                field.info.desc]))

        with open(rst_path, "wb") as h:
            text = _sub_template.render(
                struct=struct,
                summary_rows=summary_rows,
                field_rows=field_rows)
            h.write(text.encode("utf-8"))
