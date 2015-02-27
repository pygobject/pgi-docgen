# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil


_template = genutil.get_template("""\
=========
Functions
=========

{% if names %}
.. autosummary::

    {% for name in names %}
    {{ name }}
    {% endfor %}

{% else %}
None

{% endif %}

Details
-------

{% if names %}
    {% for name in names %}
.. autofunction:: {{ name }}

    {% endfor %}
{% else %}
None

{% endif %}
""")


class FunctionGenerator(genutil.Generator):

    def __init__(self):
        self._funcs = {}

    def get_names(self):
        return ["functions"]

    def is_empty(self):
        return not bool(self._funcs)

    def add_function(self, name, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._funcs[name] = code

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "functions.rst")
        func_names, func_codes = zip(*sorted(self._funcs.items()))

        with open(path, "wb") as h:
            text = _template.render(names=func_names)
            h.write(text.encode("utf-8"))

        for code in func_codes:
            module_fileobj.write(code)
