# -*- coding: utf-8 -*-
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import re
import types
import inspect

from gi.repository import GObject

from . import util
from .funcsig import FuncSignature, py_type_to_class_ref, get_type_name
from .girdata import get_source_to_url_func, get_project_version, \
    get_project_summary, get_class_image_path
from .util import escape_parameter
from .parser import docstring_to_rest


def get_signature_string(callable_):
    try:
        argspec = inspect.getargspec(callable_)
    except TypeError:
        # ... is not a Python function
        return u"()"
    if argspec[0] and argspec[0][0] in ('cls', 'self'):
        del argspec[0][0]
    return inspect.formatargspec(*argspec)


def get_hierarchy(type_seq):
    """Returns for a sequence of classes a recursive dict including
    all their sub classes.
    """

    def first_mro(obj):
        l = [obj]
        bases = util.fake_bases(obj)
        if bases[0] is not object:
            l.extend(first_mro(bases[0]))
        return l

    tree = {}
    for type_ in type_seq:
        current = tree
        for base in reversed(first_mro(type_)):
            if base not in current:
                current[base] = {}
            current = current[base]
    return tree


def class_name(cls):
    return cls.__module__.split(".")[-1] + "." + cls.__name__


def to_names(hierarchy):

    return sorted(
            [(class_name(k), to_names(v)) for (k, v) in hierarchy.iteritems()])


def to_short_desc(docs):
    """Extracts the first sentence."""

    parts = re.split("\.[\s$]", docs, 1, re.MULTILINE)
    if len(parts) > 1:
        return parts[0] + "."
    else:
        return docs


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
        for attr_name, sig in util.iter_public_attr(obj.signals):
            signals.append(Signal.from_object(repo, self.fullname, sig))
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

            fields.append(
                Field.from_object(repo, self.fullname, field_info))

        fields.sort(key=lambda f: f.name)
        self.fields = fields


class Property(BaseDocObject):

    def __init__(self, parent_fullname, name, prop_name, flags,
                 type_desc, value_desc):
        self.fullname = parent_fullname + "." + name
        self.name = name
        self.info = None

        self.prop_name = prop_name
        self.flags = flags
        self.type_desc = type_desc
        self.value_desc = value_desc
        self.short_desc = None

    @property
    def flags_short(self):
        flags = []
        for key in sorted(dir(GObject.ParamFlags)):
            if key != key.upper():
                continue
            flag = getattr(GObject.ParamFlags, key)
            if bin(flag).count("1") != 1:
                continue
            if key.startswith(("PRIVATE", "STATIC")):
                continue

            if self.flags & flag:
                flags.append((
                    flag, "".join([p[:1] for p in key.split("_")]).lower()))
        return "/".join([x[1] for x in sorted(flags)])

    @property
    def flags_string(self):
        descs = []

        for key in sorted(dir(GObject.ParamFlags)):
            if key != key.upper():
                continue
            flag = getattr(GObject.ParamFlags, key)
            if bin(flag).count("1") != 1:
                continue
            if key.startswith(("PRIVATE", "STATIC")):
                continue

            if self.flags & flag:
                d = ":obj:`%s <GObject.ParamFlags.%s>`" % (key, key)
                descs.append((flag, d))

        return ", ".join([x[1] for x in sorted(descs)])

    @classmethod
    def from_child_pspec(cls, repo, parent_fullname, spec):
        """Returns a Property for a ParamSpec"""

        # WARNING: the ParamSpecs classes here aren't the same as for
        # properties, they come from the GIR not pgi internals..
        name = spec.get_name()
        default_value = spec.get_default_value()
        if isinstance(default_value, GObject.Value):
            default_value = default_value.get_value()
        value_desc = util.instance_to_rest(
            spec.value_type.pytype, default_value)
        type_desc = py_type_to_class_ref(spec.value_type.pytype)

        prop = cls(parent_fullname, escape_parameter(name), name, spec.flags,
                   type_desc, value_desc)

        prop.info = DocInfo(prop.fullname, prop.name)

        if spec.flags & GObject.ParamFlags.DEPRECATED:
            prop.info.deprecated = True

        if spec.get_blurb() is not None:
            short_desc = docstring_to_rest(
                repo, spec.get_blurb().decode("utf-8"),
                current_type=parent_fullname)
        else:
            short_desc = u""

        prop.short_desc = short_desc
        return prop

    @classmethod
    def from_prop_spec(cls, repo, parent_fullname, attr_name, spec):
        name = spec.name
        value_desc = util.instance_to_rest(
            spec.value_type.pytype, spec.default_value)
        type_desc = py_type_to_class_ref(spec.value_type.pytype)

        prop = cls(parent_fullname, escape_parameter(name), name, spec.flags,
                   type_desc, value_desc)

        if spec.blurb is not None:
            short_desc = docstring_to_rest(
                repo, spec.blurb.decode("utf-8"),
                current_type=parent_fullname)
        else:
            short_desc = u""

        prop.info = DocInfo.from_object(repo, "properties", prop,
                                        current_type=parent_fullname)
        if spec.flags & GObject.ParamFlags.DEPRECATED:
            prop.info.deprecated = True
        if not prop.info.desc:
            prop.info.desc = short_desc
        prop.short_desc = short_desc

        return prop


