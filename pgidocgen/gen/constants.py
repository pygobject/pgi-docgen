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
Constants
=========

{% if names %}
    {% for name in names %}
* :obj:`{{ name }}`
    {% endfor %}

{% else %}
None

{% endif %}

Details
-------

{% if names %}
    {% for name in names %}
.. autodata:: {{ name }}

    {% endfor %}
{% else %}
None

{% endif %}
""")


class ConstantsGenerator(genutil.Generator):

    def __init__(self):
        self._consts = {}

    def add_constant(self, name, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._consts[name] = code

    def get_names(self):
        return ["constants"]

    def is_empty(self):
        return not bool(self._consts)

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "constants.rst")

        names = self._consts.keys()
        names.sort()

        with open(path, "wb") as h:
            text = _template.render(names=names)
            h.write(text.encode("utf-8"))

        for name in names:
            code = self._consts[name]
            module_fileobj.write(code + "\n")
