# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from __future__ import print_function

import os
import re
import inspect
import keyword
import csv
import warnings
import subprocess

from docutils.core import publish_parts


_KWD_RE = re.compile("^(%s)$" % "|".join(keyword.kwlist))


def rest2html(text):
    return publish_parts(text, writer_name='html')['html_body']


def shell(cmd):
    """Executes a command in a shell"""

    pipe = subprocess.PIPE
    p = subprocess.Popen(cmd, shell=True, stdout=pipe, stderr=pipe, stdin=pipe)
    stdout, stderr = p.communicate()
    return (p.returncode,
            stdout.strip().decode("utf-8"),
            stderr.strip().decode("utf-8"))


def parse_gir_shared_libs(gir_path):
    """Returns a list of shared libraries for a .gir file.

    XXX: This doesn't parse the file properly.. but it's fast.
    """

    shared_libs = []
    with open(gir_path, "rb") as h:
        for line in h.read().decode("utf-8").splitlines():
            line = line.strip()
            if line.startswith("shared-library="):
                shared_libs.extend(line.split("=")[-1].strip("\"").split(","))
                break
    return list(filter(None, shared_libs))


def cache_calls(func):
    _cache = {}
    def wrap(*args):
        if len(_cache) > 100:
            _cache.clear()
        if args not in _cache:
            _cache[args] = func(*args)
        return _cache[args]
    return wrap


def get_child_properties(cls):
    """Returns a list of GParamSpecs or an empty list"""

    Gtk = import_namespace("Gtk", "3.0")

    if not issubclass(cls, Gtk.Container):
        return []

    def get_props(cls):
        class_struct = cls._get_class_struct(Gtk.ContainerClass)
        return class_struct.list_child_properties()

    # only get properties the base classes don't have
    all_props = get_props(cls)
    names = dict((p.name, p) for p in all_props)

    for base in fake_mro(cls)[1:]:
        if not issubclass(base, Gtk.Container):
            break
        for p in get_props(base):
            names.pop(p.name, None)

    return names.values()


def get_style_properties(cls):
    """Returns a list of GParamSpecs or an empty list"""

    Gtk = import_namespace("Gtk", "3.0")

    if not issubclass(cls, Gtk.Widget):
        return []

    def get_props(cls):
        class_struct = cls._get_class_struct(Gtk.WidgetClass)
        return class_struct.list_style_properties()

    # only get properties the base classes don't have
    all_props = get_props(cls)
    names = dict((p.name, p) for p in all_props)

    for base in fake_mro(cls)[1:]:
        if not issubclass(base, Gtk.Widget):
            break
        for p in get_props(base):
            names.pop(p.name, None)

    return names.values()


def iter_public_attr(obj):
    for attr in sorted(dir(obj)):
        if attr.startswith("_") and not attr == "_":
            continue

        try:
            attr_obj = getattr(obj, attr)
        except (NotImplementedError, AttributeError):
            if not inspect.isclass(obj):
                obj = type(obj)
            # FIXME.. pgi exposes methods it can't compile
            print("PGI-ERROR: %s.%s.%s" % (obj.__module__, obj.__name__, attr))
            continue
        yield attr, attr_obj


def escape_identifier(text, reg=_KWD_RE):
    """Escape C identifiers (or a part of them)
    so they can be used as attributes/arguments
    """

    assert "-" not in text

    # see http://docs.python.org/reference/lexical_analysis.html#identifiers
    if not text:
        return u"_"
    if text[0].isdigit():
        text = "_" + text
    return reg.sub(r"\1_", text)


def unescape_parameter(text):
    start = 0
    end = 0
    if escape_parameter(text[1:]) == text:
        start = 1
    if escape_parameter(text[:-1]) == text:
        end = -1
    return text[start:len(text) + end].replace("_", "-")


def escape_parameter(text):
    """Escape a GObject parameter name so it can be used as python
    attribute/argument
    """

    return escape_identifier(text.replace("-", "_"))


def get_overridden_class(obj):
    """Given a class returns the overridden one or None

    If we have a Gtk.Widget override class which is a subclass of the original
    Gtk.Widget class passing in the former will return the later.
    """

    assert inspect.isclass(obj), obj

    if not hasattr(obj, "__gtype__"):
        return

    # if the class has a base with the same gtype, it's certainly an
    # override
    for base in obj.__mro__[1:]:
        if getattr(base, "__gtype__", None) == obj.__gtype__ and obj is not base:
            return base

    return


