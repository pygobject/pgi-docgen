# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re
from BeautifulSoup import BeautifulStoneSoup, Tag

from .namespace import Namespace
from . import util
from .util import unindent, get_csv_line, gtype_to_rest, escape_rest
from .util import force_unindent
from .gtkstock import parse_stock_icon
from .funcsig import FuncSignature


def handle_data(types, d):

    scanner = re.Scanner([
        (r"[#%@]?[A-Za-z0-9_:\-]+\**", lambda scanner, token:("ID", token)),
        (r"[#%@]?[A-Za-z0-9_:\-]+\**", lambda scanner, token:("ID", token)),
        (r"\(", lambda scanner, token:("OTHER", token)),
        (r"\)", lambda scanner, token:("OTHER", token)),
        (r",", lambda scanner, token:("OTHER", token)),
        (r"\s", lambda scanner, token:("SPACE", token)),
        (r"[^\s]+", lambda scanner, token:("OTHER", token)),
    ])

    results, remainder = scanner.scan(d)
    assert not remainder

    objects = {
        "NULL": "None",
        "TRUE": "True",
        "FALSE": "False",
        "gint": "int",
        "gboolean": "bool",
        "gchar": "str",
        "gdouble": "float",
        "glong": "int",
        "gfloat": "float",
        "guint": "int",
        "gulong": "int",
        "char": "str",
        "gpointer": "object",
    }

    def id_ref(token):
        # possible identifier reference

        # strip pointer
        sub = token.rstrip("*")

        if sub.startswith(("#", "%")):
            sub = sub[1:]

        if sub in objects:
            return ":obj:`%s`" % objects[sub]
        elif sub in types:
            pytype = types[sub]
            assert "." in pytype
            return ":class:`%s`" % pytype
        elif token.startswith(("#", "%")):
            if token.endswith("s"):
                # if we are sure it's a reference and it ends with 's'
                # like "a list of #GtkWindows", we also try "#GtkWindow"
                sub = token[1:-1]
                if sub in types:
                    pytype = types[sub]
                    assert "." in pytype
                    return ":class:`%s <%s>`" % (pytype + "s", pytype)
            else:
                # also try to add "s", GdkFrameTiming(s)
                sub = token[1:] + "s"
                if sub in types:
                    pytype = types[sub]
                    assert "." in pytype
                    py_no_s = pytype[:-1] if pytype[-1] == "s" else pytype
                    return ":class:`%s <%s>`" % (py_no_s, pytype)

        #if token.startswith(("#", "%")):
        #    print token

        return token

    out = []
    need_space_at_start = False
    for type_, token in results:
        orig_token = token
        if type_ == "ID":

            # paremeter reference
            if token.startswith("@"):
                token = token[1:]
                if token.lower() == token:
                    token = "`%s`" % token
                else:
                    token = id_ref(token)
            else:
                parts = re.split("(:+)", token)
                if len(parts) > 2 and parts[2]:
                    obj, sep, sigprop = parts[0], parts[1], "".join(parts[2:])
                    name = sigprop.replace("_", "-")
                    obj_token = id_ref(obj)
                    token = ""
                    if obj_token:
                        token = obj_token + " "
                    token += ":ref:`%s%s <%s>`" % (sep, name, name)
                else:
                    if "-" in token:
                        first, rest = token.split("-", 1)
                        token = id_ref(first) + "-" + rest
                    elif token.endswith(":"):
                        token = id_ref(token[:-1]) + ":"
                    else:
                        token = id_ref(token)

        changed = orig_token != token

        # nothing changed, escape
        if not changed:
            token = escape_rest(token)

        # insert a space for the previous one
        if need_space_at_start:
            if not token:
                pass
            else:
                # ., is also OK
                if not token.startswith((" ", ".", ",")):
                    token = " " + token
                need_space_at_start = False

        if changed:
            # something changed, we have to make sure that
            # the previous and next character is a space so
            # docutils doesn't get confused wit references
            need_space_at_start = True

        out.append(token)

    return "".join(out)


