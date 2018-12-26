# Copyright 2018 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import io
import os
import subprocess
import sys
import tempfile
import typing

from .namespace import get_namespace
from .repo import Repository
from .util import get_gir_files


# Initialising the current module to an invalid name
current_module: str = '-'
current_module_dependencies = set()


def strip_current_module(clsname: str) -> str:
    # Strip GI module prefix from names in the current module
    if clsname.startswith(current_module + "."):
        return '"%s"' % clsname[len(current_module + "."):]
    return clsname


def add_dependent_module(module: str):
    # FIXME: Find a better way to check this. This currently won't work for GI
    # modules that aren't installed in the current venv.
    import gi.repository
    if hasattr(gi.repository, module):
        current_module_dependencies.add(module)


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

    def add_function(self, function, *, ignore_type_error=False):
        if ignore_type_error:
            function += "  # type: ignore"
        self.functions.append(function)

    @property
    def class_line(self):
        if self.parents:
            parents = "({})".format(
                ', '.join(strip_current_module(p) for p in self.parents))
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
        return "typing.Sequence[%s]" % get_typing_name(type_[0])
    elif isinstance(type_, dict):
        assert len(type_) == 1
        key, value = type_.popitem()
        return "typing.Mapping[%s, %s]" % (get_typing_name(key), get_typing_name(value))
    elif type_.__module__ in ("__builtin__", "builtins"):
        return type_.__name__
    elif type_.__module__ == current_module:
        # Strip GI module prefix from current-module types
        return '"%s"' % type_.__name__
    else:
        add_dependent_module(type_.__module__)
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
            out.append("typing.Sequence[%s]" % arg_to_annotation(p[1:-1]))
        elif p.startswith("{"):
            p = p[1:-1]
            k, v = p.split(":", 1)
            k = arg_to_annotation(k.strip())
            v = arg_to_annotation(v.strip())
            out.append("typing.Mapping[%s, %s]" % (k, v))
        elif p:
            class_str = strip_current_module(p)
            if '.' in class_str:
                add_dependent_module(class_str.split('.', 1)[0])
            out.append(class_str)

    if len(out) == 0:
        return "typing.Any"
    elif len(out) == 1:
        return out[0]
    elif len(out) == 2 and 'None' in out:
        # This is not strictly necessary, but it's easier to read than the Union
        out.pop(out.index('None'))
        return f"typing.Optional[{out[0]}]"
    else:
        return f"typing.Union[{', '.join(out)}]"


def format_function_returns(signature_result) -> str:
    # Format return values
    return_values = []
    for r in signature_result:
        # We have either a (name, return type) pair, or just the return type.
        type_ = r[1] if len(r) > 1 else r[0]
        return_values.append(arg_to_annotation(type_))

    # Additional handling for structuring return values
    if len(return_values) == 0:
        returns = 'None'
    elif len(return_values) == 1:
        returns = return_values[0]
    else:
        returns = f'typing.Tuple[{", ".join(return_values)}]'

    return returns


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

    returns = format_function_returns(signature.res)

    return f'{decorator}def {function.name}{args} -> {returns}: ...'


def stub_flag(flag) -> str:
    stub = StubClass(flag.name)
    for v in flag.values:
        if not v.name.isidentifier():
            continue
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
        if not v.name.isidentifier():
            continue
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
    #  * pyprops: These have no type information, and I'm not certain
    #    what they cover, etc.

    for f in getattr(cls, 'fields', []):
        if not f.name.isidentifier():
            continue
        stub.add_member(format_field(f))

    for v in cls.methods + cls.vfuncs:
        # GObject-based constructors often violate Liskov substitution,
        # leading to typing errors such as:
        #     Signature of "new" incompatible with supertype "Object"
        # While we're waiting for a more general solution (see
        # https://github.com/python/mypy/issues/1237) we'll just ignore
        # the typing errors.

        # TODO: Extract constructor information from GIR and add it to
        # docobj.Function to use here.
        ignore = v.name == "new"
        stub.add_function(stub_function(v), ignore_type_error=ignore)

    return str(stub)


def format_field(field) -> str:
    return f"{field.name} = ...  # type: {get_typing_name(field.py_type)}"


def format_callback(fn) -> str:
    # We're formatting a callback signature here, not an actual function.
    args = ", ".join(arg_to_annotation(v) for k, v in fn.full_signature.args)
    returns = format_function_returns(fn.full_signature.res)
    return f"{fn.name} = typing.Callable[[{args}], {returns}]"


def format_imports(namespace, version):
    ns = get_namespace(namespace, version)
    for dep in ns.dependencies:
        current_module_dependencies.add(dep[0])

    import_lines = [
        "import typing",
        "",
        *sorted(f"from gi.repository import {dep}" for dep in current_module_dependencies),
        ""
    ]
    return "\n".join(import_lines)


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

    # We track the module currently being stubbed for naming reasons. e.g.,
    # within GObject stubs, referring to "GObject.Object" is incorrect; we
    # need the typing reference to be simply "Object".
    global current_module
    global current_module_dependencies

    for namespace, version in get_to_write(args.target, namespace, version):
        mod = Repository(namespace, version).parse()
        module_path = os.path.join(args.target, namespace + ".pyi")

        current_module = namespace
        current_module_dependencies = set()

        class_likes = (
            mod.pyclasses +
            mod.classes +
            # From a GI point of view, structures are really just classes
            # that can't inherit from anything.
            mod.structures +
            # The semantics of a GI-mapped union type don't really map
            # nicely to typing structures. It *is* a typing.Union[], but
            # you can't add e.g., function signatures to one of those.
            #
            # In practical terms, treating these as classes seems best.
            mod.unions
        )

        h = io.StringIO()

        for cls in class_likes:
            h.write(stub_class(cls))
            h.write("\n\n")

        for cls in mod.flags:
            h.write(stub_flag(cls))
            h.write("\n\n")

        for cls in mod.enums:
            h.write(stub_enum(cls))
            h.write("\n\n")

        for fn in mod.callbacks:
            h.write(format_callback(fn))
            h.write("\n")

        if mod.callbacks:
            h.write("\n\n")

        for func in mod.functions:
            h.write(stub_function(func))
            # Extra \n because the signature lacks one.
            h.write("\n\n\n")

        for const in mod.constants:
            h.write(format_field(const))
            h.write("\n")

        with open(module_path, "w", encoding="utf-8") as f:
            # Start by handling all required imports for type annotations
            f.write(format_imports(namespace, version))
            f.write("\n\n")
            f.write(h.getvalue())
