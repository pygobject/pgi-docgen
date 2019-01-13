# Copyright 2018 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import builtins
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

# Set of type names that can be unwittingly shadowed and will cause
# trouble with the type checker.
shadowed_builtins = {
    builtin for builtin in builtins.__dict__
    if isinstance(builtins.__dict__[builtin], type)
}


def strip_current_module(clsname: str) -> str:
    # Strip GI module prefix from names in the current module
    if clsname.startswith(current_module + "."):
        return clsname[len(current_module + "."):]
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

    indent = " " * 4

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

    def __str__(self):
        parents = ', '.join(strip_current_module(p) for p in self.parents)
        class_line = "class {}({}):".format(self.classname, parents)

        body_lines = sorted(self.members)
        for function in self.functions:
            body_lines.extend([''] + function.splitlines())
        if not body_lines:
            body_lines = ['...']

        return '\n'.join(
            [class_line] +
            [(self.indent + line).rstrip() for line in body_lines] +
            ['']
        )


def topological_sort(class_nodes):
    """
    Topologically sort a list of class nodes according to inheritance

    We use this as a workaround for typing stub order dependencies
    (see python/mypy#6119).

    Code adapted from https://stackoverflow.com/a/43702281/2963
    """
    # Map class name to actual class node being sorted
    name_node_map = {node.fullname: node for node in class_nodes}
    # Map class name to parent classes
    name_parents_map = {}
    # Map class name to child classes
    name_children_map = {name: [] for name in name_node_map}

    for name, node in name_node_map.items():
        in_module_bases = [b.name for b in node.bases if b.name in name_node_map]
        name_parents_map[name] = in_module_bases
        for base_name in in_module_bases:
            name_children_map[base_name].append(name)

    # Establish bases
    sorted_names = [n for n, preds in name_parents_map.items() if not preds]

    for name in sorted_names:
        for child in name_children_map[name]:
            name_parents_map[child].remove(name)
            if not name_parents_map[child]:
                # Mutating list that we're iterating over, so that this
                # class gets removed from subsequent pending parents
                # lists.
                sorted_names.append(child)

    if len(sorted_names) < len(name_node_map):
        raise RuntimeError("Couldn't establish a topological ordering")

    return [name_node_map[name] for name in sorted_names]


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
    elif type_ is type(None):
        # As a weird corner-case, some non-introspectable base types
        # actually give NoneType here. We treat them as very special.
        return "typing.Any"
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
        return "builtins.%s" % type_.__name__
    elif type_.__module__ == current_module:
        # Strip GI module prefix from current-module types
        return type_.__name__
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
        elif p in shadowed_builtins:
            out.append("builtins.%s" % p)
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


def format_function_args(function, *, include_arg_names=True) -> str:
    """Format function arguments as a type annotation fragment"""

    arg_specs = []

    if (function.is_method or function.is_vfunc) and not function.is_static:
        arg_specs.append('self')

    for key, value in function.full_signature.args:
        spec = "{key}: {type}" if include_arg_names else "{type}"
        arg_specs.append(spec.format(key=key, type=arg_to_annotation(value)))

    return ", ".join(arg_specs)


def format_function_returns(function) -> str:
    """Format function return values as a type annotation fragment"""

    return_values = []
    for r in function.full_signature.res:
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


def format_function(function) -> str:
    # We require the full signature details for argument types, and fallback
    # to the simplest possible function signature if it's not available.
    if not getattr(function, 'full_signature', None):
        print("Missing full signature for {}".format(function))
        return "def {}(*args, **kwargs): ...".format(function.name)

    return '{decorator}def {name}({args}) -> {returns}: ...'.format(
        decorator="@staticmethod\n" if function.is_static else "",
        name=function.name,
        args=format_function_args(function),
        returns=format_function_returns(function),
    )


def stub_class(cls) -> str:
    stub = StubClass(cls.name)

    if hasattr(cls, 'bases'):
        stub.parents = [b.name for b in cls.bases]
    elif hasattr(cls, 'base'):
        stub.parents = [cls.base] if cls.base else []

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

        # Special case handling for weird annotations
        if cls.fullname == 'GObject.Value' and f.name == 'data':
            continue

        stub.add_member(format_field(f))

    # The `values` attribute is available on enums and flags, and its
    # type will always be the current class.
    for v in getattr(cls, 'values', []):
        if not v.name.isidentifier():
            continue
        stub.add_member(f"{v.name} = ...  # type: {cls.name}")

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
        stub.add_function(format_function(v), ignore_type_error=ignore)

    return str(stub)


def format_field(field) -> str:
    return f"{field.name}: {get_typing_name(field.py_type)}"


def format_callback(function) -> str:
    # We're formatting a callback signature here, not an actual function.
    return "{name} = typing.Callable[[{args}], {returns}]".format(
        name=function.name,
        args=format_function_args(function, include_arg_names=False),
        returns=format_function_returns(function),
    )


def format_imports(namespace, version):
    ns = get_namespace(namespace, version)
    for dep in ns.dependencies:
        current_module_dependencies.add(dep[0])

    import_lines = [
        "import builtins",
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
            topological_sort(mod.classes) +
            # From a GI point of view, structures are really just classes
            # that can't inherit from anything.
            mod.structures +
            # The semantics of a GI-mapped union type don't really map
            # nicely to typing structures. It *is* a typing.Union[], but
            # you can't add e.g., function signatures to one of those.
            #
            # In practical terms, treating these as classes seems best.
            mod.unions +
            # `GFlag`s and `GEnum`s are slightly different to classes, but
            # easily covered by the same code.
            mod.flags +
            mod.enums
        )

        h = io.StringIO()

        for cls in class_likes:
            h.write(stub_class(cls))
            h.write("\n\n")

        for fn in mod.callbacks:
            h.write(format_callback(fn))
            h.write("\n")

        if mod.callbacks:
            h.write("\n\n")

        for func in mod.functions:
            h.write(format_function(func))
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
