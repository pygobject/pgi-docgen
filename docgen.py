#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
import os
import shutil

try:
    import pgi
except ImportError:
    is_pgi = False
else:
    is_pgi = True
    pgi.install_as_gi()
    pgi.set_backend("ctypes,null")

from gen.main import MainGenerator
from gen.util import get_gir_dirs


if __name__ == "__main__":

    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:] or len(sys.argv) < 2:
        print ("%s [-t | --tutorial] [-a | --all | <namespace-version>...]"
               % sys.argv[0])
        raise SystemExit(1)

    if not is_pgi and len(sys.argv) > 1:
        print "Can't build API docs without pgi"
        print "Get here: https://github.com/lazka/pgi"
        raise SystemExit(1)

    modules = []
    if "-a" in sys.argv[1:] or "--all" in sys.argv[1:]:
        for d in get_gir_dirs():
            if not os.path.exists(d):
                continue
            for entry in os.listdir(d):
                root, ext = os.path.splitext(entry)
                if ext == ".gir":
                    modules.append(root)
    else:
        modules.extend([a for a in sys.argv[1:] if a[:1] != "-"])

    dest_dir = "_docs"

    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    create_tutorial = "--tutorial" in sys.argv[1:] or "-t" in sys.argv[1:]

    gen = MainGenerator(dest_dir, tutorial=create_tutorial)

    for arg in modules:
        namespace, version = arg.split("-")
        print "Create docs: Namespace=%s, Version=%s" % (namespace, version)
        if namespace == "cairo":
            print "cairo gets referenced to external docs, skipping"
            continue
        gen.add_module(namespace, version)

    gen.write()

    print "done"
