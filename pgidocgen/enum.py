# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


_template = util.get_template("""\
=====
Enums
=====

{% if names %}
    {% for name in names %}
* :class:`{{ name }}`
    {% endfor %}

{% else %}
None

{% endif %}

Details
-------

{% if names %}
    {% for name in names %}
.. autoclass:: {{ name }}
    :show-inheritance:
    :members:
    :undoc-members:
    :private-members:

    {% endfor %}
{% else %}
None

{% endif %}
""")


class EnumGenerator(util.Generator):

    def __init__(self):
        self._enums = {}

    def add_enum(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._enums[obj] = code

    def get_names(self):
        return ["enums"]

    def is_empty(self):
        return not bool(self._enums)

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "enums.rst")
        classes = self._enums.keys()
        classes.sort(key=lambda x: x.__name__)

        def get_name(cls):
            return cls.__module__ + "." + cls.__name__

        names = [get_name(cls) for cls in classes]

        with open(path, "wb") as h:
            text = _template.render(names=names)
            h.write(text.encode("utf-8"))

        for cls in classes:
            code = self._enums[cls]
            module_fileobj.write(code + "\n")
