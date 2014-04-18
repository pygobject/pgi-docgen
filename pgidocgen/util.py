# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import re
import inspect
import keyword
import csv
import cStringIO


_KWD_RE = re.compile("^(%s)$" % "|".join(keyword.kwlist))


def iter_public_attr(obj):
    for attr in sorted(dir(obj)):
        if attr.startswith("_"):
            continue

        try:
            attr_obj = getattr(obj, attr)
        except (NotImplementedError, AttributeError):
            if not inspect.isclass(obj):
                obj = type(obj)
            # FIXME.. pgi exposes methods it can't compile
            print "PGI-ERROR: %s.%s.%s" % (obj.__module__, obj.__name__, attr)
            continue
        yield attr, attr_obj


def import_namespace(namespace, version):
    namespace = str(namespace)

    import gi
    try:
        gi.require_version(namespace, version)
    except ValueError as e:
        raise ImportError(e)
    module = __import__("gi.repository", fromlist=[namespace])
    module = getattr(module, namespace)

    # this needs to be synced with module._import_dependency
    if namespace in ("Clutter", "ClutterGst", "Gst", "Grl"):
        module.init([])
    elif namespace in ("Gsf", "IBus"):
        module.init()

    return module


def escape_identifier(text, reg=_KWD_RE):
    """Escape C identifiers so they can be used as attributes/arguments"""

    # see http://docs.python.org/reference/lexical_analysis.html#identifiers
    if not text:
        return text
    if text[0].isdigit():
        text = "_" + text
    return reg.sub(r"\1_", text)


def escape_parameter(text):
    """Escape a GObject parameter name so it can be used as python
    attribute/argument
    """

    return escape_identifier(text.replace("-", "_"))


def get_overridden_class(obj):
    assert inspect.isclass(obj)

    # if the class has a base with the same gtype, it's certainly an
    # override
    for base in obj.__mro__[1:]:
        if getattr(base, "__gtype__", None) == obj.__gtype__ and obj is not base:
            return base

    return


def is_method_owner(cls, method_name):
    obj = getattr(cls, method_name)
    assert obj

    ovr = get_overridden_class(cls)
    if ovr and method_name in ovr.__dict__:
        return True

    for base in merge_in_overrides(cls):
        if getattr(base, method_name, None) == obj:
            return False
    return True


def is_fundamental(obj):
    """True for classed and non-classed fundamentals"""

    if not inspect.isclass(obj):
        return False

    return hasattr(obj, "__gtype__")


def is_iface(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GObject
    return issubclass(obj, GObject.GInterface)


def is_object(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GObject
    return issubclass(obj, GObject.Object)


def is_flags(obj):
    if not inspect.isclass(obj):
        return False

    from gi.repository import GObject
    return issubclass(obj, GObject.GFlags)


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

    from gi.repository import GObject
    enum_base = GObject.GEnum
    return issubclass(obj, enum_base)


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
    base = merge_in_overrides(cls)[0]
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
    return text


def merge_in_overrides(obj):
    # hide overrides by merging the bases in
    possible_bases = []
    for base in obj.__bases__:
        if base.__name__ == obj.__name__ and base.__module__ == obj.__module__:
            for upper_base in merge_in_overrides(base):
                possible_bases.append(upper_base)
        else:
            possible_bases.append(base)

    # preserve the mro
    mro_bases = []
    for base in obj.__mro__:
        if base in possible_bases:
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


def is_normalmethod(obj):
    return not is_staticmethod(obj) and not is_classmethod(obj)


def make_rest_title(text, char="="):
    return text + "\n" + len(text) * char


def get_gir_dirs():
    from gi.repository import GLib

    dirs = GLib.get_system_data_dirs()
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
    return h.getvalue().rstrip()


def gtype_to_rest(gtype):
    p = gtype.pytype
    if p is None:
        return ""
    name = p.__name__
    if p.__module__ != "__builtin__":
        return ":class:`%s`" % (p.__module__ + "." + name)
    return ":obj:`%s`" % name


class Generator(object):
    """Abstract base class"""

    def is_empty(self):
        """If there is any content to create"""

        raise NotImplementedError

    def write(self, dir_, module_fileobj=None):
        """Create and write everything"""

        raise NotImplementedError

    def get_names(self):
        """A list of names that can be references in
        an rst file (toctree e.g.)
        """

        raise NotImplementedError
