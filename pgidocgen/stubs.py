# Copyright 2018 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import subprocess
import sys
import tempfile
import typing

from .namespace import get_namespace
from .repo import Repository
from .util import get_gir_files


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
        self.functions = []

    def add_member(self, member):
        self.members.append(member)

    def add_function(self, function):
        self.functions.append(function)

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

    @property
    def function_lines(self):
        lines = []
        for function in self.functions:
            lines.append('')
            for line in function.splitlines():
                lines.append(f'    {line}')
        return lines

    def __str__(self):
        body_lines = self.member_lines + self.function_lines
        if not body_lines:
            body_lines = ['    ...']

        return '\n'.join(
            [self.class_line] +
            body_lines +
            ['']
        )


def get_typing_name(type_: typing.Any) -> str:
    """Gives a name for a type that is suitable for a typing annotation.

    This is the Python annotation counterpart to funcsig.get_type_name().

    int -> "int"
    Gtk.Window -> "Gtk.Window"
    [int] -> "Sequence[int]"
    {int: Gtk.Button} -> "Mapping[int, Gtk.Button]"
    """

    if type_ is None:
        return ""
    elif isinstance(type_, str):
        return type_
    elif isinstance(type_, list):
        assert len(type_) == 1
        return "Sequence[%s]" % get_typing_name(type_[0])
    elif isinstance(type_, dict):
        assert len(type_) == 1
        key, value = type_.popitem()
        return "Mapping[%s, %s]" % (get_typing_name(key), get_typing_name(value))
    elif type_.__module__ in ("__builtin__", "builtins"):
        return type_.__name__
    else:
        # FIXME: We need better module handling here. I think we need to strip
        # the module if the type's module is the *current* module being
        # annotated, and if not then we need to track imports and probably add
        # a "gi.repository." prefix.
        return "%s.%s" % (type_.__module__, type_.__name__)


def arg_to_annotation(text):
    """Convert a docstring argument to a Python annotation string

    This is the Python annotation counterpart to funcsig.arg_to_class_ref().
    """

    if not text.startswith(("[", "{")) or not text.endswith(("}", "]")):
        parts = text.split(" or ")
    else:
        parts = [text]

    out = []
    for p in parts:
        if p.startswith("["):
            out.append("Sequence[%s]" % arg_to_annotation(p[1:-1]))
        elif p.startswith("{"):
            p = p[1:-1]
            k, v = p.split(":", 1)
            k = arg_to_annotation(k.strip())
            v = arg_to_annotation(v.strip())
            out.append("Mapping[%s, %s]" % (k, v))
        elif p:
            out.append(p)

    if len(out) == 1:
        return out[0]
    elif len(out) == 2 and 'None' in out:
        # This is not strictly necessary, but it's easier to read than the Union
        out.pop(out.index('None'))
        return f"Optional[{out[0]}]"
    else:
        return f"Union[{', '.join(out)}]"


def stub_function(function) -> str:
    # We require the full signature details for argument types, and fallback
    # to the simplest possible function signature if it's not available.
    signature = getattr(function, 'full_signature', None)
    if not signature:
        print(f"Missing full signature for {function}; falling back")
        return f"def {function.name}(*args, **kwargs): ..."

    # Decorator handling
    decorator = "@staticmethod\n" if function.is_static else ""

    # Format argument types
    arg_specs = []

    if (function.is_method or function.is_vfunc) and not function.is_static:
        arg_specs.append('self')

    for key, value in signature.args:
        arg_specs.append(f'{key}: {arg_to_annotation(value)}')
    args = f'({", ".join(arg_specs)})'

    # Format return values
    return_values = []
    for r in signature.res:
        # We have either a (name, return type) pair, or just the return type.
        type_ = r[1] if len(r) > 1 else r[0]
        return_values.append(arg_to_annotation(type_))

    # Additional handling for structuring return values
    if len(return_values) == 0:
        returns = 'None'
    elif len(return_values) == 1:
        returns = return_values[0]
    else:
        returns = f'Tuple[{", ".join(return_values)}]'

    return f'{decorator}def {function.name}{args} -> {returns}: ...'


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


def stub_enum(enum) -> str:
    stub = StubClass(enum.name)
    for v in enum.values:
        stub.add_member(f"{v.name} = ...  # type: {enum.name}")

    for v in enum.methods:
        stub.add_function(stub_function(v))

    if enum.vfuncs:
        # This is unsupported simply because I can't find any GIR that
        # has vfuncs on its enum types.
        raise NotImplementedError(
            "Enum support doesn't annotate vfuncs")

    return str(stub)


def stub_class(cls) -> str:
    stub = StubClass(cls.name)

    bases = getattr(cls, 'bases', [])
    # TODO: These parent classes may require namespace prefix sanitising.
    stub.parents = [b.name for b in bases]

    # TODO: We don't handle:
    #  * child_properties: It's not clear how to annotate these
    #  * gtype_struct: I'm not sure what we'd use this for.
    #  * properties: It's not clear how to annotate these
    #  * signals: It's not clear how to annotate these

    for f in cls.fields:
        stub.add_member(format_field(f))

    for v in cls.methods + cls.vfuncs:
        stub.add_function(stub_function(v))

    return str(stub)


def format_field(field) -> str:
    return f"{field.name} = ...  # type: {get_typing_name(field.py_type)}"


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

        mods = set()
        if os.path.exists(os.path.join(dir_, namespace + ".pyi")):
            return mods
        mods.add((namespace, version))

        ns = get_namespace(namespace, version)
        for dep in ns.dependencies:
            mods |= get_to_write(dir_, *dep)

        return mods

    for namespace, version in get_to_write(args.target, namespace, version):
        mod = Repository(namespace, version).parse()
        module_path = os.path.join(args.target, namespace + ".pyi")

        with open(module_path, "w", encoding="utf-8") as h:

            for cls in mod.classes:
                h.write(stub_class(cls))
                h.write("\n\n")

            for cls in mod.structures:
                # From a GI point of view, structures are really just classes
                # that can't inherit from anything.
                h.write(stub_class(cls))
                h.write("\n\n")

            for cls in mod.unions:
                # The semantics of a GI-mapped union type don't really map
                # nicely to typing structures. It *is* a typing.Union[], but
                # you can't add e.g., function signatures to one of those.
                #
                # In practical terms, treating these as classes seems best.
                h.write(stub_class(cls))
                h.write("\n\n")

            for cls in mod.flags:
                h.write(stub_flag(cls))
                h.write("\n\n")

            for cls in mod.enums:
                h.write(stub_enum(cls))
                h.write("\n\n")

            for func in mod.functions:
                h.write(stub_function(func))
                # Extra \n because the signature lacks one.
                h.write("\n\n\n")

            for const in mod.constants:
                h.write(format_field(const))
                h.write("\n")
