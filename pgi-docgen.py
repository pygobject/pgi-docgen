#!/usr/bin/python
# Copyright 2013, 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
import os
import shutil
import argparse

try:
    import pgi
except ImportError:
    is_pgi = False
else:
    is_pgi = True
    pgi.install_as_gi()
    pgi.set_backend("ctypes,null")

from pgidocgen.main import MainGenerator
from pgidocgen.util import get_gir_files


def main(argv):
    parser = argparse.ArgumentParser(
        description='Create a sphinx environ')
    parser.add_argument('-f', '--force', action='store_true',
                        help="Remove the target path if it exists")
    parser.add_argument('target', help='path to where the result should be')
    parser.add_argument('namespaces', nargs='+',
                        help='A list of namespaces including versions '
                             '(e.g. "Gtk-3.0 GLib-2.0")')

    args = parser.parse_args(argv[1:])

    if not is_pgi and args.namespaces:
        print "Can't build API docs without pgi"
        print "Get it here: https://github.com/lazka/pgi"
        raise SystemExit(1)

    # this catches the "pip install pgi" case
    if pgi.version_info[-1] != -1:
        print "atm pgi-docgen needs pgi trunk and not a stable release"
        print "Get it here: https://github.com/lazka/pgi"
        raise SystemExit(1)

    girs = get_gir_files()

    filtered = {}
    for name in args.namespaces:
        if name not in girs:
            print "GIR file for %s not found, aborting." % name
            raise SystemExit(1)
        if name in filtered:
            print "Passed multiple times: %r" % name
        filtered[name] = girs[name]

    dest_dir = args.target
    if os.path.exists(dest_dir):
        if args.force:
            shutil.rmtree(dest_dir)
        else:
            print "Target already exists (pass -f to ignore): %s" % dest_dir
            raise SystemExit(1)

    gen = MainGenerator(dest_dir)
    for name in filtered:
        namespace, version = name.split("-")
        print "Create docs: Namespace=%s, Version=%s" % (namespace, version)
        if namespace == "cairo":
            print "cairo gets referenced to external docs, skipping"
            continue
        gen.add_module(namespace, version)
    gen.write()


if __name__ == "__main__":
    main(sys.argv)
