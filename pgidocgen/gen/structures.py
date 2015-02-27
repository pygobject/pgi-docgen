# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import genutil
from .fields import FieldsMixin

from .. import util


_main_template = genutil.get_template("""\
==========
Structures
==========

.. toctree::
    :maxdepth: 1

{% for name in names %}
    {{ name }}
{% endfor %}

""")

_sub_template = genutil.get_template("""\
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


class StructGenerator(genutil.Generator, FieldsMixin):

    def __init__(self):
        self._structs = {}
        self._methods = {}

    def get_names(self):
        return ["structs/index"]

    def is_empty(self):
        return not bool(self._structs)

    def add_struct(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")
        self._structs[obj] = code

    def add_method(self, cls_obj, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        if cls_obj in self._methods:
            self._methods[cls_obj].append((obj, code))
        else:
            self._methods[cls_obj] = [(obj, code)]

    def write(self, dir_, module_fileobj):
        sub_dir = os.path.join(dir_, "structs")

        os.mkdir(sub_dir)

        structs = self._structs.keys()

        def indent(c):
            return "\n".join(["    %s" % l for l in c.splitlines()])

        # write the code
        for cls in structs:
            module_fileobj.write(self._structs[cls])
            methods = self._methods.get(cls, [])
            def sort_func(e):
                return util.is_normalmethod(e[0]), e[0].__name__
            methods.sort(key=sort_func)

            for obj, code in methods:
                module_fileobj.write(indent(code) + "\n")

        structs = sorted(structs, key=lambda x: x.__name__)

        path = os.path.join(sub_dir, "index.rst")
        with open(path, "wb") as h:
            struct_names = [s.__name__ for s in structs]
            text = _main_template.render(names=struct_names)
            h.write(text.encode("utf-8"))

        for cls in structs:
            self._write_struct(sub_dir, cls)

    def _write_struct(self, sub_dir, cls):
        rst_path = os.path.join(sub_dir, cls.__name__) + ".rst"

        def get_name(cls):
            return cls.__module__ + "." + cls.__name__

        def get_method_name(cls, obj):
            return get_name(cls) + "." + obj.__name__

        with open(rst_path, "wb") as h:
            cls_name = get_name(cls)
            is_base = util.is_base(cls)
            field_table = self.get_field_table(cls)

            methods = [e[0] for e in self._methods.get(cls, [])]
            # sort static methods first, then by name
            def sort_func(e):
                return util.is_normalmethod(e), e.__name__
            methods.sort(key=sort_func)

            method_names = [get_method_name(cls, m) for m in methods]

            text = _sub_template.render(
                cls_name=cls_name, field_table=field_table,
                method_names=method_names, is_base=is_base)
            h.write(text.encode("utf-8"))
