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

    # get all availabel gir files
    all_modules = {}
    for d in get_gir_dirs():
        if not os.path.exists(d):
            continue
        for entry in os.listdir(d):
            root, ext = os.path.splitext(entry)
            if ext == ".gir":
                all_modules[root] = os.path.join(d, entry)

    modules = []
    if "-a" in sys.argv[1:] or "--all" in sys.argv[1:]:
        modules = all_modules.keys()
    else:
        modules.extend([a for a in sys.argv[1:] if a[:1] != "-"])
        for m in modules:
            if m not in all_modules.keys():
                print "%r not found" % m
                raise SystemExit(1)

    # print all packages that cotain the gir files on debian
    if "--debian" in sys.argv[1:]:
        print "Generating dpkg list.."
        packages = []
        for m in modules:
            import subprocess
            out = subprocess.check_output(["dpkg", "-S", all_modules[m]])
            packages.append(out.split(":", 1)[0])
        print "sudo apt-get install " + " ".join(sorted(set(packages)))
        raise SystemExit(0)

    print "Modules:", " ".join(modules)

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
