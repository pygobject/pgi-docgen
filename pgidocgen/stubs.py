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


class StubClass:
    def __init__(self, classname):
        self.classname = classname
        self.parents = []
        self.members = []

    def add_member(self, member):
        self.members.append(member)

    @property
    def class_line(self):
        if self.parents:
            parents = "({})".format(', '.join(self.parents))
        else:
            parents = ""
        return "class {}{}:".format(self.classname, parents)

    @property
    def member_lines(self):
        return [
            "    {}".format(member)
            for member in sorted(self.members)
        ]

    def __str__(self):
        return '\n'.join(
            [self.class_line] +
            self.member_lines +
            ['']
        )


def stub_flag(flag) -> str:
    stub = StubClass(flag.name)
    for v in flag.values:
        stub.add_member(f"{v.name} = ...  # type: {flag.name}")

    if flag.methods or flag.vfuncs:
        # This is unsupported simply because I can't find any GIR that
        # has methods or vfuncs on its flag types.
        raise NotImplementedError(
            "Flag support doesn't annotate methods or vfuncs")

    return str(stub)


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
        types = mod.classes + mod.enums + \
            mod.structures + mod.unions
        with open(module_path, "w", encoding="utf-8") as h:
            for cls in types:
                h.write("""\
class {}: ...
""".format(cls.name))

            for cls in mod.flags:
                h.write(stub_flag(cls))
                h.write("\n\n")

            for func in mod.functions:
                h.write("""\
def {}(*args, **kwargs): ...
""".format(func.name))

            for const in mod.constants:
                h.write("""\
{} = ...
""".format(const.name))