class Signal(BaseDocObject):

    def __init__(self, parent_fullname, name, sig_name, flags):
        self.fullname = parent_fullname + "." + name
        self.name = name
        self.info = None

        self.sig_name = sig_name
        self.flags = flags
        self.signature_desc = None
        self.short_desc = None

    @classmethod
    def from_object(cls, repo, parent_fullname, sig):
        name = escape_parameter(sig.name)
        inst = cls(parent_fullname, name, sig.name, sig.flags)

        try:
            fsig = FuncSignature.from_string(name, sig.__doc__)
            assert fsig, (sig.__doc__, name)
        except NotImplementedError:
            fsig = None
            ssig = "%s(*fixme)" % name
        else:
            ssig = fsig.to_simple_signature()

        inst.signature = ssig

        if fsig:
            signature_desc = fsig.to_rest_listing(
                repo, inst.fullname, signal=True)
        else:
            # FIXME pgi
            print "FIXME: signal: %s " % inst.fullname
            signature_desc = "(FIXME pgi-docgen: arguments are missing here)"

        inst.signature_desc = signature_desc
        inst.info = DocInfo.from_object(repo, "signals", inst,
                                        current_type=parent_fullname)
        if sig.flags & GObject.SignalFlags.DEPRECATED:
            inst.info.deprecated = True
        inst.short_desc = to_short_desc(inst.info.desc)
        return inst

    @property
    def flags_string(self):
        descs = []

        for key in sorted(dir(GObject.SignalFlags)):
            if key != key.upper():
                continue
            flag = getattr(GObject.SignalFlags, key)
            if self.flags & flag:
                d = ":obj:`%s <GObject.SignalFlags.%s>`" % (key, key)
                descs.append((flag, d))

        return ", ".join([x[1] for x in sorted(descs)])


class PyClass(BaseDocObject, MethodsMixin):

    def __init__(self, namespace, name):
        self.fullname = namespace + "." + name
        self.name = name

    @classmethod
    def from_object(cls, repo, obj):
        namespace = obj.__module__
        name = obj.__name__

        return cls(namespace, name)


class ClassNode(object):

    def __init__(self, name, is_interface, is_abstract):
        self.name = name
        self.is_interface = is_interface
        self.is_abstract = is_abstract

    def __hash__(self):
        return hash((self.name, self.is_interface, self.is_abstract))

    def __eq__(self, other):
        return self.name == other.name and \
            self.is_interface == other.is_interface and \
            self.is_abstract == other.is_abstract

    @classmethod
    def from_class(cls, obj):
        is_interface = util.is_iface(obj)
        if is_interface:
            # pgi bug, interface base class has no gtype
            is_abstract = False
        else:
            is_abstract = obj.__gtype__.is_abstract()
        name = class_name(obj)
        return cls(name, is_interface, is_abstract)

    def __repr__(self):
        return "<%s name=%r>" % (type(self).__name__, self.name)


