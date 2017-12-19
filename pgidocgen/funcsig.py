# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re

from .util import indent
from .rstutil import field_name, bold


def get_type_name(type_):
    """Gives a name for a type that is suitable for a docstring.

    int -> "int"
    Gtk.Window -> "Gtk.Window"
    [int] -> "[int]"
    {int: Gtk.Button} -> "{int: Gtk.Button}"
    """

    if type_ is None:
        return ""
    elif isinstance(type_, str):
        return type_
    elif isinstance(type_, list):
        assert len(type_) == 1
        return "[%s]" % get_type_name(type_[0])
    elif isinstance(type_, dict):
        assert len(type_) == 1
        key, value = type_.popitem()
        return "{%s: %s}" % (get_type_name(key), get_type_name(value))
    elif type_.__module__ in ("__builtin__", "builtins"):
        return type_.__name__
    else:
        return "%s.%s" % (type_.__module__, type_.__name__)


def py_type_to_class_ref(type_):
    return arg_to_class_ref(get_type_name(type_))


def arg_to_class_ref(text):
    """Convert a docstring argument to a string with reST references"""

    if not text.startswith(("[", "{")) or not text.endswith(("}", "]")):
        parts = text.split(" or ")
    else:
        parts = [text]

    out = []
    for p in parts:
        if p.startswith("["):
            out.append("[%s]" % arg_to_class_ref(p[1:-1]))
        elif p.startswith("{"):
            p = p[1:-1]
            k, v = p.split(":", 1)
            k = arg_to_class_ref(k.strip())
            v = arg_to_class_ref(v.strip())
            out.append("{%s: %s}" % (k, v))
        else:
            if p == "bytes":
                out.append(":obj:`%s <str>`" % p)
            elif p:
                out.append(":obj:`%s`" % p)

    return " or ".join(out)


class FuncSignature(object):

    def __init__(self, res, args, raises, name):
        self.res = res
        self.args = args
        self.name = name
        self.raises = raises

    def __repr__(self):
        return "<%s res=%r args=%r, name=%r, raises=%r>" % (
            type(self).__name__, self.res, self.args, self.name, self.raises)

    @property
    def arg_names(self):
        return [p[0] for p in self.args]

    def get_arg_type(self, name):
        for a, t in self.args:
            if a == name:
                return t

    @classmethod
    def from_string(cls, orig_name, line):
        match = re.match("(.*?)\((.*?)\)\s*(raises|)\s*(-> )?(.*)", line)
        if not match:
            return

        groups = match.groups()
        name, args, raises, dummy, ret = groups
        if orig_name != name:
            return

        args = args and args.split(",") or []

        arg_map = []
        for arg in args:
            arg = arg.strip()
            # **kwargs
            if arg.startswith("**"):
                continue
            parts = arg.split(":", 1)
            if len(parts) == 1:
                parts.append("")
            parts = [p.strip() for p in parts]
            arg_map.append(parts)

        ret = ret and ret.strip() or ""
        if ret == "None":
            ret = ""
        ret = ret.strip("()")
        ret = ret and ret.split(",") or []
        res = []
        for r in ret:
            if r.startswith("{"):
                res.append([r])
            else:
                parts = [p.strip() for p in r.split(":", 1)]
                res.append(parts)

        raises = bool(raises)

        return cls(res, arg_map, raises, name)

    def to_simple_signature(self):
        """Gives a simple Python signature.

        e.g. foo(bar, bar2, *args)
        """

        args = []
        for key, value in self.args:
            args.append(key)

        return "(%s)" % (", ".join(args),)

    def to_rest_listing(self, doc_repo, full_name, current=None, signal=False):
        """A reST listing for this function signature.

        full_name: e.g. 'GObject.Binding.get_flags'
        doc_repo: Repository()
        """

        if signal:
            assert full_name.split(".")[-1].replace("-", "_") == self.name
        else:
            assert full_name.split(".")[-1] == self.name

        current_func = full_name
        if full_name.count(".") == 2:
            current_type = full_name.rsplit(".", 1)[0]
        else:
            current_type = None

        docs = []
        for i, (key, value) in enumerate(self.args):
            # strip * from *args
            key = key.lstrip("*")
            param_key = full_name + "." + key
            if signal and i == 0:
                text = "The object which received the signal"
            else:
                text = doc_repo.lookup_docs(
                    "signal-parameters" if signal else "parameters",
                    param_key, current_type=current_type,
                    current_func=full_name)[0]
            docs.append("%s\n%s" % (field_name("param", key), indent(text)))
            docs.append("%s %s\n" % (field_name("type", key), arg_to_class_ref(value)))

        if self.raises:
            docs.append(":raises: :class:`GLib.Error`")

        return_docs = []

        for r in self.res:
            if len(r) == 1:
                # normal return value
                text = doc_repo.lookup_docs(
                    "signal-returns" if signal else "returns",
                    full_name, current_type=current_type,
                    current_func=current_func)[0]
                if text:
                    return_docs.append(text)
            else:
                # out value
                name, type_ = r
                pkey = full_name + "." + name
                text = doc_repo.lookup_docs(
                    "signal-parameters" if signal else "parameters",
                    pkey, current_type=current_type,
                    current_func=current_func)[0]
                if text:
                    if len(self.res) != 1:
                        text = "%s\n%s" % (field_name(name), indent(text))
                    return_docs.append(text)

        if return_docs:
            docs.append(":returns:\n%s\n" % indent("\n\n".join(return_docs)))

        res_list = []
        for r in self.res:
            if len(r) > 1:
                res_list.append(
                    "%s: %s" % (bold(r[0]), arg_to_class_ref(r[1])))
            else:
                res_list.append(arg_to_class_ref(r[0]))

        if res_list:
            res_line = ", ".join(res_list)
            if len(self.res) > 1:
                res_line = "(%s)" % res_line
            docs.append(":rtype: %s" % res_line)

        return "\n".join(docs)