def handle_xml(types, out, item):
    if isinstance(item, Tag):
        if item.name == "literal" or item.name == "type":
            out.append("``%s``" % item.text)
        elif item.name == "itemizedlist":
            lines = []
            for item in item.contents:
                if not isinstance(item, Tag):
                    continue

                lines.append("* " + " ".join(handle_data(
                             types, item.getText()
                             ).splitlines()))
            out.append("\n" + "\n".join(lines) + "\n")

        elif item.name == "programlisting":
            text = item.getText()
            if not text.count("\n"):
                out.append("``%s``" % item.getText())
            else:
                code = "\n.. code-block:: c\n\n%s" % util.indent(
                    util.unindent(item.getText(), ignore_first_line=True))
                out.append(code)

        elif item.name == "title":
            out.append(handle_data(types, item.getText()))
        else:
            for sub in item.contents:
                handle_xml(types, out, sub)
    else:
        if not out or out[-1].endswith("\n"):
            data = force_unindent(item.string, ignore_first_line=False)
        else:
            data = force_unindent(item.string, ignore_first_line=True)
        out.append(handle_data(types, data))


def docstring_to_rest(types, docstring):
    # |[ ]| seems to mark inline code. Move it to docbook so we have a
    # single thing to work with below

    def to_programlisting(match):
        from xml.sax.saxutils import escape
        escaped = escape(match.group(1))
        return "<programlisting>%s</programlisting>" % escaped

    docstring = re.sub("\|\[(.*?)\]\|", to_programlisting,
                       docstring, flags=re.MULTILINE | re.DOTALL)

    # We don't care about para
    docstring = re.sub("<para>", "", docstring)
    docstring = re.sub("</para>", "", docstring)

    soup = BeautifulStoneSoup(docstring,
                              convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    out = []
    for item in soup.contents:
        handle_xml(types, out, item)
    rst = "".join(out)

    def fixup_added_since(match):
        return """

:Since: *%s*

""" % match.group(1).strip()

    rst = re.sub('@?Since:?\s+([^\s]+)$', fixup_added_since, rst)
    return rst


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

    def lookup_return_docs(self, name):
        """Get docs for the return value by function name.

        e.g. 'GObject.Value.set_char'
        """

        if name in self._returns:
            return self._fix_docs(self._returns[name])
        return ""

    def lookup_parameter_docs(self, name):
        """Get docs for a function parameter by function name + parameter name.

        e.g. 'GObject.Value.set_char.v_char'
        """

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

            l = map(util.escape_identifier, l)
            key = ".".join(l)
            if not kind:
                self._all[key] = docs
            elif kind == "parameters":
                self._parameters[key] = docs
            elif kind == "return-value":
                self._returns[key] = docs

    def _fix_docs(self, d):
        return docstring_to_rest(self._types, d)

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
            n = "_`%s`" % n  # inline target
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
        docs = sig.to_rest_listing(self, name).splitlines()

        # if we have a user docstring, use it, otherwise use the gir one
        if user_docstring:
            docs.append("")
            docs.append(unindent(user_docstring))
        elif name in self._all:
            docs.append("")
            docs.append(self._get_docs(name))

        docs = "\n".join(docs)

        # in case the function is overriden, let sphinx get the funcspec
        # but still keep around the old docstring (sphinx seems to understand
        # the string under attribute thing.. good, since we can't change
        # a docstring in py2)

        if is_method:
            # Rewrap them here so spinx knows that they static and
            # we can use that information in the autosummary extension.
            # If we wrap a classmethod in another one sphinx doesn't
            # pick up the function signature.. so only use staticmethod.
            if util.is_staticmethod(obj) or util.is_classmethod(obj):
                name = "staticmethod(%s)" % name

            return """
%s = %s
r'''
%s
'''
""" % (func_name, name, docs.encode("utf-8"))

        return """
%s = %s
%s.__doc__ = \
r'''
%s
'''
""" % (func_name, name ,name, docs.encode("utf-8"))