class Class(BaseDocObject, MethodsMixin, PropertiesMixin, SignalsMixin,
            ChildPropertiesMixin, StylePropertiesMixin, FieldsMixin):

    def __init__(self, namespace, name):
        self.fullname = namespace + "." + name
        self.name = name
        self.info = None

        self.is_interface = False
        self.is_abstract = False
        self.is_gobject = False
        self.signature = None
        self.image_path = None

        self.gtype_struct = ""
        self.gtype_struct_methods_inherited = []

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

    _cache = {}

    @classmethod
    def from_object(cls, repo, obj):
        # cache as we need them multiple times for the inheritance counts
        if obj in cls._cache:
            return cls._cache[obj]

        namespace = obj.__module__
        name = obj.__name__

        image_path = get_class_image_path(repo.namespace, repo.version, name)
        if not os.path.exists(image_path):
            image_path = None

        def get_sub_tree(obj):
            x = []
            for base in util.fake_bases(obj, ignore_redundant=True):
                if base is object:
                    continue
                x.append((ClassNode.from_class(base), get_sub_tree(base)))
            return x

        def get_base_tree(obj):
            return [(ClassNode.from_class(obj), get_sub_tree(obj))]

        klass = cls(namespace, name)
        klass._parse_methods(repo, obj)
        klass._parse_properties(repo, obj)
        klass._parse_child_properties(repo, obj)
        klass._parse_style_properties(repo, obj)
        klass._parse_signals(repo, obj)
        klass._parse_fields(repo, obj)

        klass.info = DocInfo.from_object(repo, "all", klass,
                                         current_type=klass.fullname)

        if util.is_iface(obj):
            klass.is_interface = True
            klass.is_abstract = True
            iface_struct = obj._get_iface_struct()
            if iface_struct:
                cs = type(iface_struct)
                klass.gtype_struct = class_name(cs)
        else:
            klass.is_interface = False
            klass.is_abstract = obj.__gtype__.is_abstract()
            class_struct = obj._get_class_struct()
            if class_struct:
                cs = type(class_struct)
                klass.gtype_struct = class_name(cs)

        klass.is_gobject = util.is_object(obj) or util.is_iface(obj)

        def iter_gtype_structs(obj):
            for base in util.fake_mro(obj):
                if base is object:
                    continue
                if util.is_iface(base):
                    struct = base._get_iface_struct()
                else:
                    struct = base._get_class_struct()
                if not struct:
                    continue
                yield Structure.from_object(repo, type(struct))

        for struct in iter_gtype_structs(obj):
            method_count = len(struct.methods)
            if not method_count:
                continue
            klass.gtype_struct_methods_inherited.append(
                (struct.fullname, method_count))

        klass.base_tree = get_base_tree(obj)

        def iter_bases(obj):
            for base in util.fake_mro(obj):
                if base is object or base is obj:
                    continue
                yield Class.from_object(repo, base)

        inherited = {}
        inherit_types = ["vfuncs", "methods", "properties", "signals",
                         "fields", "child_properties", "style_properties"]
        for base in iter_bases(obj):
            for type_ in inherit_types:
                attr = getattr(base, type_)
                if len(attr):
                    inherited.setdefault(type_, []).append(
                        (base.fullname, len(attr)))
        for type_ in inherit_types:
            setattr(klass, type_ + "_inherited", inherited.get(type_, []))

        subclasses = []
        for subc in util.fake_subclasses(obj):
            if subc.__module__ == namespace:
                subclasses.append(class_name(subc))
        subclasses.sort()
        klass.subclasses = subclasses
        klass.signature = get_signature_string(obj.__init__)
        klass.image_path = image_path

        cls._cache[obj] = klass
        return klass


class Field(BaseDocObject):

    def __init__(self, parent_fullname, name):
        self.fullname = parent_fullname + "." + name
        self.name = name
        self.info = None

        self.readable = False
        self.writable = False
        self.type_desc = None

    @property
    def flags_string(self):
        flags = []
        if self.readable:
            flags.append("r")
        if self.writable:
            flags.append("w")
        return "/".join(flags)

    @classmethod
    def from_object(cls, repo, parent_fullname, field_info):
        name = field_info.name
        field = cls(parent_fullname, name)

        field.type_desc = py_type_to_class_ref(field_info.py_type)
        field.readable = field_info.readable
        field.writable = field_info.writeable

        field.info = DocInfo.from_object(repo, "fields", field,
                                         current_type=parent_fullname)

        return field


