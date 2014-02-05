# -*- coding: utf-8 -*-
# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from gi.repository import GObject

from .namespace import get_namespace
from . import util
from .util import unindent, get_csv_line, gtype_to_rest

from .gtkstock import parse_stock_icon
from .funcsig import FuncSignature
from .parser import docstring_to_rest


class Property(object):

    def __init__(self, name, type_desc, readable, writable, construct,
                 short_desc, desc):
        self.name = name
        self.type_desc = type_desc

        self.readable = readable
        self.writable = writable
        self.construct = construct

        self.short_desc = short_desc
        self.desc = desc


class Repository(object):
    """Takes gi objects and gives documented code"""

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        self._ns = ns = get_namespace(namespace, version)

        # Gtk.foo_bar.arg1 -> "some doc"
        self._parameters = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        self._returns = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        # Gtk.FooBar -> "some doc"
        self._all = {}

        # Gtk.Foo.some-signal -> "some doc"
        self._signals = {}

        # Gtk.Foo.some-prop -> "some doc"
        self._properties = {}

        a, pa, r, s, pr = ns.parse_docs()
        self._all.update(a)
        self._parameters.update(pa)
        self._returns.update(r)
        self._signals.update(s)
        self._properties.update(pr)

        self._private = ns.parse_private()

        loaded = {}
        to_load = ns.get_dependencies()
        while to_load:
            key = to_load.pop()
            if key in loaded:
                continue
            sub_ns = get_namespace(*key)
            loaded[key] = sub_ns
            to_load.extend(sub_ns.get_dependencies())

        # merge all type mappings
        self._types = {}
        for sub_ns in loaded.values():
            self._types.update(sub_ns.get_types())
        self._types.update(ns.get_types())

    def lookup_attr_docs(self, name):
        """Get docs for a namespace attribute.

        e.g. 'GObject.Value'
        """

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

    def lookup_signal_docs(self, name):
        if name in self._signals:
            return self._fix_docs(self._signals[name])
        return ""

    def lookup_prop_docs(self, name):
        if name in self._properties:
            return self._fix_docs(self._properties[name])
        return ""

    def get_dependencies(self):
        return self._ns.get_dependencies()

    def is_private(self, name):
        """is_private('Gtk.ViewportPrivate')"""

        assert "." in name

        return name in self._private

    def _fix_docs(self, d):
        return docstring_to_rest(self._types, d)

    def parse_constant(self, name):
        # FIXME: broken escaping in pgi
        if name.split(".")[-1][:1].isdigit():
            return

        docs = self.lookup_attr_docs(name)

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

        docs = self.lookup_attr_docs(name)

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
            docs = self.lookup_signal_docs(doc_name)

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

        # get all specs owned by the class
        specs = []
        for attr in dir(obj.props):
            if attr.startswith("_"):
                continue
            spec = getattr(obj.props, attr, None)
            if not spec or spec.owner_type.pytype is not obj:
                continue
            specs.append(spec)

        props = []
        for spec in specs:
            name = spec.name
            type_desc = gtype_to_rest(spec.value_type)
            readable = spec.flags & GObject.ParamFlags.READABLE
            writable = spec.flags & GObject.ParamFlags.WRITABLE
            construct = spec.flags & GObject.ParamFlags.CONSTRUCT
            short_desc = self._fix_docs(spec.blurb)
            doc_name = obj.__module__ + "." + obj.__name__ + "." + name
            desc = self.lookup_prop_docs(doc_name)

            props.append(Property(name, type_desc, readable, writable,
                                  construct, short_desc, desc))

        return props

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
""" % (obj.__name__, base_name, self.lookup_attr_docs(name))

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
            docs = self.lookup_attr_docs(doc_key)
            code += "    r'''\n%s\n'''\n" % docs

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
            if not self.lookup_attr_docs(name):
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
""" % (func_name, name, self.lookup_attr_docs(name))
            else:
                # for toplevel functions, replace the introspected one
                # since sphinx ignores docstrings on the module level
                # and replacing __doc__ for normal functions is possible
                return """
%s = %s
%s.__doc__ = r'''
%s
'''
""" % (func_name, name, func_name, self.lookup_attr_docs(name))

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
        elif self.lookup_attr_docs(name):
            docs.append("")
            docs.append(self.lookup_attr_docs(name))

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
