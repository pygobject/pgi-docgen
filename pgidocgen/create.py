# Copyright 2013, 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import argparse

import pgi

from .gen import ModuleGenerator
from .util import get_gir_files


def main(argv):
    parser = argparse.ArgumentParser(
        description='Create a sphinx environ')
    parser.add_argument('source',
                        help='path to where the resulting source should be')
    parser.add_argument('namespace',
                        help='namespace including version e.g. Gtk-3.0')

    try:
        args = parser.parse_args(argv[1:])
    except SystemExit:
        raise SystemExit(1)

    if not args.namespace:
        print "No namespace given"
        raise SystemExit(1)

    # this catches the "pip install pgi" case
    if pgi.version_info[-1] != -1:
        print "atm pgi-docgen needs pgi trunk and not a stable release"
        print "Get it here: https://github.com/lazka/pgi"
        raise SystemExit(1)

    girs = get_gir_files()

    if args.namespace not in girs:
        print "GIR file for %s not found, aborting." % args.namespace
        raise SystemExit(1)

    gen = ModuleGenerator()
    namespace, version = args.namespace.split("-", 1)
    print "Create docs: Namespace=%s, Version=%s" % (namespace, version)
    gen.add_module(namespace, version)
    gen.write(args.source)
