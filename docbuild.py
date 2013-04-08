#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import subprocess


def png_optimize_dir(dir_):
    if not os.path.exists(dir_):
        return
    pngs = [e for e in os.listdir(dir_) if e.endswith(".png")]
    for i, file_ in enumerate(pngs):
        if not file_.endswith(".png"):
            continue
        path = os.path.join(dir_, file_)
        print "optipng(%d/%d): %r" % (i, len(pngs), file_)
        subprocess.check_output(["optipng", path])


if __name__ == "__main__":
    DEST = "_docs"
    build_dir = os.path.join(DEST, "_build")
    subprocess.call(["sphinx-build", DEST, build_dir])

    png_dirs = [
        os.path.join(build_dir, "_static"),
        os.path.join(build_dir, "_images")
    ]

    for dir_ in png_dirs:
        if os.path.exists(dir_):
            png_optimize_dir(dir_)
