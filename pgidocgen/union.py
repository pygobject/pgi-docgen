# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util
from .fields import FieldsMixin


_main_template = util.get_template("""\
======
Unions
======

.. toctree::
    :maxdepth: 1

{% for name in names %}
    {{ name }}
{% endfor %}

""")


_sub_template = util.get_template("""\
{{ "=" * cls_name|length }}
{{ cls_name }}
{{ "=" * cls_name|length }}

{{ field_table }}


Methods
-------

{% if method_names %}
.. autosummary::

    {% for name in method_names %}
        {{ name }}
    {% endfor %}

{% else %}
None

{% endif %}

Details
-------

.. autoclass:: {{ cls_name }}
    {% if not is_base %}
    :show-inheritance:
    {% endif %}
    :members:
    :undoc-members:

""")


class UnionGenerator(util.Generator, FieldsMixin):

    def __init__(self):
        self._unions = {}
        self._methods = {}

    def get_names(self):
        return ["unions/index.rst"]

    def is_empty(self):
        return not bool(self._unions)

    def add_union(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")
        self._unions[obj] = code

    def add_method(self, cls_obj, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        if cls_obj in self._methods:
            self._methods[cls_obj].append((obj, code))
        else:
            self._methods[cls_obj] = [(obj, code)]

    def write(self, dir_, module_fileobj):
        sub_dir = os.path.join(dir_, "unions")
        path = os.path.join(sub_dir, "index.rst")
        os.mkdir(sub_dir)

        unions = sorted(self._unions.keys(), key=lambda x: x.__name__)

        # write the code
        for cls in unions:
            module_fileobj.write(self._unions[cls])
            methods = self._methods.get(cls, [])
            def sort_func(e):
                return util.is_normalmethod(e[0]), e[0].__name__
            methods.sort(key=sort_func)

            for obj, code in methods:
                module_fileobj.write(util.indent(code) + "\n")

        # write rest
        with open(path, "wb") as h:
            names = [cls.__name__ for cls in unions]
            text = _main_template.render(names=names)
            h.write(text.encode("utf-8"))

        for cls in self._unions:
            methods = [m[0] for m in self._methods.get(cls, [])]
            self._write_union(sub_dir, cls, methods)

    def _write_union(self, sub_dir, cls, methods):
        rst_path = os.path.join(sub_dir, cls.__name__) + ".rst"

        with open(rst_path, "wb") as h:

            def get_name(cls):
                return cls.__module__ + "." + cls.__name__

            cls_name = get_name(cls)
            field_table = self.get_field_table(cls)

            def get_method_name(cls, obj):
                return get_name(cls) + "." + obj.__name__

            # sort static methods first, then by name
            def sort_func(e):
                return util.is_normalmethod(e), e.__name__

            methods.sort(key=sort_func)
            method_names = [get_method_name(cls, obj) for obj in methods]
            is_base = util.is_base(cls)

            text = _sub_template.render(
                method_names=method_names, is_base=is_base,
                field_table=field_table, cls_name=cls_name)

            h.write(text.encode("utf-8"))
