#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import subprocess
import multiprocessing


def _do_optimize(path):
    subprocess.check_output(["optipng", path])
    return path


def png_optimize_dir(dir_):
    if not os.path.exists(dir_):
        return

    pngs = [e for e in os.listdir(dir_) if e.endswith(".png")]
    paths = [os.path.join(dir_, f) for f in pngs]

    pool = multiprocessing.Pool(6)
    for i, path in enumerate(pool.imap_unordered(_do_optimize, paths), 1):
        name = os.path.basename(path)
        print "optipng(%d/%d): %r" % (i, len(paths), name)


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

    # make a nice tarball without the sphinx cruft
    os.chdir("_docs/_build")
    paths = [p for p in os.listdir(".") if p[:1] != "."]
    subprocess.call(["tar", "-zcvf", "../build.tar.gz"] + paths)
    os.chdir("../..")
