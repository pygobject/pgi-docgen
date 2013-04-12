#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# this is all ugly.. but a start

import sys
sys.path.insert(0, "../")

from xml.dom import minidom
import xml.sax.saxutils as saxutils
import types
import os
import re
import inspect
import shutil
import keyword
import csv
import cStringIO


import pgi
pgi.install_as_gi()
pgi.set_backend("ctypes,null")


def get_gir_dirs():
    if "XDG_DATA_DIRS" in os.environ:
        dirs = os.environ["XDG_DATA_DIRS"].split(os.pathsep)
    else:
        dirs = ["/usr/local/share/", "/usr/share/"]

    return [os.path.join(d, "gir-1.0") for d in dirs]


def escape_keyword(text, reg=re.compile("^(%s)$" % "|".join(keyword.kwlist))):
    return reg.sub(r"\1_", text)


def make_rest_title(text, char="="):
    return text + "\n" + len(text) * char


def gtype_to_rest(gtype):
    p = gtype.pytype
    if p is None:
        return ""
    name = p.__name__
    if p.__module__ != "__builtin__":
        name = p.__module__ + "." + name
    return ":class:`%s`" % name


def import_namespace(namespace, version):
    import gi
    gi.require_version(namespace, version)
    module = __import__("gi.repository", fromlist=[namespace])
    return getattr(module, namespace)


class CSVDialect(csv.Dialect):
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_ALL


def get_csv_line(values):
    values = [v.replace("\n", " ") for v in values]
    h = cStringIO.StringIO()
    w = csv.writer(h, CSVDialect)
    w.writerow(values)
    return h.getvalue().rstrip()


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


def method_is_static(obj):
    try:
        return obj.im_self is not None
    except AttributeError:
        return True


class FuncSignature(object):

    def __init__(self, res, args, raises, name):
        self.res = res
        self.args = args
        self.name = name
        self.raises = raises

    @property
    def arg_names(self):
        return [p[0] for p in self.args]

    def get_arg_type(self, name):
        for a, t in self.args:
            if a == name:
                return t

    @classmethod
    def from_string(cls, line):
        match = re.match("(.*?)\((.*?)\)\s*(raises|)\s*(-> )?(.*)", line)
        if not match:
            return

        groups = match.groups()
        name, args, raises, dummy, ret = groups

        args = args and args.split(",") or []

        arg_map = []
        for arg in args:
            parts = arg.split(":", 1)
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


