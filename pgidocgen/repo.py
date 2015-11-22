# -*- coding: utf-8 -*-
# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re
import inspect

from gi.repository import GObject

from .namespace import get_namespace
from . import util
from .util import unindent, cache_calls

from .funcsig import FuncSignature, py_type_to_class_ref, get_type_name
from .parser import docstring_to_rest
from .girdata import get_source_to_url_func, get_project_version


def get_signature_string(callable_):
    try:
        argspec = inspect.getargspec(callable_)
    except TypeError:
        # ... is not a Python function
        return u"()"
    if argspec[0] and argspec[0][0] in ('cls', 'self'):
        del argspec[0][0]
    return inspect.formatargspec(*argspec)


class BaseDocObject(object):

    name = None
    fullname = None

    def __repr__(self):
        return "<%s fullname=%s name=%s>" % (
            type(self).__name__, self.fullname, self.name)


class SignalsMixin(object):

    def _parse_signals(self, repo, obj):
        if not hasattr(obj, "signals"):
            self.signals = []
            return

        signals = []
        for attr_name,  sig in util.iter_public_attr(obj.signals):
            signals.append(
                Signal.from_object(repo, attr_name, self.fullname, sig))
        signals.sort(key=lambda s: s.name)
        self.signals = signals


class MethodsMixin(object):

    def get_methods(self, static=False):
        methods = []
        for m in self.methods:
            if m.is_static == static:
                methods.append(m)
        methods.sort(key=lambda x: x.name)
        return methods

    def _parse_methods(self, repo, obj):
        methods = []
        vfuncs = []
        for attr, attr_obj in util.iter_public_attr(obj):
            if not callable(attr_obj):
                continue

            if not util.is_method_owner(obj, attr):
                continue

            func = Function.from_object(self.fullname, attr_obj, repo, obj)
            if func.is_vfunc:
                vfuncs.append(func)
            else:
                methods.append(func)

        methods.sort(key=lambda m: m.name)
        vfuncs.sort(key=lambda m: m.name)
        self.methods = methods
        self.vfuncs = vfuncs


class PropertiesMixin(object):

    def _parse_properties(self, repo, obj):
        if not hasattr(obj, "props"):
            self.properties = []
            return

        # get all specs owned by the class
        specs = []
        for attr, spec in util.iter_public_attr(obj.props):
            if not spec or spec.owner_type.pytype is not obj:
                continue
            specs.append((attr, spec))

        props = []
        for attr_name, spec in specs:
            prop = Property.from_prop_spec(
                repo, self.fullname, attr_name, spec)
            props.append(prop)
        self.properties = props


class ChildPropertiesMixin(object):

    def _parse_child_properties(self, repo, obj):
        props = []
        for spec in util.get_child_properties(obj):
            prop = Property.from_child_pspec(repo, self.fullname, spec)
            props.append(prop)
        props.sort(key=lambda p: p.name)
        self.child_properties = props


class StylePropertiesMixin(object):

    def _parse_style_properties(self, repo, obj):
        props = []
        for spec in util.get_style_properties(obj):
            prop = Property.from_child_pspec(repo, self.fullname, spec)
            props.append(prop)
        props.sort(key=lambda p: p.name)
        self.style_properties = props


class FieldsMixin(object):

    def _parse_fields(self, repo, obj):
        fields = []
        for attr, field_info in util.iter_public_attr(obj):
            if not util.is_field(field_info):
                continue
            if not util.is_field_owner(obj, attr):
                continue

            py_type = field_info.py_type
            type_name = get_type_name(py_type)
            if "." in type_name and repo.is_private(type_name):
                continue

            name = field_info.name
            type_desc = py_type_to_class_ref(field_info.py_type)
            readable = field_info.readable
            writable = field_info.writeable
            doc_name = self.fullname + "." + name
            desc = repo.lookup_field_docs(
                doc_name, current=self.fullname)
            fields.append(
                Field(self.fullname, name, readable, writable,
                      type_desc, desc))

        fields.sort(key=lambda f: f.name)
        self.fields = fields