class Function(BaseDocObject):

    def __init__(self, parent_fullname, name, is_method, is_static, is_vfunc):
        self.fullname = parent_fullname + "." + name
        self.name = name
        self.info = None

        self.is_method = is_method
        self.is_static = is_static
        self.is_vfunc = is_vfunc

        self.signature = u"()"
        self.signature_desc = u""

    @classmethod
    def from_object(cls, parent_fullname, obj, repo, owner):

        name = obj.__name__
        fullname = parent_fullname + "." + name
        is_method = owner is not None

        if is_method:
            is_static = util.is_staticmethod(obj)
            is_vfunc = util.is_virtualmethod(obj)
        else:
            is_static = False
            is_vfunc = False

        def get_docstring():
            """Get first non-empty docstring following the MRO"""

            doc = str(obj.__doc__ or u"")

            # no docstring, try to get it from base classes
            if not doc and owner:
                for base in owner.__mro__[1:]:
                    try:
                        base_obj = getattr(base, name, None)
                    except NotImplementedError:
                        # function not implemented in pgi
                        continue
                    else:
                        doc = str(base_obj.__doc__ or u"")
                    if doc:
                        break

            return doc

        docstring = get_docstring()
        first_line = docstring and docstring.splitlines()[0] or u""

        def get_instance():
            instance = cls(
                parent_fullname, name, is_method, is_static, is_vfunc)
            current_type = parent_fullname if is_method else None
            instance.info = DocInfo.from_object(
                repo, "all", instance,
                current_type=current_type, current_func=instance.fullname)
            return instance

        sig = FuncSignature.from_string(name, first_line)

        # no valid sig, but still a docstring, probably new function
        # or an override with a new docstring
        if not sig:
            instance = get_instance()
            if docstring:
                instance.info.desc = docstring
            instance.signature = get_signature_string(obj)
            return instance

        # we got a valid signature here
        assert sig

        instance = get_instance()

        # create sphinx lists for the signature we found
        instance.signature_desc = sig.to_rest_listing(repo, fullname)
        instance.signature = sig.to_simple_signature()

        return instance


class Structure(BaseDocObject, MethodsMixin, FieldsMixin):

    def __init__(self, namespace, name, signature):
        self.fullname = namespace + "." + name
        self.name = name
        self.info = None

        self.signature = signature
        self.methods = []
        self.fields = []

    _cache = {}

    @classmethod
    def from_object(cls, repo, obj):
        # cache as we need them multiple times for the inheritance counts
        if obj in cls._cache:
            return cls._cache[obj]

        signature = get_signature_string(obj.__init__)
        instance = cls(obj.__module__, obj.__name__, signature)
        instance.info = DocInfo.from_object(repo, "all", instance,
                                            current_type=instance.fullname)
        instance._parse_methods(repo, obj)
        instance._parse_fields(repo, obj)

        cls._cache[obj] = instance

        return instance


class Union(Structure):
    pass


class Flags(BaseDocObject, MethodsMixin):

    def __init__(self, namespace, name):
        self.fullname = namespace + "." + name
        self.name = name
        self.info = None

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
        instance.info = DocInfo.from_object(repo, "all", instance,
                                            current_type=instance.fullname)
        instance._parse_values(repo, obj)
        instance._parse_methods(repo, obj)
        return instance


class Constant(BaseDocObject):

    def __init__(self, parent_fullname, name, value):
        self.fullname = parent_fullname + "." + name
        self.name = name
        self.info = None

        self.value = value

    @classmethod
    def from_object(cls, repo, parent_fullname, name, obj):
        instance = Constant(parent_fullname, name, repr(obj))
        instance.info = DocInfo.from_object(repo, "all", instance)
        return instance


class SymbolMapping(object):

    def __init__(self, symbol_map, source_map):
        self.symbol_map = symbol_map  # [(c sym, url, py sym, is_shadowed)]
        self.source_map = source_map  # {py sym: git url}

    @classmethod
    def from_module(cls, repo, module):
        lib_version = get_project_version(module)
        func = get_source_to_url_func(repo.namespace, lib_version)

        source_map = repo.get_source_map()
        pysource_map = {}
        if func:
            for key, value in source_map.iteritems():
                value = func(value)
                for pyid in repo.lookup_all_py_id(key, shadowed=False):
                    pysource_map[pyid] = value

        symbol_map = []
        items = repo.get_types().iteritems()
        for key, values in sorted(items, key=lambda x: x[0].lower()):
            if func:
                source_path = source_map.get(key, u"")
                source_url = func(source_path) if source_path else u""
            else:
                source_url = u""
            for value in values:
                if not value.startswith(repo.namespace + "."):
                    continue
                if repo.is_private(value):
                    continue
                symbol_map.append((key, source_url, value, u""))
            if not values:
                is_shadowed = repo.get_shadowed(key)
                symbol_map.append((key, source_url, u"", is_shadowed))
        return cls(symbol_map, pysource_map)