class Namespace(object):

    _doms = {}
    _types = {}

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        key = namespace + version

        if key not in self._doms:
            self._doms[key] = self._parse_dom()
        self._dom = self._doms[key]

        if not key in self._types:
            self._types[key] = self._parse_types()
        self.types = self._types[key]

    def _parse_dom(self):
        print "Parsing GIR: %s-%s" % (self.namespace, self.version)
        return minidom.parse(self.get_path())

    def _parse_types(self):
        """Create a mapping of various C names to python names"""

        dom = self.get_dom()
        namespace = self.namespace
        types = {}

        # classes and aliases: GtkFooBar -> Gtk.FooBar
        for t in dom.getElementsByTagName("type"):
            local_name = t.getAttribute("name")
            c_name = t.getAttribute("c:type").rstrip("*")
            types[c_name] = local_name

        # gtk_main -> Gtk.main
        for t in dom.getElementsByTagName("function"):
            local_name = t.getAttribute("name")
            # Copy escaping from gi: Foo.break -> Foo.break_
            local_name = escape_keyword(local_name)
            namespace = t.parentNode.getAttribute("name")
            c_name = t.getAttribute("c:identifier")
            name = namespace + "." + local_name
            types[c_name] = name

        # gtk_dialog_get_response_for_widget ->
        #     Gtk.Dialog.get_response_for_widget
        elements = dom.getElementsByTagName("constructor")
        elements += dom.getElementsByTagName("method")
        for t in elements:
            local_name = t.getAttribute("name")
            # Copy escaping from gi: Foo.break -> Foo.break_
            local_name = escape_keyword(local_name)
            owner = t.parentNode.getAttribute("name")
            c_name = t.getAttribute("c:identifier")
            name = namespace + "." + owner + "." + local_name
            types[c_name] = name

        # enums etc. GTK_SOME_FLAG_FOO -> Gtk.SomeFlag.FOO
        for t in dom.getElementsByTagName("member"):
            parent = t.parentNode
            if parent.tagName == "bitfield" or parent.tagName == "enumeration":
                c_name = t.getAttribute("c:identifier")
                class_name = parent.getAttribute("name")
                field_name = t.getAttribute("name").upper()
                local_name = namespace + "." + class_name + "." + field_name
                types[c_name] = local_name

        # cairo_t -> cairo.Context
        for t in dom.getElementsByTagName("record"):
            c_name = t.getAttribute("c:type")
            type_name = t.getAttribute("name")
            types[c_name] = type_name

        # G_TIME_SPAN_MINUTE -> GLib.TIME_SPAN_MINUTE
        for t in dom.getElementsByTagName("constant"):
            c_name = t.getAttribute("c:type")
            if t.parentNode.tagName == "namespace":
                name = namespace + "." + t.getAttribute("name")
                types[c_name] = name

        return types

    def get_path(self):
        return "/usr/share/gir-1.0/%s-%s.gir" % (self.namespace, self.version)

    def get_dom(self):
        return self._dom

    def get_dependencies(self):
        dom = self.get_dom()
        deps = []
        for include in dom.getElementsByTagName("include"):
            name = include.getAttribute("name")
            version = include.getAttribute("version")
            deps.append((name, version))
        return deps


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
            mro_bases = merge_in_overrides(obj)

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
    '''\n""" % (name.split(".")[-1], bases, docs.encode("utf-8"))

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
        is_static = method_is_static(obj)

        def get_sig(obj):
            doc = str(obj.__doc__)
            first_line = doc and doc.splitlines()[0] or ""
            return FuncSignature.from_string(first_line)

        func_name = name.split(".")[-1]

        sig = get_sig(obj)

        # no valid sig, but still a docstring, probably new function
        # or an override with a new docstring
        if not sig and obj.__doc__:
            return "%s = %s\n" % (func_name, name)

        # if true, let sphinx figure out the call spec, it might have changed
        ignore_spec = False

        # no docstring, try to get the signature from base classes
        if not sig and owner:
            for base in owner.__mro__[1:]:
                base_obj = getattr(base, func_name, None)
                sig = get_sig(base_obj)
                if sig:
                    ignore_spec = True
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

        arg_names = sig.arg_names
        if is_method and not is_static:
            arg_names.insert(0, "self")
        arg_names = ", ".join(arg_names)

        docs = []
        for key, value in sig.args:
            param_key = name + "." + key
            text = self._get_parameter_docs(param_key)
            docs.append(":param %s: %s" % (key, text))
            docs.append(":type %s: :class:`%s`" % (key, value))

        if sig.raises:
            docs.append(":raises: :class:`GObject.GError`")

        if name in self._returns:
            # don't allow newlines here
            text = self._get_return_docs(name)
            doc_string = " ".join(text.splitlines())
            docs.append(":returns: %s" % doc_string)

        res = []
        for r in sig.res:
            if len(r) > 1:
                res.append("%s: :class:`%s`" % tuple(r))
            else:
                res.append(":class:`%s`" % r[0])

        if res:
            docs.append(":rtype: %s" % ", ".join(res))

        docs.append("")

        if name in self._all:
            docs.append(self._get_docs(name))

        docs = "\n".join(docs)

        # in case the function is overriden, let sphinx get the funcspec
        # but still keep around the old docstring (sphinx seems to understand
        # the string under attribute thing.. good, since we can't change
        # a docstring in py2)
        if ignore_spec:
            final = """
%s = %s
r'''
%s
'''
""" % (func_name, name, docs.encode("utf-8"))

        else:
            final = ""
            if is_method and is_static:
                final += "@staticmethod\n"
            final += """\
def %s(%s):
    r'''