class Property(BaseDocObject):

    def __init__(self, parent_fullname, name, attr_name,
                 readable, writable, construct, type_desc, value_desc):
        self.fullname = parent_fullname + "." + name
        self.name = name
        self.attr_name = attr_name

        self.readable = readable
        self.writable = writable
        self.construct = construct

        self.type_desc = type_desc
        self.value_desc = value_desc

        self.short_desc = None
        self.desc = None

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

    @classmethod
    def from_child_pspec(cls, repo, parent_fullname, spec):
        """Returns a Property for a ParamSpec"""

        # WARNING: the ParamSpecs classes here aren't the same as for
        # properties, they come from the GIR not pgi internals..
        attr_name = ""
        name = spec.get_name()
        default_value = spec.get_default_value()
        if isinstance(default_value, GObject.Value):
            default_value = default_value.get_value()
        value_desc = util.instance_to_rest(
            spec.value_type.pytype, default_value)
        type_desc = py_type_to_class_ref(spec.value_type.pytype)
        readable = spec.flags & GObject.ParamFlags.READABLE
        writable = spec.flags & GObject.ParamFlags.WRITABLE
        construct = spec.flags & GObject.ParamFlags.CONSTRUCT

        prop = cls(parent_fullname, name, attr_name,
                   readable, writable, construct,
                   type_desc, value_desc)

        if spec.get_blurb() is not None:
            short_desc = repo._fix_docs(
                spec.get_blurb(), current=parent_fullname)
        else:
            short_desc = u""
        desc = u""

        prop.short_desc = short_desc
        prop.desc = desc

        return prop

    @classmethod
    def from_prop_spec(cls, repo, parent_fullname, attr_name, spec):
        name = spec.name
        value_desc = util.instance_to_rest(
            spec.value_type.pytype, spec.default_value)
        type_desc = py_type_to_class_ref(spec.value_type.pytype)
        readable = spec.flags & GObject.ParamFlags.READABLE
        writable = spec.flags & GObject.ParamFlags.WRITABLE
        construct = spec.flags & GObject.ParamFlags.CONSTRUCT
        if spec.blurb is not None:
            short_desc = repo._fix_docs(
                spec.blurb, current=parent_fullname)
        else:
            short_desc = u""

        prop = cls(parent_fullname, name, attr_name,
                   readable, writable, construct,
                   type_desc, value_desc)

        desc = repo.lookup_prop_docs(
            prop.fullname, current=parent_fullname) or short_desc
        desc += repo.lookup_prop_meta(prop.fullname)
        prop.desc = desc
        prop.short_desc = short_desc

        return prop


class Signal(BaseDocObject):

    def __init__(self, parent_fullname, name, attr_name, sig, flags):
        self.fullname = parent_fullname + "." + name
        self.flags = flags
        self.name = name
        self.attr_name = attr_name
        self.sig = sig
        self.desc = None
        self.short_desc = None

    @classmethod
    def from_object(cls, repo, attr_name, parent_fullname, sig):
        try:
            fsig = FuncSignature.from_string(attr_name, sig.__doc__)
            assert fsig, sig.__doc__
        except NotImplementedError:
            fsig = None
            ssig = "%s(*fixme)" % attr
        else:
            ssig = fsig.to_simple_signature()

        inst = cls(parent_fullname, sig.name, attr_name, ssig, sig.flags)

        if fsig:
            desc = fsig.to_rest_listing(
                repo, inst.fullname, current=parent_fullname, signal=True)
        else:
            # FIXME pgi
            print "FIXME: signal: %s " % doc_key
            desc = "(FIXME pgi-docgen: arguments are missing here)"

        desc += "\n\n"
        desc += repo.lookup_signal_docs(inst.fullname, current=parent_fullname)
        desc += repo.lookup_signal_meta(inst.fullname)
        short_desc = repo.lookup_signal_docs(
            inst.fullname, short=True, current=parent_fullname)

        inst.desc = desc
        inst.short_desc = short_desc
        return inst

    @property
    def flags_string(self):
        descs = []

        for key in dir(GObject.SignalFlags):
            if key != key.upper():
                continue
            flag = getattr(GObject.SignalFlags, key)
            if self.flags & flag:
                d = ":obj:`%s <GObject.SignalFlags.%s>`" % (key, key)
                descs.append(d)

        return ", ".join(descs)


class PyClass(BaseDocObject, MethodsMixin):

    def __init__(self, namespace, name):
        self.fullname = namespace + "." + name
        self.name = name

    @classmethod
    def from_object(cls, repo, obj):
        namespace = obj.__module__
        name = obj.__name__

        return cls(namespace, name)


