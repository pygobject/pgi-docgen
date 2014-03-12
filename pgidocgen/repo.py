# -*- coding: utf-8 -*-
# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re

from gi.repository import GObject

from .namespace import get_namespace
from . import util
from .util import unindent, gtype_to_rest

from .gtkstock import parse_stock_icon
from .funcsig import FuncSignature, py_type_to_class_ref, get_type_name
from .parser import docstring_to_rest


class Property(object):

    def __init__(self, name, attr_name, type_desc, readable, writable,
                 construct, short_desc, desc):
        self.name = name
        self.attr_name = attr_name
        self.type_desc = type_desc

        self.readable = readable
        self.writable = writable
        self.construct = construct

        self.short_desc = short_desc
        self.desc = desc

    @property
    def flags_string(self):
        flags = []
        if self.readable:
            flags.append("r")
        if self.writable:
            flags.append("w")
        if self.construct:
            flags.append("c")
        return "/".join(flags)


class Signal(object):

    def __init__(self, name, sig, flags, desc, short_desc):
        self.flags = flags
        self.desc = desc
        self.short_desc = short_desc
        self.name = name
        self.sig = sig

    @property
    def flags_string(self):
        descs = []

        for key in dir(GObject.SignalFlags):
            if key != key.upper():
                continue
            flag = getattr(GObject.SignalFlags, key)
            if self.flags & flag:
                d = ":data:`%s <GObject.SignalFlags.%s>`" % (key, key)
                descs.append(d)

        return ", ".join(descs)


class Field(object):

    def __init__(self, name, readable, writable, type_desc, desc):
        self.name = name
        self.readable = readable
        self.writable = writable
        self.type_desc = type_desc
        self.desc = desc

    @property
    def flags_string(self):
        flags = []
        if self.readable:
            flags.append("r")
        if self.writable:
            flags.append("w")
        return "/".join(flags)


