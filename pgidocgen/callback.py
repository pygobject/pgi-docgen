# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


_template = util.get_template(u"""\
=========
Callbacks
=========

{% if func_names %}
.. autosummary::

    {% for name in func_names %}
    {{ name }}
    {% endfor %}
{% else %}
None
{% endif %}


Details
-------

{% if func_names %}
    {% for name in func_names %}
.. autofunction:: {{ name }}

    {% endfor %}
{% else %}
None
{% endif %}
""")


class CallbackGenerator(util.Generator):

    _FILENAME = "callbacks"

    def __init__(self):
        self._callbacks = {}

    def add_callback(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._callbacks[obj] = code

    def get_names(self):
        return [self._FILENAME]

    def is_empty(self):
        return not bool(self._callbacks)

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "%s.rst" % self._FILENAME)

        def get_name(func):
            return func.__module__ + "." + func.__name__

        funcs = self._callbacks.keys()
        funcs.sort(key=lambda x: x.__name__)
        func_names = [get_name(f) for f in funcs]

        with open(path, "wb") as h:
            text = _template.render(func_names=func_names)
            h.write(text.encode("utf-8"))

        for f in funcs:
            code = self._callbacks[f]
            module_fileobj.write(code + "\n")