class Module(BaseDocObject):

    def __init__(self, namespace):
        self.fullname = namespace
        self.name = namespace

        self.classes = []
        self.pyclasses = []
        self.constants = []
        self.functions = []
        self.callbacks = []
        self.flags = []
        self.enums = []
        self.structures = []
        self.class_structures = []
        self.iface_structures = []
        self.unions = []

        self.symbol_mapping = None
        self.hierarchy = None
        self.project_summary = None
        self.library_version = None
        self.dependencies = []

    @classmethod
    def from_repo(cls, repo):
        mod = Module(repo.namespace)
        mod.dependencies = repo.get_all_dependencies()

        pymod = repo.import_module()
        mod.library_version = get_project_version(pymod)
        hierarchy_classes = set()

        for key in dir(pymod):
            if key.startswith("_"):
                continue
            obj = getattr(pymod, key)

            if isinstance(obj, types.FunctionType):
                if obj.__module__.split(".")[-1] != repo.namespace:
                    # originated from other namespace
                    continue

                func = Function.from_object(repo.namespace, obj, repo, None)
                if util.is_callback(obj):
                    mod.callbacks.append(func)
                else:
                    mod.functions.append(func)
            elif inspect.isclass(obj):
                if obj.__name__ != key:
                    # renamed class
                    continue
                if obj.__module__.split(".")[-1] != repo.namespace:
                    # originated from other namespace
                    continue

                if util.is_object(obj) or util.is_iface(obj):
                    klass = Class.from_object(repo, obj)
                    if not klass.is_interface:
                        hierarchy_classes.add(obj)
                    mod.classes.append(klass)
                elif util.is_flags(obj):
                    flags = Flags.from_object(repo, obj)
                    mod.flags.append(flags)
                elif util.is_enum(obj):
                    enum = Flags.from_object(repo, obj)
                    mod.enums.append(enum)
                elif util.is_struct(obj):
                    struct = Structure.from_object(repo, obj)
                    # Hide private structs
                    if repo.is_private(struct.fullname):
                        continue
                    mod.structures.append(struct)
                elif util.is_union(obj):
                    union = Union.from_object(repo, obj)
                    mod.unions.append(union)
                else:
                    # don't include GError
                    if not issubclass(obj, BaseException):
                        hierarchy_classes.add(obj)

                    # classes not subclassing from any gobject base class
                    if util.is_fundamental(obj):
                        klass = Class.from_object(repo, obj)
                        mod.classes.append(klass)
                    else:
                        klass = PyClass.from_object(repo, obj)
                        mod.pyclasses.append(klass)
            else:
                const = Constant.from_object(repo, repo.namespace, key, obj)
                mod.constants.append(const)

        gtype_structs = set(
            [(c.gtype_struct, c.is_interface) for c in mod.classes
             if c.gtype_struct])

        def is_gtype_struct(obj, is_iface):
            return (obj.fullname, is_iface) in gtype_structs

        mod.class_structures = [
            c for c in mod.structures if is_gtype_struct(c, False)]
        mod.iface_structures = [
            c for c in mod.structures if is_gtype_struct(c, True)]

        mod.structures = [
            c for c in mod.structures
            if c not in mod.class_structures and c not in mod.iface_structures]

        symbol_mapping = SymbolMapping.from_module(repo, pymod)
        mod.symbol_mapping = symbol_mapping

        mod.hierarchy = to_names(get_hierarchy(hierarchy_classes))
        mod.project_summary = get_project_summary(repo.namespace)
        mod.project_summary.dependencies = repo.get_dependencies()

        return mod


class DocInfo(BaseDocObject):

    def __init__(self, fullname, name):
        self.fullname = fullname
        self.name = name

        self.desc = u""
        self.shadowed_desc = u""

        self.version_added = u""

        self.deprecated = False
        self.version_deprecated = u""
        self.deprecation_desc = u""

    @classmethod
    def from_object(cls, repo, type_, doc_object,
                    current_type=None, current_func=None):
        info = cls(doc_object.fullname, doc_object.name)
        info.desc, info.shadowed_desc = repo.lookup_docs(
            type_, info.fullname,
            current_type=current_type, current_func=current_func)
        info.version_added, info.version_deprecated, info.deprecation_desc = \
            repo.lookup_meta(type_, info.fullname)
        info.deprecated = bool(
            info.version_deprecated or info.deprecation_desc)
        return info
