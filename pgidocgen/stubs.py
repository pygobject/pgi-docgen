# Copyright 2018 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
import subprocess
import tempfile
import os

from .repo import Repository
from .util import get_gir_files
from .namespace import get_namespace


def add_parser(subparsers):
    parser = subparsers.add_parser("stubs", help="Create a typing stubs")
    parser.add_argument('target',
                        help='path to where the resulting stubs should be')
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
                [sys.executable, sys.argv[0], "stubs", target, namespace])
    finally:
        try:
            os.unlink(temp_cache)
        except OSError:
            pass


def main(args):
    if not args.namespace:
        print("No namespace given")
        raise SystemExit(1)
    elif len(args.namespace) > 1:
        return _main_many(args.target, args.namespace)
    else:
        namespace = args.namespace[0]

    girs = get_gir_files()

    if namespace not in girs:
        print("GIR file for %s not found, aborting." % namespace)
        raise SystemExit(1)

    namespace, version = namespace.split("-", 1)
    try:
        os.mkdir(args.target)
    except OSError:
        pass

    def get_to_write(dir_, namespace, version):
        """Returns a list of modules to write.

        Traverses the dependencies and stops if a module
        build directory is found, skipping it and all its deps.
        """

        mods = []
        if os.path.exists(os.path.join(dir_, namespace + ".pyi")):
            return mods
        mods.append((namespace, version))

        ns = get_namespace(namespace, version)
        for dep in ns.dependencies:
            mods.extend(get_to_write(dir_, *dep))

        return mods

    for namespace, version in get_to_write(args.target, namespace, version):
        mod = Repository(namespace, version).parse()
        module_path = os.path.join(args.target, namespace + ".pyi")
        types = mod.classes + mod.flags + mod.enums + \
            mod.structures + mod.unions
        with open(module_path, "w", encoding="utf-8") as h:
            for cls in types:
                h.write("""\
class {}: ...
""".format(cls.name))

            for func in mod.functions:
                h.write("""\
def {}(*args, **kwargs): ...
""".format(func.name))

            for const in mod.constants:
                h.write("""\
{} = ...
""".format(const.name))