def is_attribute_owner(cls, attr_name):
    """Given a class returns True if the attribute name is owned by the
    class itself or its base if it is an override class.

    If the attribute isn't found returns False
    """

    try:
        obj = getattr(cls, attr_name)
    except AttributeError:
        return False

    ovr = get_overridden_class(cls)
    if ovr and attr_name in ovr.__dict__:
        return True

    for base in fake_bases(cls):
        if getattr(base, attr_name, None) == obj:
            return False
    return True


def is_method_owner(cls, method_name):
    return is_attribute_owner(cls, method_name)


def is_field_owner(cls, field_name):
    return is_attribute_owner(cls, field_name)


def is_fundamental(obj):
    """True for classed and non-classed fundamentals"""

    if not inspect.isclass(obj):
        return False

    return hasattr(obj, "__gtype__")


def is_iface(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GObject
    return issubclass(obj, GObject.GInterface) and not is_object(obj)


def is_object(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GObject
    return issubclass(obj, GObject.Object)


def is_flags(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GLib
    return issubclass(obj, GLib.Flags)


def is_struct(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GLib
    struct_base = GLib.Data.__mro__[-2]  # FIXME
    return issubclass(obj, struct_base)


def is_union(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GLib
    union_base = GLib.DoubleIEEE754.__mro__[-2]  # FIXME
    return issubclass(obj, union_base)


def is_enum(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GLib
    return issubclass(obj, GLib.Enum)


def is_field(obj):
    from gi.repository import GObject

    field_base = type(GObject.Value.g_type)
    return isinstance(obj, field_base)


def is_base(cls):
    """If all base classes of the passed class are internal"""

    if not inspect.isclass(cls):
        return False

    if cls.__bases__[0] in (object, int, long, float, str, unicode):
        return True

    # skip any overrides
    base = fake_bases(cls)[0]
    if base.__module__.split(".")[0] in ("pgi", "gi"):
        return True

    return False


def indent(text, count=4):
    return "\n".join([(" " * count) + l for l in text.splitlines()])


def unindent(text, ignore_first_line=False):
    """Unindent a piece of text"""

    lines = text.splitlines()
    common_indent = -1
    for i, line in enumerate(lines):
        if i == 0 and ignore_first_line:
            continue
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if common_indent == -1:
            common_indent = indent
        else:
            common_indent = min(indent, common_indent)

    if common_indent == -1:
        common_indent = 0

    new = []
    for l in lines:
        indent = min(len(l) - len(l.lstrip()), common_indent)
        new.append(l[indent:])
    return "\n".join(new)


def force_unindent(text, ignore_first_line=False):
    """Unindent a piece of text, line by line"""

    lines = text.split("\n")

    if ignore_first_line:
        return "\n".join(lines[:1] + [l.lstrip() for l in lines[1:]])
    else:
        return "\n".join([l.lstrip() for l in lines])


def escape_rest(text):
    text = text.replace("\\", "\\\\")
    text = text.replace("*", "\\*")
    text = text.replace("_", "\\_")
    text = text.replace(":", "\\:")
    text = text.replace("`", "\\`")
    text = text.replace("@", "\\@")  # email auto detection
    return text


def fake_subclasses(cls):
    """Gives a list of subclasses, replacing classes by their overrides"""

    subs = []
    for sub in cls.__subclasses__():
        for subsub in fake_subclasses(sub):
            if get_overridden_class(subsub) is sub:
                subs.append(subsub)
                break
        else:
            subs.append(sub)
    return subs


def fake_bases(obj, ignore_redundant=False):
    """If ignore_redundant=True any bases which are already implied by previous
    bases are ignored.
    """

    # hide overrides by merging the bases in
    possible_bases = []
    known = set()
    for base in obj.__bases__:
        new_bases = []
        if base.__name__ == obj.__name__ and base.__module__ == obj.__module__:
            for upper_base in fake_bases(base,
                                         ignore_redundant=ignore_redundant):
                new_bases.append(upper_base)
        else:
            new_bases.append(base)

        for new_base in new_bases:
            if not ignore_redundant or new_base not in known:
                possible_bases.append(new_base)

        known.update(base.__mro__)

    # preserve the mro
    mro_bases = []
    for base in obj.__mro__:
        if base in possible_bases:
            mro_bases.append(base)
    return mro_bases


def fake_mro(obj):

    def get_mro(obj):
        mro = [obj]
        for base in fake_bases(obj):
            mro.extend(get_mro(base))
        return mro

    possible_mro = get_mro(obj)

    # preserve the real mro
    mro_bases = []
    for base in obj.__mro__:
        if base in possible_mro:
            mro_bases.append(base)
    return mro_bases


def is_staticmethod(obj):
    return not hasattr(obj, "im_self")


def is_classmethod(obj):
    try:
        return obj.im_self is not None
    except AttributeError:
        return False


def is_virtualmethod(obj):
    assert callable(obj)

    return getattr(obj, "_is_virtual", False)


def is_callback(obj):
    assert callable(obj)

    return hasattr(obj, "_is_callback")


def is_property(obj):
    return isinstance(obj, property) or (
        hasattr(obj, "__get__") and not callable(obj))


def is_normalmethod(obj):
    return not is_staticmethod(obj) and not is_classmethod(obj)


def make_rest_title(text, char="="):
    return text + "\n" + len(text) * char


def xdg_get_system_data_dirs():
    """http://standards.freedesktop.org/basedir-spec/latest/"""

    data_dirs = os.getenv("XDG_DATA_DIRS")
    if data_dirs:
        return list(map(os.path.abspath, data_dirs.split(":")))
    else:
        return ("/usr/local/share/", "/usr/share/")


def get_gir_dirs():
    dirs = xdg_get_system_data_dirs()
    return [os.path.join(d, "gir-1.0") for d in dirs]


def get_gir_files():
    """All gir files: {'{namespace}-{version}': path}"""

    all_modules = {}
    for d in get_gir_dirs():
        if not os.path.exists(d):
            continue
        for entry in os.listdir(d):
            root, ext = os.path.splitext(entry)
            # use the first one found
            if ext == ".gir" and root not in all_modules:
                all_modules[root] = os.path.join(d, entry)
    return all_modules


def get_csv_line(values):
    import cStringIO

    class CSVDialect(csv.Dialect):
        delimiter = ','
        quotechar = '"'
        doublequote = True
        skipinitialspace = False
        lineterminator = '\n'
        quoting = csv.QUOTE_ALL

    encoded = []
    for value in [v.replace("\n", " ") for v in values]:
        if isinstance(value, unicode):
            value = value.encode("utf-8")
        encoded.append(value)

    h = cStringIO.StringIO()
    w = csv.writer(h, CSVDialect)
    w.writerow(encoded)
    return h.getvalue().rstrip().decode("utf-8")


def instance_to_rest(cls, inst):
    """Reference some python instance.

    For flags/enums try to get the predefined instance.
    """

    # get rid of 'L' suffixes with repr()
    if isinstance(inst, long):
        inst = int(inst)

    if inst is None or inst is True or inst is False:
        return ":obj:`%s`" % inst

    if is_enum(cls):
        for k, v in cls.__dict__.items():
            if isinstance(v, cls) and v == inst:
                return  ":obj:`%s`" % (
                    get_namespace(cls) + "." + cls.__name__ + "." + k)
    elif is_flags(cls):
        bits = []
        for k, v in cls.__dict__.items():
            if isinstance(v, cls) and (v & inst or (v == 0 and v == inst)):
                bits.append(":obj:`%s`" % (
                    get_namespace(cls) + "." + cls.__name__ + "." + k))
        if bits:
            return " | ".join(bits)
        else:
            inst = int(inst)

    return "``%s``" % repr(inst)


def import_namespace(namespace, version=None, ignore_version=False):
    """Equivalent to 'from gi.repository import <ns>'

    Returns the namespace module.
    Raises ImportError in case the import fails.
    """

    import gi

    if version is not None:
        try:
            gi.require_version(namespace, version)
        except ValueError as e:
            raise ImportError(e, version)

    with warnings.catch_warnings(record=True) as w:
        mod = getattr(
                __import__("gi.repository." + namespace).repository, namespace)

        if namespace in ("Clutter", "ClutterGst", "Gst", "Grl"):
            mod.init([])
        elif namespace in ("Gsf", "IBus"):
            mod.init()

        if not ignore_version:
            assert not w, namespace
        return mod


def get_module_version(module):
    return module._version


def get_namespace(obj):
    """Returns the gi namespace for an instance or type

    get_namespace(Gtk.Widget) -> "Gtk"
    """

    return obj.__module__.split(".")[-1]


class cached_property(object):
    """A read-only @property that is only evaluated once."""

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = name = fget.__name__
        # these get name mangled, so caching wont work unless
        # we mangle too
        assert not (name.startswith("__") and not name.endswith("__")), \
            "can't cache a dunder method"

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result


class VersionedNamespace(str):

    @property
    def name(self):
        return self.split("-", 1)[0]

    @property
    def version(self):
        return self.split("-", 1)[-1]
