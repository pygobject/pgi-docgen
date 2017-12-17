# Copyright 2013, 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from __future__ import print_function

import sys
import argparse
import subprocess
import tempfile
import os

import pgi

from .gen import ModuleGenerator
from .util import get_gir_files


def add_parser(subparsers):
    parser = subparsers.add_parser("create",
        help="Create a sphinx environ")
    parser.add_argument('target',
                        help='path to where the resulting source should be')
    parser.add_argument('namespace', nargs="+",
                        help='namespace including version e.g. Gtk-3.0')
    parser.set_defaults(func=main)


def _main_many(target, namespaces):
    fd, temp_cache = tempfile.mkstemp("pgidocgen-cache")
    os.close(fd)
    try:
        os.environ["PGIDOCGEN_CACHE"] = temp_cache
        for namespace in namespaces:
            subprocess.check_call(
                [sys.executable, sys.argv[0], "create", target, namespace])
    finally:
        os.unlink(temp_cache)


def main(args):
    if not args.namespace:
        print("No namespace given")
        raise SystemExit(1)
    elif len(args.namespace) > 1:
        return _main_many(args.target, args.namespace)
    else:
        namespace = args.namespace[0]

    # this catches the "pip install pgi" case
    if pgi.version_info[-1] != -1:
        print("atm pgi-docgen needs pgi trunk and not a stable release")
        print("Get it here: https://github.com/pygobject/pgi")
        raise SystemExit(1)

    girs = get_gir_files()

    if namespace not in girs:
        print("GIR file for %s not found, aborting." % namespace)
        raise SystemExit(1)

    namespace, version = namespace.split("-", 1)
    gen = ModuleGenerator(namespace, version)
    gen.write(args.target)
