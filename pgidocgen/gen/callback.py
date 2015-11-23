# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil

from .. import util


_template = genutil.get_template(u"""\
=========
Callbacks
=========

{% if summary_rows %}
.. csv-table::
    :widths: 1, 99

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

    {{ function.desc|indent(4, False) }}

    {% endfor %}
{% else %}
None

{% endif %}

""")


class CallbackGenerator(genutil.Generator):

    def __init__(self):
        self._callbacks = set()

    def add_callback(self, func):
        self._callbacks.add(func)

    def get_names(self):
        return ["callbacks"]

    def is_empty(self):
        return not bool(self._callbacks)

    def write(self, dir_):
        path = os.path.join(dir_, "callbacks.rst")

        functions = sorted(self._callbacks, key=lambda f: f.name)

        summary_rows = []
        for func in functions:
            summary_rows.append(util.get_csv_line([
                "",
                ":py:func:`%s<%s>` %s" % (func.name, func.fullname,
                                          util.escape_rest(func.signature))]))

        text = _template.render(
            functions=functions,
            summary_rows=summary_rows)

        with open(path, "wb") as h:
            h.write(text.encode("utf-8"))
