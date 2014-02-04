#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
usage: pgi-docgen-build.py [-h] target path

Build the sphinx environ created with pgi-docgen

positional arguments:
  target      path to where the result should be
  path        path to the sphinx environ
"""

import argparse
import os
import subprocess
import multiprocessing


OPTIPNG = "optipng"


def has_optipng():
    try:
        subprocess.check_output([OPTIPNG, "--version"])
    except OSError:
        return False
    return True


def _do_optimize(path):
    subprocess.check_output([OPTIPNG, path])
    return path


def png_optimize_dir(dir_, pool_size=6):
    """Optimizes all pngs in dir_ (non-recursive)"""

    if not os.path.exists(dir_):
        return

    pngs = [e for e in os.listdir(dir_) if e.lower().endswith(".png")]
    paths = [os.path.join(dir_, f) for f in pngs]

    pool = multiprocessing.Pool(pool_size)
    for i, path in enumerate(pool.imap_unordered(_do_optimize, paths), 1):
        name = os.path.basename(path)
        print "%s(%d/%d): %r" % (OPTIPNG, i, len(paths), name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Build the sphinx environ created with pgi-docgen')
    parser.add_argument('target', help='path to where the result should be')
    parser.add_argument('path', help='path to the sphinx environ')
    args = parser.parse_args()

    build_dir = args.target
    subprocess.check_call(["sphinx-build", args.path, build_dir])

    if has_optipng():
        png_dirs = [
            os.path.join(build_dir, "_static"),
            os.path.join(build_dir, "_images")
        ]

        for dir_ in png_dirs:
            png_optimize_dir(dir_)
    else:
        print "optipng missing, skipping compression"
