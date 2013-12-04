# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import cStringIO
import csv
import re
import xml.sax.saxutils as saxutils

from .namespace import Namespace
from . import util
from .util import escape_rest, unindent


def gtype_to_rest(gtype):
    p = gtype.pytype
    if p is None:
        return ""
    name = p.__name__
    if p.__module__ != "__builtin__":
        name = p.__module__ + "." + name
    return ":class:`%s`" % name


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


# Adapted from the PyGObject-Tutorial code
# Copyright by Sebastian Pölsterl
def parse_stock_icon(name):
    """
        e.g. 'Gtk.STOCK_ORIENTATION_LANDSCAPE'
    """

    img_p = re.compile("fileref=\"(.+?)\"")
    define_p = re.compile("\\s+")
    mapping = {}

    with open("/usr/include/gtk-3.0/gtk/gtkstock.h", "rb") as fp:
        imgs = []
        item = None
        for line in fp:
            if "inlinegraphic" in line:
                m = img_p.search(line)
                if m is not None:
                    imgs.append(m.group(1))

            if line.startswith("#define GTK_"):
                item = define_p.split(line)[1].replace("GTK_", "Gtk.")
                mapping[item] = imgs
                imgs = []

    base = "http://developer.gnome.org/gtk3/stable/"
    if not name in mapping:
        print "W: no image found for %r" % name
        return ""

    docs = ""
    for fn in mapping[name]:
        title = ""
        if "-ltr" in fn:
            title = "LTR variant:"
        elif "-rtl" in fn:
            title = "RTL variant:"
        docs += """

%s

.. image:: %s
    :alt: %s

""" % (title, base + fn, fn)

    return docs


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
            # skip *args, **kwargs
            if arg.startswith("*"):
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
            parts = [p.strip() for p in r.split(":")]
            res.append(parts)

        raises = bool(raises)

        return cls(res, arg_map, raises, name)


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
            if p == "None":
                out.append(":obj:`%s`" % p)
            else:
                out.append(":class:`%s`" % p)

    return " or ".join(out)