class Class(BaseDocObject, MethodsMixin, PropertiesMixin, SignalsMixin,
            ChildPropertiesMixin, StylePropertiesMixin, FieldsMixin):

    def __init__(self, namespace, name):
        self.fullname = namespace + "." + name
        self.name = name
        self.desc = None
        self.image_name = None
        self.is_interface = False
        self.signature = None

        self.methods = []
        self.methods_inherited = []

        self.vfuncs = []
        self.vfuncs_inherited = []

        self.properties = []
        self.properties_inherited = []

        self.signals = []
        self.signals_inherited = []

        self.fields = []
        self.fields_inherited = []

        self.child_properties = []
        self.child_properties_inherited = []

        self.style_properties = []
        self.style_properties_inherited = []

        self.base_tree = []
        self.subclasses = []

    @property
    def bases(self):
        return [c[0] for c in self.base_tree[0][1]]

    @classmethod
    def from_object(cls, repo, obj):
        namespace = obj.__module__
        name = obj.__name__

        def get_base_tree(obj):
            x = []
            for base in util.fake_bases(obj):
                if base is object:
                    continue
                x.append((base.__module__ + "."  + base.__name__,
                          get_base_tree(base)))
            return x

        klass = cls(namespace, name)
        klass._parse_methods(repo, obj)
        klass._parse_properties(repo, obj)
        klass._parse_child_properties(repo, obj)
        klass._parse_style_properties(repo, obj)
        klass._parse_signals(repo, obj)
        klass._parse_fields(repo, obj)
        klass.image_name = util.get_image_name(
            repo.namespace, repo.version, klass.fullname)

        docs = repo.lookup_attr_docs(klass.fullname, current=klass.fullname)
        docs += repo.lookup_attr_meta(klass.fullname)
        klass.desc = docs
        klass.is_interface = util.is_iface(obj)
        klass.base_tree = [(klass.fullname, get_base_tree(obj))]

        def iter_bases(obj):
            for base in util.fake_mro(obj):
                if base is object or base is obj:
                    continue
                yield repo.parse_class(base)

        inherited = {}
        inherit_types = ["vfuncs", "methods", "properties", "signals",
                         "fields", "child_properties", "style_properties"]
        for cls in iter_bases(obj):
            for type_ in inherit_types:
                attr = getattr(cls, type_)
                if len(attr):
                    inherited.setdefault(type_, []).append(
                        (cls.fullname, len(attr)))
        for type_ in inherit_types:
            setattr(klass, type_ + "_inherited", inherited.get(type_, []))

        subclasses = []
        for cls in util.fake_subclasses(obj):
            if cls.__module__ == namespace:
                subclasses.append(cls.__module__ + "." + cls.__name__)
        subclasses.sort()
        klass.subclasses = subclasses
        klass.signature = get_signature_string(obj.__init__)

        return klass


class Field(BaseDocObject):

    def __init__(self, parent_fullname, name, readable, writable, type_desc, desc):
        self.fullname = parent_fullname + "." + name
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


class Function(BaseDocObject):

    def __init__(self, parent_fullname, name, is_method, is_static, is_vfunc,
                 signature, desc):
        self.fullname = parent_fullname + "." + name
        self.name = name
        self.is_method = is_method
        self.is_static = is_static
        self.is_vfunc = is_vfunc
        self.signature = signature
        self.desc = desc

    @classmethod
    def from_object(cls, parent_fullname, obj, repo, owner):

        name = obj.__name__
        fullname = parent_fullname + "." + name
        is_method = owner is not None

        signature = get_signature_string(obj)

        if is_method:
            current_rst_target = parent_fullname
            is_static = util.is_staticmethod(obj)
            is_vfunc = util.is_virtualmethod(obj)
        else:
            current_rst_target = None
            is_static = False
            is_vfunc = False

        def get_instance(docs):
            return cls(
                parent_fullname, name, is_method, is_static, is_vfunc,
                signature, docs)

        def get_sig(obj):
            doc = str(obj.__doc__ or "")
            first_line = doc and doc.splitlines()[0] or ""
            return FuncSignature.from_string(name, first_line)

        sig = get_sig(obj)

        # no valid sig, but still a docstring, probably new function
        # or an override with a new docstring
        if not sig and obj.__doc__:
            # add the versionadded from the gir here too
            docs = str(obj.__doc__ or "")
            docs += repo.lookup_attr_meta(fullname)
            return get_instance(docs)

         # no docstring, try to get the signature from base classes
        if not sig and owner:
            for base in owner.__mro__[1:]:
                try:
                    base_obj = getattr(base, name, None)
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

            docs = repo.lookup_attr_docs(fullname, current=current_rst_target)
            if not docs:
                docs = str(obj.__doc__ or "")
            docs += repo.lookup_attr_meta(fullname)
            return get_instance(docs)

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
            repo, fullname, current=current_rst_target).splitlines()
        docs = "\n".join(docs)

        # if we have a user docstring, use it, otherwise use the gir one
        if user_docstring:
            docs += "\n\n" + unindent(user_docstring)
        elif repo.lookup_attr_docs(fullname):
            docs += "\n\n" + repo.lookup_attr_docs(fullname,
                                                   current=current_rst_target)
            docs += repo.lookup_attr_meta(fullname)

        return get_instance(docs)


