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
=====
Flags
=====

{% if entries %}
    {% for name, is_base in entries %}
* :class:`{{ name }}`
    {% endfor %}

{% else %}
None

{% endif %}

Details
-------

{% if entries %}
    {% for name, is_base in entries %}
.. autoclass:: {{ name }}
    {% if not is_base %}
    :show-inheritance:
    {% endif %}
    :members:
    :undoc-members:
    :private-members:

    {% endfor %}
{% else %}
None

{% endif %}
""")


class FlagsGenerator(genutil.Generator):

    def __init__(self):
        self._flags = {}

    def add_flags(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._flags[obj] = code

    def get_names(self):
        return ["flags"]

    def is_empty(self):
        return not bool(self._flags)

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "flags.rst")
        classes = self._flags.keys()
        classes.sort(key=lambda x: x.__name__)

        def get_name(cls):
            return cls.__module__ + "." + cls.__name__

        entries = [(get_name(cls), util.is_base(cls)) for cls in classes]

        with open(path, "wb") as h:
            text = _template.render(entries=entries)
            h.write(text.encode("utf-8"))

        for cls in classes:
            code = self._flags[cls]
            module_fileobj.write(code + "\n")
