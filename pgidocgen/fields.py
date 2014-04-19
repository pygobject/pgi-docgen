# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from . import util


class FieldsMixin(object):

    _fields = {}

    def add_fields(self, cls_obj, fields):
        assert cls_obj not in self._fields

        self._fields[cls_obj] = fields

    def write_field_table(self, cls, h, inherit_list=None):
        cls_name = cls.__module__ + "." + cls.__name__

        h.write("""

.. _%s.fields:

Fields
------

""" % cls_name)

        h.write(inherit_list or "")

        lines = []
        for field in self._fields.get(cls, []):
            prop = util.get_csv_line([
                field.name, field.type_desc, field.flags_string, field.desc])
            lines.append("    %s" % prop)
        lines = "\n".join(lines)

        if not lines and not inherit_list:
            h.write("None\n")

        if lines:
            h.write('''
.. csv-table::
    :header: "Name", "Type", "Access", "Description"
    :widths: 20, 1, 1, 100

%s
''' % lines)
