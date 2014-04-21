# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util


class MappingGenerator(util.Generator):

    def __init__(self, repo):
        self.repo = repo

    def get_names(self):
        return ["mapping"]

    def is_empty(self):
        return False

    def write(self, dir_, module_fileobj):
        path = os.path.join(dir_, "mapping.rst")
        handle = open(path, "wb")
        handle.write("""
Symbol Mapping
==============
""")

        def write_table(handle, lines):
            handle.write('''

.. csv-table::
    :header: "C", "Python"
    :widths: 1, 99

%s

    ''' % "\n".join(lines))

        i = 0
        lines = []
        for key, value in sorted(self.repo._types.items()):
            if not value.startswith(self.repo.namespace + "."):
                continue
            if self.repo.is_private(value):
                continue

            i += 1
            if not i % 100:
                write_table(handle, lines)
                lines = []

            key = util.escape_rest(key)
            value = util.escape_rest(value)
            line = util.get_csv_line([key, ":py:data:`%s`" % value])
            lines.append("    %s" % line)

        if lines:
            write_table(handle, lines)

        handle.close()