class Structure(BaseDocObject, MethodsMixin, FieldsMixin):

    def __init__(self, namespace, name, signature):
        self.fullname = namespace + "." + name
        self.name = name
        self.signature = signature
        self.desc = None
        self.methods = []
        self.fields = []

    @classmethod
    def from_object(cls, repo, obj):
        signature = get_signature_string(obj.__init__)
        instance = cls(obj.__module__, obj.__name__, signature)

        docs = repo.lookup_attr_docs(instance.fullname,
                                     current=instance.fullname)
        docs += repo.lookup_attr_meta(instance.fullname)
        instance._parse_methods(repo, obj)
        instance._parse_fields(repo, obj)
        instance.desc = docs
        return instance


class Union(Structure):
    pass


class Flags(BaseDocObject, MethodsMixin):

    def __init__(self, namespace, name):
        self.fullname = namespace + "." + name
        self.name = name
        self.desc = None
        self.values = []
        self.methods = []

    def _parse_values(self, repo, obj):
        values = []
        for attr_name in dir(obj):
            if attr_name.upper() != attr_name:
                continue
            attr = getattr(obj, attr_name)
            if not isinstance(attr, obj):
                continue

            flag_value = Constant.from_object(
                repo, self.fullname, attr_name, int(attr))
            values.append((int(attr), flag_value))

        values.sort()
        self.values = [v[1] for v in values]

    @classmethod
    def from_object(cls, repo, obj):
        instance = cls(obj.__module__, obj.__name__)
        docs = repo.lookup_attr_docs(instance.fullname)
        docs += repo.lookup_attr_meta(instance.fullname)
        instance.desc = docs
        instance._parse_values(repo, obj)
        instance._parse_methods(repo, obj)
        return instance


class Constant(BaseDocObject):

    def __init__(self, parent_fullname, name, value):
        self.fullname = parent_fullname + "." + name
        self.name = name
        self.value = value
        self.desc = None

    @classmethod
    def from_object(cls, repo, parent_fullname, name, obj):
        instance = Constant(parent_fullname, name, repr(obj))
        docs = repo.lookup_attr_docs(instance.fullname)
        docs += repo.lookup_attr_meta(instance.fullname)
        instance.desc = docs
        return instance


class SymbolMapping(object):

    def __init__(self, symbol_map, source_map):
        self.symbol_map = symbol_map # [(c sym, py sym)]
        self.source_map = source_map # {py sym: git url}

    @classmethod
    def from_repo(cls, repo, module):
        lib_version = get_project_version(module)
        func = get_source_to_url_func(repo.namespace, lib_version)
        source_map = {}
        if func:
            source = repo.get_source()
            for key, value in source.iteritems():
                source_map[key] = func(value)

        symbol_map = []
        items = repo.get_types().iteritems()
        for key, values in sorted(items, key=lambda x: x[0].lower()):
            for value in values:
                if not value.startswith(repo.namespace + "."):
                    continue
                if repo.is_private(value):
                    continue
                symbol_map.append((key, value))
        return cls(symbol_map, source_map)


class Repository(object):
    """Takes gi objects and gives documentation objects"""

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

    def get_types(self):
        return self._types

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

    def get_source(self):
        return self._ns.get_source()

    def is_private(self, name):
        """is_private('Gtk.ViewportPrivate')"""

        assert "." in name

        return name in self._private

    def _fix_docs(self, d, current=None):
        if not d:
            return u""
        rest = docstring_to_rest(self._types, current, d)
        return rest

    def parse_constant(self, namespace, name, obj):
        return Constant.from_object(self, namespace, name, obj)

    def parse_structure(self, obj):
        return Structure.from_object(self, obj)

    def parse_union(self, obj):
        return Union.from_object(self, obj)

    @cache_calls
    def parse_class(self, obj):
        return Class.from_object(self, obj)

    def parse_pyclass(self, obj):
        return PyClass.from_object(self, obj)

    def parse_flags(self, obj):
        return Flags.from_object(self, obj)

    def parse_enum(self, obj):
        return Flags.from_object(self, obj)

    def parse_function(self, namespace, obj):
        return Function.from_object(namespace, obj, self, None)

    def parse_mapping(self, module):
        return SymbolMapping.from_repo(self, module)