class Repository(object):
    """Takes gi objects and gives documented code"""

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        # c def name -> python name
        # gtk_foo_bar -> Gtk.foo_bar
        self._types = {}

        # Gtk.foo_bar.arg1 -> "some doc"
        self._parameters = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        self._returns = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        # Gtk.FooBar -> "some doc"
        self._all = {}

        self._ns = ns = Namespace(namespace, version)

        loaded = {}
        to_load = ns.get_dependencies()
        while to_load:
            key = to_load.pop()
            if key in loaded:
                continue
            sub_ns = Namespace(*key)
            loaded[key] = sub_ns
            to_load.extend(sub_ns.get_dependencies())

        for sub_ns in loaded.values():
            self._parse_types(sub_ns)

        self._parse_types(ns)
        self._parse_docs(ns)

    def _get_docs(self, name):
        if name in self._all:
            return self._fix_docs(self._all[name])
        return ""

    def _get_return_docs(self, name):
        if name in self._returns:
            return self._fix_docs(self._returns[name])
        return ""

    def _get_parameter_docs(self, name):
        if name in self._parameters:
            return self._fix_docs(self._parameters[name])
        return ""

    def get_dependencies(self):
        return self._ns.get_dependencies()

    def _parse_types(self, ns):
        self._types.update(ns.types)

    def _parse_docs(self, ns):
        """Parse docs"""

        dom = ns.get_dom()

        for doc in dom.getElementsByTagName("doc"):
            docs = doc.firstChild.nodeValue

            l = []
            current = doc
            kind = ""
            while current.tagName != "namespace":
                current = current.parentNode
                name = current.getAttribute("name")
                if not name:
                    kind = current.tagName
                    continue
                l.insert(0, name)

            key = ".".join(l)
            if not kind:
                self._all[key] = docs
            elif kind == "parameters":
                self._parameters[key] = docs
            elif kind == "return-value":
                self._returns[key] = docs

    def _fix_docs(self, d):

        d = saxutils.unescape(d)

        def fixup_code(match):
            # FIXME: do this right.. skipped for now
            return ""
            code = match.group(1)
            lines = code.splitlines()
            return "\n::\n\n%s" % ("\n".join(["    %s" % l for l in lines]))

        d = re.sub('\|\[(.*?)\]\|', fixup_code, d,
                   flags=re.MULTILINE | re.DOTALL)
        d = re.sub('<programlisting>(.*?)</programlisting>', fixup_code, d,
                   flags=re.MULTILINE | re.DOTALL)

        d = re.sub('<literal>(.*?)</literal>', '`\\1`', d)
        d = re.sub('<[^<]+?>', '', d)

        def fixup_class_refs(match):
            x = match.group(1)
            if x in self._types:
                local = self._types[x]
                if "." not in local:
                    local = self.namespace + "." + local
                return ":class:`%s` " % local
            return x

        d = re.sub('[#%]?([A-Za-z0-9_]+)', fixup_class_refs, d)

        def fixup_param_refs(match):
            return "`%s`" % match.group(1)

        d = re.sub('@([A-Za-z0-9_]+)', fixup_param_refs, d)

        def fixup_function_refs(match):
            x = match.group(1)
            # functions are always prefixed
            if not "_" in x:
                return x
            new = x.rstrip(")").rstrip("(")
            if new in self._types:
                return ":func:`%s`" % self._types[new]
            return x

        d = re.sub('([a-z0-9_]+(\(\)|))', fixup_function_refs, d)

        def fixup_signal_refs(match):
            name = match.group(1)
            name = name.replace("_", "-")
            return " :ref:`\:\:%s <%s>` " % (name, name)

        d = re.sub('::([a-z\-_]+)', fixup_signal_refs, d)

        def fixup_added_since(match):
            return """

.. versionadded:: %s
""" % match.group(1)

        d = re.sub('Since (\d+\.\d+)\s*$', fixup_added_since, d)

        d = d.replace("NULL", ":obj:`None`")
        d = d.replace("%NULL", ":obj:`None`")
        d = d.replace("%TRUE", ":obj:`True`")
        d = d.replace("TRUE", ":obj:`True`")
        d = d.replace("%FALSE", ":obj:`False`")
        d = d.replace("FALSE", ":obj:`False`")

        return d

    def parse_constant(self, name):
        # FIXME: broken escaping in pgi
        if name.split(".")[-1][:1].isdigit():
            return
        docs = self._get_docs(name)

        # Add images for stock icon constants
        if name.startswith("Gtk.STOCK_"):
            docs += parse_stock_icon(name)

        # sphinx gets confused by empty docstrings
        return """
%s = %s
r'''
.. fake comment to help sphinx

%s
'''

""" % (name.split(".")[-1], name, docs)

    def parse_class(self, name, obj, add_bases=False):
        names = []

        if add_bases:
            mro_bases = util.merge_in_overrides(obj)

            # prefix with the module if it's an external class
            for base in mro_bases:
                base_name = base.__name__
                if base.__module__ != self.namespace and base_name != "object":
                    base_name = base.__module__ + "." + base_name
                names.append(base_name)

        if not names:
            names = ["object"]

        bases = ", ".join(names)

        docs = self._get_docs(name)

        return """
class %s(%s):
    r'''
%s
    '''

    __init__ = %s.__init__

""" % (name.split(".")[-1], bases, docs.encode("utf-8"), name)

    def parse_signals(self, obj):

        if not hasattr(obj, "signals"):
            return ""

        sigs = []
        for attr in dir(obj.signals):
            if attr.startswith("_"):
                continue

            sig = getattr(obj.signals, attr)
            sigs.append(sig)

        lines = []
        for sig in sigs:
            name = sig.name

            doc_name = obj.__module__ + "." + obj.__name__ + "." + name
            docs = self._get_docs(doc_name)

            params = ", ".join([gtype_to_rest(t) for t in sig.param_types])
            ret = gtype_to_rest(sig.return_type)

            name = "_`%s`" % name  # inline target
            line = get_csv_line([name, params, ret, docs])
            lines.append('    %s' % line)

        lines = "\n".join(lines)
        if not lines:
            return ""

        return '''
.. csv-table::
    :header: "Name", "Parameters", "Return", "Description"
    :widths: 25, 10, 10, 100

%s
''' % lines

    def parse_properties(self, obj):

        if not hasattr(obj, "props"):
            return ""

        def get_flag_str(spec):
            flags = spec.flags
            s = []
            from pgi.repository import GObject
            if flags & GObject.ParamFlags.READABLE:
                s.append("r")
            if flags & GObject.ParamFlags.WRITABLE:
                s.append("w")
            if flags & GObject.ParamFlags.CONSTRUCT_ONLY:
                s.append("c")
            return "/".join(s)

        props = []
        for attr in dir(obj.props):
            if attr.startswith("_"):
                continue
            spec = getattr(obj.props, attr, None)
            if not spec:
                continue
            if spec.owner_type.pytype is obj:
                type_name = gtype_to_rest(spec.value_type)
                flags = get_flag_str(spec)
                props.append((spec.name, type_name, flags, spec.blurb))

        lines = []
        for n, t, f, b in props:
            b = self._fix_docs(b)
            prop = get_csv_line([n, t, f, b])
            lines.append("    %s" % prop)
        lines = "\n".join(lines)

        if not lines:
            return ""

        return '''
.. csv-table::
    :header: "Name", "Type", "Flags", "Description"
    :widths: 20, 1, 1, 100

%s
''' % lines

    def parse_flags(self, name, obj):
        from gi.repository import GObject

        # the base classes themselves: reference the real ones
        if obj in (GObject.GFlags, GObject.GEnum):
            return "%s = GObject.%s" % (obj.__name__, obj.__name__)

        base = obj.__bases__[0]
        base_name = base.__module__ + "." + base.__name__

        code = """
class %s(%s):
    r'''
%s
    '''
""" % (obj.__name__, base_name, self._get_docs(name))

        escaped = []

        values = []
        for attr_name in dir(obj):
            if attr_name.upper() != attr_name:
                continue
            attr = getattr(obj, attr_name)
            # hacky.. if there is an escaped one, ignore this one
            # and add it later with setattr
            if hasattr(obj, "_" + attr_name):
                escaped.append(attr_name)
                continue
            if not isinstance(attr, obj):
                continue
            values.append((int(attr), attr_name))

        values.sort()

        for val, n in values:
            code += "    %s = %r\n" % (n, val)
            doc_key = name + "." + n.lower()
            docs = self._get_docs(doc_key)
            code += "    r'''%s'''\n" % docs

        name = obj.__name__
        for v in escaped:
            code += "setattr(%s, '%s', %s)\n" % (name, v, "%s._%s" % (name, v))

        return code

    def parse_function(self, name, owner, obj):
        """Returns python code for the object"""

        is_method = owner is not None
        is_static = util.method_is_static(obj)

        def get_sig(obj):
            doc = str(obj.__doc__)
            first_line = doc and doc.splitlines()[0] or ""
            return FuncSignature.from_string(name.split(".")[-1], first_line)

        # FIXME: "GLib.IConv."
        if name.split(".")[-1] == "":
            return

        func_name = name.split(".")[-1]
        sig = get_sig(obj)

        # no valid sig, but still a docstring, probably new function
        # or an override with a new docstring
        if not sig and obj.__doc__:
            return "%s = %s\n" % (func_name, name)

        # no docstring, try to get the signature from base classes
        if not sig and owner:
            for base in owner.__mro__[1:]:
                try:
                    base_obj = getattr(base, func_name, None)
                except NotImplementedError:
                    # function not implemented in pgi
                    continue
                sig = get_sig(base_obj)
                if sig:
                    break

        # still nothing, try making the best out of it
        if not sig:
            if name not in self._all:
                # no gir docs, let sphinx handle it
                return "%s = %s\n" % (func_name, name)
            elif is_method:
                # INFO: this probably only happens if there is an override
                # for something pgi doesn't support. The base class
                # is missing the real one, but the gir docs are still there

                # for methods, add the docstring after
                return """
%s = %s
r'''
%s
'''
""" % (func_name, name, self._get_docs(name))
            else:
                # for toplevel functions, replace the introspected one
                # since sphinx ignores docstrings on the module level
                # and replacing __doc__ for normal functions is possible
                return """
%s = %s
%s.__doc__ = r'''
%s
'''
""" % (func_name, name, func_name, self._get_docs(name))

        # we got a valid signature here
        assert sig

        docstring = str(obj.__doc__)
        # the docstring contains additional text, propably an override
        # or internal function (GObject.Object methods for example)
        lines = docstring.splitlines()[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
        user_docstring = "\n".join(lines)

        # create sphinx lists for the signature we found
        docs = []
        for key, value in sig.args:
            param_key = name + "." + key
            text = self._get_parameter_docs(param_key)
            text = escape_rest(text)
            key = escape_rest(key)
            docs.append(":param %s: %s" % (key, text))
            docs.append(":type %s: %s" % (key, arg_to_class_ref(value)))

        if sig.raises:
            docs.append(":raises: :class:`GLib.GError`")

        if name in self._returns:
            # don't allow newlines here
            text = self._get_return_docs(name)
            doc_string = " ".join(text.splitlines())
            docs.append(":returns: %s" % doc_string)

        res = []
        for r in sig.res:
            if len(r) > 1:
                res.append("%s: %s" % (r[0], arg_to_class_ref(r[1])))
            else:
                res.append(arg_to_class_ref(r[0]))

        if res:
            docs.append(":rtype: %s" % ", ".join(res))

        docs.append("")

        # if we have a user docstring, use it, otherwise use the gir one
        if user_docstring:
            docs.append(unindent(user_docstring))
        elif name in self._all:
            docs.append(self._get_docs(name))

        docs = "\n".join(docs)

        # in case the function is overriden, let sphinx get the funcspec
        # but still keep around the old docstring (sphinx seems to understand
        # the string under attribute thing.. good, since we can't change
        # a docstring in py2)
        return """
%s = %s
r'''
%s
'''
""" % (func_name, name, docs.encode("utf-8"))