class Repository(object):
    """Takes gi objects and gives documented code"""

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        self._ns = ns = get_namespace(namespace, version)

        # Gtk.foo_bar.arg1 -> "some doc"
        self._parameters = {}

        self._sig_parameters = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        self._returns = {}

        self._sreturns = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        # Gtk.FooBar -> "some doc"
        self._all = {}

        # Gtk.Foo.some-signal -> "some doc"
        self._signals = {}

        # Gtk.Foo.some-prop -> "some doc"
        self._properties = {}

        self._fields = {}

        a, pa, r, s, pr, fi, sp, sr = ns.parse_docs()
        self._all.update(a)
        self._parameters.update(pa)
        self._returns.update(r)
        self._signals.update(s)
        self._properties.update(pr)
        self._fields.update(fi)
        self._sig_parameters.update(sp)
        self._sreturns.update(sr)

        self._private = ns.parse_private()

        # merge all type mappings
        self._types = {}
        loaded = [ns] + [get_namespace(*x) for x in ns.get_all_dependencies()]
        for sub_ns in loaded:
            self._types.update(sub_ns.get_types())
        self._types.update(ns.get_types())

    def lookup_attr_docs(self, *args, **kwargs):
        return self._lookup_docs(self._all, *args, **kwargs)

    def _lookup_meta(self, source, name):
        docs = u""
        if name in source:
            version, dep_version, dep = source[name][1:]
            if version:
                docs += u"\n\n.. versionadded:: %s\n\n" % version
            if dep_version or dep:
                dep_version = dep_version or "??"
                docs += u"\n\n.. deprecated:: %s\n%s\n\n" % (
                    dep_version, util.indent(self._fix_docs(dep)))
        return docs

    def _lookup_docs(self, source, name, current=None):
        if name in source:
            docs = source[name][0]
            return self._fix_docs(docs, current)
        return u""

    def lookup_attr_meta(self, name):
        return self._lookup_meta(self._all, name)

    def lookup_field_docs(self, *args, **kwargs):
        return self._lookup_docs(self._fields, *args, **kwargs)

    def lookup_return_docs(self, *args, **kwargs):
        if kwargs.pop("signal", False):
            return self._lookup_docs(self._sreturns, *args, **kwargs)
        else:
            return self._lookup_docs(self._returns, *args, **kwargs)

    def lookup_parameter_docs(self, *args, **kwargs):
        if kwargs.pop("signal", False):
            return self._lookup_docs(self._sig_parameters, *args, **kwargs)
        else:
            return self._lookup_docs(self._parameters, *args, **kwargs)

    def lookup_signal_docs(self, name, short=False, current=None):
        if name in self._signals:
            docs = self._signals[name][0]
            if short:
                parts = re.split("\.[\s$]", docs, 1, re.MULTILINE)
                if len(parts) > 1:
                    return self._fix_docs(parts[0] + ".", current)
                else:
                    return self._fix_docs(docs, current)
            else:
                return self._fix_docs(docs, current)
        return u""

    def lookup_signal_meta(self, name):
        return self._lookup_meta(self._signals, name)

    def lookup_prop_docs(self, *args, **kwargs):
        return self._lookup_docs(self._properties, *args, **kwargs)

    def lookup_prop_meta(self, name):
        return self._lookup_meta(self._properties, name)

    def get_dependencies(self):
        return self._ns.get_dependencies()

    def is_private(self, name):
        """is_private('Gtk.ViewportPrivate')"""

        assert "." in name

        return name in self._private

    def _fix_docs(self, d, current=None):
        if not d:
            return u""
        rest = docstring_to_rest(self._types, current, d)
        return rest

    def parse_constant(self, name):
        # FIXME: broken escaping in pgi
        if name.split(".")[-1][:1].isdigit():
            return

        docs = self.lookup_attr_docs(name)

        # Add images for stock icon constants
        if name.startswith("Gtk.STOCK_"):
            docs += parse_stock_icon(name)

        docs += self.lookup_attr_meta(name)

        # sphinx gets confused by empty docstrings
        return """
%s = %s
r'''
.. fake comment to help sphinx

%s
'''

""" % (name.split(".")[-1], name, docs)

    def parse_custom_class(self, name, obj):
        return """

%s = %s

""" % (name.split(".")[-1], name)

    def parse_class(self, name, obj):
        names = []
        # prefix with the module if it's an external class
        for base in util.merge_in_overrides(obj):
            base_name = base.__name__
            if base_name != "object":
                base_name = base.__module__ + "." + base_name
            names.append(base_name)
        bases = ", ".join(names or ["object"])

        name = str(name)
        current_rst_target = obj.__module__ + "." + obj.__name__
        docs = self.lookup_attr_docs(name, current=current_rst_target)
        docs += self.lookup_attr_meta(name)

        return """
class %s(%s):
    r'''
%s
    '''

    __init__ = %s.__init__

""" % (name.split(".")[-1], bases, docs.encode("utf-8"), name)

    def parse_signals(self, obj):
        assert util.is_object(obj) or util.is_iface(obj)

        current_rst_target = obj.__module__ + "." + obj.__name__

        if not hasattr(obj, "signals"):
            return []

        result = []
        for attr, sig in util.iter_public_attr(obj.signals):
            doc_key = obj.__module__ + "." + obj.__name__ + "." + sig.name

            try:
                fsig = FuncSignature.from_string(attr, sig.__doc__)
                assert fsig, (doc_key, sig.__doc__)
            except NotImplementedError:
                # FIXME pgi
                print "FIXME: signal: %s " % doc_key
                desc = "(FIXME pgi-docgen: arguments are missing here)"
                ssig = "%s(*fixme)" % attr
            else:
                ssig = fsig.to_simple_signature()
                desc = fsig.to_rest_listing(
                    self, doc_key, current=current_rst_target, signal=True)

            desc += "\n\n"
            desc += self.lookup_signal_docs(doc_key, current=current_rst_target)
            desc += self.lookup_signal_meta(doc_key)
            short_desc = self.lookup_signal_docs(
                doc_key, short=True, current=current_rst_target)

            result.append(Signal(sig.name, ssig, sig.flags, desc, short_desc))

        return result

    def parse_fields(self, obj):
        current_rst_target = obj.__module__ + "." + obj.__name__

        fields = []
        for attr, field_info in util.iter_public_attr(obj):
            if not util.is_field(field_info):
                continue

            py_type = field_info.py_type
            type_name = get_type_name(py_type)
            if "." in type_name and self.is_private(type_name):
                continue

            name = field_info.name
            type_desc = py_type_to_class_ref(field_info.py_type)
            readable = field_info.readable
            writable = field_info.writeable
            doc_name = current_rst_target + "." + name
            desc = self.lookup_field_docs(doc_name, current=current_rst_target)
            fields.append(Field(name, readable, writable, type_desc, desc))

        return fields

    def parse_properties(self, obj):
        assert util.is_object(obj) or util.is_iface(obj)

        current_rst_target = obj.__module__ + "." + obj.__name__

        if not hasattr(obj, "props"):
            return []

        # get all specs owned by the class
        specs = []
        for attr, spec in util.iter_public_attr(obj.props):
            if not spec or spec.owner_type.pytype is not obj:
                continue
            specs.append((attr, spec))

        props = []
        for attr_name, spec in specs:
            name = spec.name
            type_desc = gtype_to_rest(spec.value_type)
            readable = spec.flags & GObject.ParamFlags.READABLE
            writable = spec.flags & GObject.ParamFlags.WRITABLE
            construct = spec.flags & GObject.ParamFlags.CONSTRUCT
            if spec.blurb is not None:
                short_desc = self._fix_docs(
                    spec.blurb, current=current_rst_target)
            else:
                short_desc = ""
            doc_key = obj.__module__ + "." + obj.__name__ + "." + name
            desc = self.lookup_prop_docs(
                doc_key, current=current_rst_target) or short_desc
            desc += self.lookup_prop_meta(doc_key)

            props.append(Property(name, attr_name, type_desc, readable,
                                  writable, construct, short_desc, desc))

        return props

    def parse_flags(self, name, obj):
        from gi.repository import GObject

        # the base classes themselves: reference the real ones
        if obj in (GObject.GFlags, GObject.GEnum):
            return "%s = GObject.%s" % (obj.__name__, obj.__name__)

        base = obj.__bases__[0]
        base_name = base.__module__ + "." + base.__name__

        docs = self.lookup_attr_docs(name)
        docs += self.lookup_attr_meta(name)

        code = """
class %s(%s):
    r'''
%s
    '''
""" % (obj.__name__, base_name, docs)

        for attr, attr_obj in util.iter_public_attr(obj):
            if not callable(attr_obj):
                continue

            if not util.is_method_owner(obj, attr):
                continue

            func_key = name + "." + attr
            code += util.indent(self.parse_function(func_key, obj, attr_obj))
            code += "\n\n"

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
            docs += self.lookup_attr_meta(doc_key)
            code += "    r'''\n%s\n'''\n" % docs

        name = obj.__name__
        for v in escaped:
            code += "setattr(%s, '%s', %s)\n" % (name, v, "%s._%s" % (name, v))

        return code

    def parse_function(self, name, owner, obj):
        """Returns python code for the object"""

        is_method = owner is not None

        if is_method:
            current_rst_target = owner.__module__ + "." + owner.__name__

            # for methods, add the docstring after
            def get_func_def(func_name, name, docs):
                return """
%s = %s
r'''
%s
'''
""" % (func_name, name, docs)

        else:
            current_rst_target = None

            # for toplevel functions, replace the introspected one
            # since sphinx ignores docstrings on the module level
            # and replacing __doc__ for normal functions is possible
            def get_func_def(func_name, name, docs):
                return """
%s = %s
%s.__doc__ = r'''
%s
'''
""" % (func_name, name, func_name, docs)

        def get_sig(obj):
            doc = str(obj.__doc__ or "")
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
            # add the versionadded from the gir here too
            docs = str(obj.__doc__ or "")
            docs += self.lookup_attr_meta(name)
            return get_func_def(func_name, name, docs)

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
            # INFO: this probably only happens if there is an override
            # for something pgi doesn't support. The base class
            # is missing the real one, but the gir docs may be still there

            docs = self.lookup_attr_docs(name, current=current_rst_target)
            if not docs:
                docs = str(obj.__doc__ or "")
            docs += self.lookup_attr_meta(name)
            return get_func_def(func_name, name, docs)

        # we got a valid signature here
        assert sig

        docstring = str(obj.__doc__ or "")
        # the docstring contains additional text, propably an override
        # or internal function (GObject.Object methods for example)
        lines = docstring.splitlines()[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
        user_docstring = "\n".join(lines)

        # create sphinx lists for the signature we found
        docs = sig.to_rest_listing(
            self, name, current=current_rst_target).splitlines()
        docs = "\n".join(docs)

        if util.is_virtualmethod(obj):
            docs = ":Type: virtual\n\n" + docs

        # if we have a user docstring, use it, otherwise use the gir one
        if user_docstring:
            docs += "\n\n" + unindent(user_docstring)
        elif self.lookup_attr_docs(name):
            docs += "\n\n" + self.lookup_attr_docs(name,
                                                   current=current_rst_target)
            docs += self.lookup_attr_meta(name)

        if is_method:
            # Rewrap them here so spinx knows that they static and
            # we can use that information in the autosummary extension.
            # If we wrap a classmethod in another one sphinx doesn't
            # pick up the function signature.. so only use staticmethod.
            if util.is_staticmethod(obj) or util.is_classmethod(obj):
                name = "staticmethod(%s)" % name

        return get_func_def(func_name, name, docs)
