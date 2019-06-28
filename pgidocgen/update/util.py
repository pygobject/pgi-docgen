# Copyright 2018 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
from contextlib import contextmanager


@contextmanager
def progress(total):
    width = 70
    last_blocks = [-1]

    def update(current, clear=False):
        if total == 0:
            blocks = 0
        else:
            blocks = int((float(current) / total) * width)
        if blocks == last_blocks[0] and not clear:
            return
        last_blocks[0] = blocks
        line = "[" + "#" * blocks + " " * (width - blocks) + "]"
        line += (" %%%dd/%%d" % len(str(total))) % (current, total)
        if clear:
            line = " " * len(line)
        sys.stdout.write(line)
        sys.stdout.write("\b" * len(line))
        sys.stdout.flush()

    update(0)
    yield update
    update(0, True)