%s
    '''
""" % (func_name, arg_names, docs.encode("utf-8"))

        return final


class Generator(object):
    """Abstract base class"""

    def is_empty(self):
        """If there is any content to create"""
        raise NotImplementedError

    def write(self):
        """Create and write everything"""
        raise NotImplementedError

    def get_name(self):
        """A name that can be references in an rst file (toctree e.g.)"""
        raise NotImplementedError


class MainGenerator(Generator):
    """Creates the sphinx environment and the index page"""

    API_DIR = "api"
    TUTORIAL_DIR = "tutorial"
    THEME_DIR = "theme"
    CONF_NAME = "conf.py"

    def __init__(self, dest):
        self._dest = dest
        self._modules = []

    def add_module(self, namespace, version):
        """Add a module: add_module('Gtk', '3.0')"""
        self._modules.append((namespace, version))

    def write(self):
        os.mkdir(self._dest)

        # sort by namespace
        modules = sorted(self._modules, key=lambda x: x[0].lower())

        path = os.path.join(self._dest, self.API_DIR)
        os.mkdir(path)

        module_names = []
        for namespace, version in modules:
            gen = ModuleGenerator(path, namespace, version)
            gen.write()
            module_names.append(gen.get_name())

        api_path = os.path.join(self._dest, self.API_DIR)
        with open(os.path.join(api_path, "index.rst"), "wb") as h:
            h.write("""
API Reference
=============

.. toctree::
    :maxdepth: 1

""")

            for sub in module_names:
                h.write("    %s\n" % sub)

        with open(os.path.join(self._dest, "index.rst"), "wb") as h:
            h.write("""
Python GObject Introspection Documentation
==========================================

.. toctree::
    :maxdepth: 2

    %s/index
    %s/index
""" % (self.TUTORIAL_DIR, self.API_DIR))

        # copy the theme, conf.py and all the static reST files
        dest_conf = os.path.join(self._dest, self.CONF_NAME)
        shutil.copy(self.CONF_NAME, dest_conf)
        theme_dest = os.path.join(self._dest, self.THEME_DIR)
        shutil.copytree(self.THEME_DIR, theme_dest)
        tutorial_dest = os.path.join(self._dest, self.TUTORIAL_DIR)
        shutil.copytree(self.TUTORIAL_DIR, tutorial_dest)


class FunctionGenerator(Generator):

    def __init__(self, dir_, module_fileobj):
        self.path = os.path.join(dir_, "functions.rst")

        self._funcs = {}
        self._module = module_fileobj

    def get_name(self):
        return os.path.basename(self.path)

    def is_empty(self):
        return not bool(self._funcs)

    def add_function(self, name, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._funcs[name] = code

    def write(self):

        handle = open(self.path, "wb")
        handle.write("""
Functions
=========
""")

        for name, code in sorted(self._funcs.items()):
            self._module.write(code)
            handle.write(".. autofunction:: %s\n\n" % name)

        handle.close()


class EnumGenerator(Generator):

    def __init__(self, dir_, module_fileobj):
        self.path = os.path.join(dir_, "enums.rst")

        self._enums = {}
        self._module = module_fileobj

    def add_enum(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._enums[obj] = code

    def get_name(self):
        return os.path.basename(self.path)

    def is_empty(self):
        return not bool(self._enums)

    def write(self):
        classes = self._enums.keys()
        classes.sort(key=lambda x: x.__name__)

        handle = open(self.path, "wb")
        handle.write("""\
Enums
=====

""")

        for cls in classes:
            title = make_rest_title(cls.__name__, "-")
            handle.write("""
%s

.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
    :private-members:

""" % (title, cls.__module__ + "." + cls.__name__))

        for cls in classes:
            code = self._enums[cls]
            self._module.write(code + "\n")

        handle.close()


class ConstantsGenerator(Generator):

    def __init__(self, dir_, module_fileobj):
        self.path = os.path.join(dir_, "constants.rst")

        self._consts = {}
        self._module = module_fileobj

    def add_constant(self, name, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._consts[name] = code

    def get_name(self):
        return os.path.basename(self.path)

    def is_empty(self):
        return not bool(self._consts)

    def write(self):
        names = self._consts.keys()
        names.sort()

        handle = open(self.path, "wb")
        handle.write("""\
Constants
=========

""")

        for name in names:
            handle.write("""
.. autodata:: %s

""" % name)

        for name in names:
            code = self._consts[name]
            self._module.write(code + "\n")

        handle.close()


class FlagsGenerator(Generator):

    def __init__(self, dir_, module_fileobj):
        self.path = os.path.join(dir_, "flags.rst")

        self._flags = {}
        self._module = module_fileobj

    def add_flags(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._flags[obj] = code

    def get_name(self):
        return os.path.basename(self.path)

    def is_empty(self):
        return not bool(self._flags)

    def write(self):
        classes = self._flags.keys()
        classes.sort(key=lambda x: x.__name__)

        handle = open(self.path, "wb")
        handle.write("""\
Flags
=====

""")


        for cls in classes:
            title = make_rest_title(cls.__name__, "-")
            handle.write("""
%s

.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
    :private-members:

""" % (title, cls.__module__ + "." + cls.__name__))

        for cls in classes:
            code = self._flags[cls]
            self._module.write(code + "\n")

        handle.close()


class ClassGenerator(Generator):
    """Base class for GObjects an GInterfaces"""

    DIR_NAME = ""
    HEADLINE = ""

    def __init__(self, dir_, module_fileobj):
        self._sub_dir = os.path.join(dir_, self.DIR_NAME)
        self.path = os.path.join(self._sub_dir, "index.rst")

        self._classes = {}  # cls -> code
        self._methods = {}  # cls -> code
        self._props = {}  # cls -> code
        self._sigs = {} # cls -> code

        self._module = module_fileobj

    def add_class(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._classes[obj] = code

    def add_method(self, cls_obj, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        if cls_obj in self._methods:
            self._methods[cls_obj].append((obj, code))
        else:
            self._methods[cls_obj] = [(obj, code)]

    def add_properties(self, cls, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._props[cls] = code

    def add_signals(self, cls, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._sigs[cls] = code

    def get_name(self):
        return os.path.join(self.DIR_NAME, "index.rst")

    def is_empty(self):
        return not bool(self._classes)

    def write(self):
        classes = self._classes.keys()

        # try to get the right order, so all bases are defined
        # this probably isn't right...
        def check_order(cls):
            for c in cls:
                for b in merge_in_overrides(c):
                    if b in cls and cls.index(b) > cls.index(c):
                        return False
            return True

        def get_key(cls, c):
            i = 0
            for b in merge_in_overrides(c):
                if b not in cls:
                    continue
                if cls.index(b) > cls.index(c):
                    i += 1
            return i

        ranks = {}
        while not check_order(classes):
            for cls in classes:
                ranks[cls] = ranks.get(cls, 0) + get_key(classes, cls)
            classes.sort(key=lambda x: ranks[x])

        def indent(c):
            return "\n".join(["    %s" % l for l in c.splitlines()])

        os.mkdir(self._sub_dir)

        index_handle = open(self.path, "wb")
        index_handle.write(make_rest_title(self.HEADLINE) + "\n\n")

        # add classes to the index toctree
        index_handle.write(".. toctree::\n    :maxdepth: 1\n\n")
        for cls in sorted(classes, key=lambda x: x.__name__):
            index_handle.write("""\
    %s
""" % cls.__name__)

        # write the code
        for cls in classes:
            self._module.write(self._classes[cls])
            methods = self._methods.get(cls, [])
            # sort static methods first, then by name
            methods.sort(key=lambda e: (not method_is_static(e[0]), e[0].__name__))
            for obj, code in methods:
                self._module.write(indent(code) + "\n")

        # create a new file for each class
        for cls in classes:
            h = open(os.path.join(self._sub_dir, cls.__name__)  + ".rst", "wb")
            name = cls.__module__ + "." + cls.__name__
            title = name
            h.write(make_rest_title(title, "=") + "\n")

            h.write("""
Inheritance Diagram
-------------------

.. inheritance-diagram:: %s
""" % name)

            h.write("""
Properties
----------
""")
            h.write(self._props.get(cls, ""))

            h.write("""
Signals
-------
""")
            h.write(self._sigs.get(cls, ""))

            h.write("""
Class
-----
""")

            h.write("""
.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
""" % name)


            h.close()

        index_handle.close()


class GObjectGenerator(ClassGenerator):
    DIR_NAME = "classes"
    HEADLINE = "Classes"


class InterfaceGenerator(ClassGenerator):
    DIR_NAME = "interfaces"
    HEADLINE = "Interfaces"


class StructGenerator(Generator):
    def __init__(self, dir_, module_fileobj):
        self._sub_dir = os.path.join(dir_, "structs")
        self.path = os.path.join(self._sub_dir, "index.rst")

        self._structs = {}
        self._module = module_fileobj

    def get_name(self):
        return os.path.join("structs", "index.rst")

    def is_empty(self):
        return not bool(self._structs)

    def add_struct(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")
        self._structs[obj] = code

    def write(self):
        os.mkdir(self._sub_dir)

        structs = self._structs.keys()

        # write the code
        for cls in structs:
            self._module.write(self._structs[cls])

        index_handle = open(self.path, "wb")
        index_handle.write(make_rest_title("Structures") + "\n\n")

        # add classes to the index toctree
        index_handle.write(".. toctree::\n    :maxdepth: 1\n\n")
        for cls in sorted(structs, key=lambda x: x.__name__):
            index_handle.write("""\
    %s
""" % cls.__name__)

        for cls in structs:
            h = open(os.path.join(self._sub_dir, cls.__name__)  + ".rst", "wb")
            name = cls.__module__ + "." + cls.__name__
            title = name
            h.write(make_rest_title(title, "=") + "\n")

            h.write("""
.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
""" % name)

            h.close()

        index_handle.close()


class ModuleGenerator(Generator):

    def __init__(self, dir_, namespace, version):
        # create the basic package structure
        self.namespace = namespace
        self.version = version

        nick = "%s_%s" % (namespace, version)
        self._index_name = os.path.join(nick, "index")
        self._module_path = os.path.join(dir_, nick)

    def get_name(self):
        return self._index_name

    def _add_dependency(self, module, name, version):
        """Import the module in the generated code"""
        module.write("import pgi\n")
        module.write("pgi.set_backend('ctypes,null')\n")
        module.write("pgi.require_version('%s', '%s')\n" % (name, version))
        module.write("from pgi.repository import %s\n" % name)

    def write(self):

        namespace, version = self.namespace, self.version

        os.mkdir(self._module_path)
        module_path = os.path.join(self._module_path, namespace + ".py")
        module = open(module_path, "wb")

        # utf-8 encoded .py
        module.write("# -*- coding: utf-8 -*-\n")
        # for references to the real module
        self._add_dependency(module, namespace, version)
        # for flags
        self._add_dependency(module, "GObject", "2.0")

        try:
            mod = import_namespace(namespace, version)
        except ImportError:
            print "Couldn't import %r, skipping" % namespace
            return

        repo = Repository(namespace, version)

        for dep in repo.get_dependencies():
            self._add_dependency(module, *dep)

        from gi.repository import GObject, Gtk
        class_base = GObject.Object
        iface_base = GObject.GInterface
        flags_base = GObject.GFlags
        enum_base = GObject.GEnum
        struct_base = Gtk.AccelKey.__mro__[-2]  # FIXME

        obj_gen = GObjectGenerator(self._module_path, module)
        iface_gen = InterfaceGenerator(self._module_path, module)
        flags_gen = FlagsGenerator(self._module_path, module)
        enums_gen = EnumGenerator(self._module_path, module)
        func_gen = FunctionGenerator(self._module_path, module)
        struct_gen = StructGenerator(self._module_path, module)
        const_gen = ConstantsGenerator(self._module_path, module)

        def is_method_owner(cls, method_name):
            for base in merge_in_overrides(cls):
                if hasattr(base, method_name):
                    return False
            return True

        for key in dir(mod):
            if key.startswith("_"):
                continue
            obj = getattr(mod, key)

            name = "%s.%s" % (namespace, key)

            if isinstance(obj, types.FunctionType):
                code = repo.parse_function(name, None, obj)
                if code:
                    func_gen.add_function(name, code)
            elif inspect.isclass(obj):
                if issubclass(obj, (iface_base, class_base)):

                    if issubclass(obj, class_base):
                        class_gen = obj_gen
                    else:
                        class_gen = iface_gen

                    code = repo.parse_class(name, obj, add_bases=True)
                    class_gen.add_class(obj, code)

                    code = repo.parse_properties(obj)
                    class_gen.add_properties(obj, code)

                    code = repo.parse_signals(obj)
                    class_gen.add_signals(obj, code)

                    for attr in dir(obj):
                        if attr.startswith("_"):
                            continue

                        if not is_method_owner(obj, attr):
                            continue

                        func_key = name + "." + attr
                        try:
                            attr_obj = getattr(obj, attr)
                        except NotImplementedError:
                            # FIXME.. pgi exposes methods it can't compile
                            continue
                        if callable(attr_obj):
                            code = repo.parse_function(func_key, obj, attr_obj)
                            if code:
                                class_gen.add_method(obj, attr_obj, code)
                elif issubclass(obj, flags_base):
                    code = repo.parse_flags(name, obj)
                    flags_gen.add_flags(obj, code)
                elif issubclass(obj, enum_base):
                    code = repo.parse_flags(name, obj)
                    enums_gen.add_enum(obj, code)
                elif issubclass(obj, struct_base):
                    # Hide FooPrivate if Foo exists
                    if key.endswith("Private") and hasattr(mod, key[:-7]):
                        continue
                    code = repo.parse_class(name, obj, add_bases=True)
                    struct_gen.add_struct(obj, code)
                else:
                    # unions..
                    code = repo.parse_class(name, obj)
                    if code:
                        obj_gen.add_class(obj, code)
            else:
                code = repo.parse_constant(name)
                if code:
                    const_gen.add_constant(name, code)

        handle = open(os.path.join(self._module_path, "index.rst"),  "wb")

        title = "%s %s" % (namespace, version)
        handle.write(title + "\n")
        handle.write(len(title) * "=" + "\n")

        handle.write("""
.. toctree::
    :maxdepth: 1

""")

        gens = [func_gen, iface_gen, obj_gen, struct_gen,
                flags_gen, enums_gen, const_gen]
        for gen in gens:
            if gen.is_empty():
                continue
            handle.write("    %s\n" % gen.get_name())
            gen.write()

        module.close()

        # make sure the generated code is valid python
        with open(module.name, "rb") as h:
            exec h.read() in {}


if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print "%s <namespace-version>..." % sys.argv[0]
        print "%s -a" % sys.argv[0]
        raise SystemExit(1)

    modules = []
    if "-a" in sys.argv[1:]:
        for d in get_gir_dirs():
            if not os.path.exists(d):
                continue
            for entry in os.listdir(d):
                root, ext = os.path.splitext(entry)
                if ext == ".gir":
                    modules.append(root)
    else:
        modules.extend(sys.argv[1:])

    dest_dir = "_docs"

    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    gen = MainGenerator(dest_dir)

    for arg in modules:
        namespace, version = arg.split("-")
        print "Create docs: Namespace=%s, Version=%s" % (namespace, version)
        if namespace == "cairo":
            print "cairo gets referenced to external docs, skipping"
            continue
        gen.add_module(namespace, version)

    gen.write()

    print "done"
