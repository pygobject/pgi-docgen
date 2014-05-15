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
from .util import unindent, gtype_to_rest, escape_identifier

from .funcsig import FuncSignature, py_type_to_class_ref, get_type_name
from .parser import docstring_to_rest


class Property(object):

    def __init__(self, name, attr_name, type_desc, readable, writable,
                 construct, short_desc, desc, value_desc):
        self.name = name
        self.attr_name = attr_name
        self.type_desc = type_desc
        self.value_desc = value_desc

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


class Method(object):

    def __init__(self, name, is_static, is_vfunc, code):
        self.name = name
        self.is_static = is_static
        self.code = code
        self.is_vfunc = is_vfunc



def cache_calls(func):
    _cache = {}
    def wrap(*args):
        if len(_cache) > 100:
            _cache.clear()
        if args not in _cache:
            _cache[args] = func(*args)
        return _cache[args]
    return wrap


class Repository(object):
    """Takes gi objects and gives documented code"""

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        self._ns = ns = get_namespace(namespace, version)
        self._docs = ns.parse_docs()
        self._private = ns.parse_private()

        # merge all type mappings
        self._types = {}
        loaded = [ns] + [get_namespace(*x) for x in ns.get_all_dependencies()]
        for sub_ns in loaded:
            self._types.update(sub_ns.get_types())
        self._types.update(ns.get_types())

    def lookup_attr_docs(self, *args, **kwargs):
        docs = self._lookup_docs("all", *args, **kwargs)
        shadowed = self._lookup_docs("all_shadowed", *args, **kwargs)
        if shadowed and shadowed != docs:
            docs += """

.. note::

    This function is an alternative implementation for bindings. The following
    text is the documentation of the original, replaced function, which might
    include additional information:

%s
""" % util.indent(util.indent(shadowed))
        return docs

    def _lookup_meta(self, source, name):
        source = self._docs[source]

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
        source = self._docs[source]
        if name in source:
            docs = source[name][0]
            return self._fix_docs(docs, current)
        return u""

    def lookup_attr_meta(self, name):
        return self._lookup_meta("all", name)

    def lookup_field_docs(self, *args, **kwargs):
        return self._lookup_docs("fields", *args, **kwargs)

    def lookup_return_docs(self, *args, **kwargs):
        if kwargs.pop("signal", False):
            return self._lookup_docs("signal-returns", *args, **kwargs)
        else:
            return self._lookup_docs("returns", *args, **kwargs)

    def lookup_parameter_docs(self, *args, **kwargs):
        if kwargs.pop("signal", False):
            return self._lookup_docs("signal-parameters", *args, **kwargs)
        else:
            return self._lookup_docs("parameters", *args, **kwargs)

    def lookup_signal_docs(self, name, short=False, current=None):
        source = self._docs["signals"]
        if name in source:
            docs = source[name][0]
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
        return self._lookup_meta("signals", name)

    def lookup_prop_docs(self, *args, **kwargs):
        return self._lookup_docs("properties", *args, **kwargs)

    def lookup_prop_meta(self, name):
        return self._lookup_meta("properties", name)

    def get_dependencies(self):
        return self._ns.get_dependencies()

    def get_all_dependencies(self):
        return self._ns.get_all_dependencies()

    def import_module(self):
        return self._ns.import_module()

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
        for base in util.fake_bases(obj):
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

    @cache_calls
    def parse_signals(self, obj):
        if not (util.is_object(obj) or util.is_iface(obj)):
            return []

        current_rst_target = obj.__module__ + "." + obj.__name__

        if not hasattr(obj, "signals"):
            return []

        result = []
        for attr, sig in util.iter_public_attr(obj.signals):
            doc_key = obj.__module__ + "." + obj.__name__ + "." + \
                escape_identifier(sig.name)

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

    def get_signal_count(self, obj):
        return len(self.parse_signals(obj))

    @cache_calls
    def parse_fields(self, obj):
        current_rst_target = obj.__module__ + "." + obj.__name__

        fields = []
        for attr, field_info in util.iter_public_attr(obj):
            if not util.is_field(field_info):
                continue
            if not util.is_field_owner(obj, attr):
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

    def get_field_count(self, obj):
        return len(self.parse_fields(obj))

    @cache_calls
    def parse_child_properties(self, obj):
        # fast path..
        if obj.__module__ != "Gtk":
            return []

        if not (util.is_object(obj) or util.is_iface(obj)):
            return []

        current_rst_target = obj.__module__ + "." + obj.__name__

        props = []
        # WARNING: the ParamSpecs classes here aren't the same as for
        # properties, they come from the GIR not pgi internals..
        for spec in util.get_child_properties(obj):
            attr_name = ""
            name = spec.get_name()
            default_value = spec.get_default_value()
            if isinstance(default_value, GObject.Value):
                default_value = default_value.get_value()
            value_desc = util.instance_to_rest(
                spec.value_type.pytype, default_value)
            type_desc = gtype_to_rest(spec.value_type)
            readable = spec.flags & GObject.ParamFlags.READABLE
            writable = spec.flags & GObject.ParamFlags.WRITABLE
            construct = spec.flags & GObject.ParamFlags.CONSTRUCT
            if spec.get_blurb() is not None:
                short_desc = self._fix_docs(
                    spec.get_blurb(), current=current_rst_target)
            else:
                short_desc = ""
            desc = u""

            props.append(Property(name, attr_name, type_desc, readable,
                      writable, construct, short_desc, desc,
                      value_desc))

        return props

    @cache_calls
    def parse_properties(self, obj):
        if not (util.is_object(obj) or util.is_iface(obj)):
            return []

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
            value_desc = util.instance_to_rest(
                spec.value_type.pytype, spec.default_value)
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
                                  writable, construct, short_desc, desc,
                                  value_desc))

        return props

    def get_property_count(self, obj):
        return len(self.parse_properties(obj))

    def get_child_property_count(self, obj):
        return len(self.parse_child_properties(obj))

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

    @cache_calls
    def parse_methods(self, obj):
        name = obj.__module__ + "." + obj.__name__

        methods = []
        for attr, attr_obj in util.iter_public_attr(obj):
            # can fail for the base class
            try:
                if not util.is_method_owner(obj, attr):
                    continue
            except NotImplementedError:
                continue

            if callable(attr_obj):
                func_key = name + "." + attr
                code = self.parse_function(func_key, obj, attr_obj)
                code = code or ""
                is_vfunc = util.is_virtualmethod(attr_obj)
                is_static = not util.is_normalmethod(attr_obj)
                methods.append(Method(attr, is_static, is_vfunc, code))

        return methods

    def get_method_count(self, obj):
        return len([m for m in self.parse_methods(obj) if not m.is_vfunc])

    def get_vfunc_count(self, obj):
        return len([m for m in self.parse_methods(obj) if m.is_vfunc])

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
