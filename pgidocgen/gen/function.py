# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil

from .. import util


_template = genutil.get_template("""\
{% import '.genutil.UTIL' as util %}
=========
Functions
=========

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

{% if functions %}
    {% for function in functions %}
.. function:: {{ function.fullname }}{{ function.signature }}

    {{ function.signature_desc|indent(4, False) }}

    {{ util.render_info(function.info)|indent(4, False) }}

    {% endfor %}
{% else %}
None

{% endif %}
""")


class FunctionGenerator(genutil.Generator):

    def __init__(self):
        self._funcs = set()

    def get_names(self):
        return ["functions"]

    def is_empty(self):
        return not bool(self._funcs)

    def add_function(self, func):
        self._funcs.add(func)

    def write(self, dir_):
        path = os.path.join(dir_, "functions.rst")

        functions = sorted(self._funcs, key=lambda f: f.name)

        summary_rows = []
        for func in functions:
            summary_rows.append(util.get_csv_line([
                "",
                ":py:func:`%s<%s>` %s" % (func.name, func.fullname,
                                          util.escape_rest(func.signature))]))

        with open(path, "wb") as h:
            text = _template.render(
                functions=functions,
                summary_rows=summary_rows)
            h.write(text.encode("utf-8"))
