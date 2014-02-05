# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from . import util
from .funcsig import py_type_to_class_ref


class FieldsMixin(object):

    _fields = {}

    def add_field(self, cls_obj, field_info):
        if cls_obj in self._fields:
            self._fields[cls_obj].append(field_info)
        else:
            self._fields[cls_obj] = [field_info]

    def has_fields(self, cls):
        return bool(self._fields.get(cls, []))

    def write_field_table(self, cls, h):

        h.write("""
Fields
------

""")

        lines = []
        for field_info in self._fields.get(cls, []):
            flags = []
            if field_info.readable:
                flags.append("r")
            if field_info.writeable:
                flags.append("w")

            prop = util.get_csv_line([
                field_info.name,
                py_type_to_class_ref(field_info.py_type),
                "/".join(flags)])
            lines.append("    %s" % prop)
        lines = "\n".join(lines)

        if not lines:
            h.write("None\n")
        else:
            h.write('''
.. csv-table::
    :header: "Name", "Type", "Access", "Description"
    :widths: 20, 1, 1, 100

%s
''' % lines)
