# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import re
import keyword
import inspect
import csv
import cStringIO


def escape_keyword(text, reg=re.compile("^(%s)$" % "|".join(keyword.kwlist))):
    return reg.sub(r"\1_", text)


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

    from gi.repository import Gtk
    struct_base = Gtk.AccelKey.__mro__[-2]  # FIXME
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


def indent(text):
    return "\n".join(["    " + l for l in text.splitlines()])


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
    return text


def merge_in_overrides(obj):
    # hide overrides by merging the bases in
    possible_bases = []
    for base in obj.__bases__:
        if base.__name__ == obj.__name__ and base.__module__ == obj.__module__:
            for upper_base in base.__bases__:
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


def is_normalmethod(obj):
    return not is_staticmethod(obj) and not is_classmethod(obj)


def make_rest_title(text, char="="):
    return text + "\n" + len(text) * char


def get_gir_dirs():
    if "XDG_DATA_DIRS" in os.environ:
        dirs = os.environ["XDG_DATA_DIRS"].split(os.pathsep)
    else:
        dirs = ["/usr/local/share/", "/usr/share/"]

    return [os.path.join(d, "gir-1.0") for d in dirs]


def get_gir_files():
    """All gir files: {'{namespace}-{version}': path}"""

    all_modules = {}
    for d in get_gir_dirs():
        if not os.path.exists(d):
            continue
        for entry in os.listdir(d):
            root, ext = os.path.splitext(entry)
            if ext == ".gir":
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

    values = [v.replace("\n", " ") for v in values]
    h = cStringIO.StringIO()
    w = csv.writer(h, CSVDialect)
    w.writerow(values)
    return h.getvalue().rstrip()


def gtype_to_rest(gtype):
    p = gtype.pytype
    if p is None:
        return ""
    name = p.__name__
    if p.__module__ != "__builtin__":
        name = p.__module__ + "." + name
    return ":class:`%s`" % name


class Generator(object):
    """Abstract base class"""

    def is_empty(self):
        """If there is any content to create"""
        raise NotImplementedError

    def write(self):
        """Create and write everything"""
        raise NotImplementedError

    def get_names(self):
        """A list of names that can be references in
        an rst file (toctree e.g.)
        """

        raise NotImplementedError
