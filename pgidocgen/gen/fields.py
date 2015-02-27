# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from . import genutil

from .. import util


_template = genutil.get_template("""\

.. _{{ cls_name }}.fields:

Fields
------

{% if inherit_list %}
{{ inherit_list }}
{% endif %}

{% if lines %}
.. csv-table::
    :header: "Name", "Type", "Access", "Description"
    :widths: 20, 1, 1, 100

    {% for line in lines %}
    {{ line }}
    {% endfor %}

{% elif not inherit_list %}
None

{% endif %}
""")


class FieldsMixin(object):

    _fields = {}

    def add_fields(self, cls_obj, fields):
        assert cls_obj not in self._fields

        self._fields[cls_obj] = fields

    def get_field_table(self, cls, inherit_list=None):
        cls_name = cls.__module__ + "." + cls.__name__

        lines = []
        for field in self._fields.get(cls, []):
            prop = util.get_csv_line([
                field.name, field.type_desc, field.flags_string, field.desc])
            lines.append( prop)
        inherit_list = inherit_list or ""

        text = _template.render(inherit_list=inherit_list, lines=lines,
                                cls_name=cls_name)
        return text

    def write_field_table(self, cls, h, inherit_list=None):
        h.write(self.get_field_table(cls, inherit_list).encode("utf-8"))
