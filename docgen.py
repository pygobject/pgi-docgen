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

from xml.dom.minidom import parseString
import xml.sax.saxutils as saxutils
import types
import os
import re
import inspect
import shutil
import keyword


import pgi
pgi.install_as_gi()
pgi.set_backend("ctypes,cffi,null")


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


def import_namespace(namespace, version):
    import gi
    gi.require_version(namespace, version)
    module = __import__("gi.repository", fromlist=[namespace])
    return getattr(module, namespace)


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

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        key = namespace + version
        if key in self._doms:
            self._dom = self._doms[key]
            return

        with open(self.get_path(), "rb") as h:
            self._dom = parseString(h.read())

        self._doms[key] = self._dom

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
            print "Load dependencies: %s %s" % key
            sub_ns = Namespace(*key)
            loaded[key] = sub_ns
            to_load.extend(sub_ns.get_dependencies())

        for sub_ns in loaded.values():
            self._parse_types(sub_ns)

        self._parse_types(ns)
        self._parse_docs(ns)

    def get_dependencies(self):
        return self._ns.get_dependencies()

    def _parse_types(self, ns):
        """Create a mapping of various C names to python names, taking the
        current namespace into account.
        """

        dom = ns.get_dom()
        namespace = ns.namespace

        # classes and aliases: GtkFooBar -> Gtk.FooBar
        for t in dom.getElementsByTagName("type"):
            local_name = t.getAttribute("name")
            c_name = t.getAttribute("c:type").rstrip("*")
            self._types[c_name] = local_name

        # gtk_main -> Gtk.main
        for t in dom.getElementsByTagName("function"):
            local_name = t.getAttribute("name")
            # Copy escaping from gi: Foo.break -> Foo.break_
            local_name = escape_keyword(local_name)
            namespace = t.parentNode.getAttribute("name")
            c_name = t.getAttribute("c:identifier")
            name = namespace + "." + local_name
            self._types[c_name] = name

        # gtk_dialog_get_response_for_widget ->
        #     Gtk.Dialog.get_response_for_widget
        for t in dom.getElementsByTagName("method"):
            local_name = t.getAttribute("name")
            # Copy escaping from gi: Foo.break -> Foo.break_
            local_name = escape_keyword(local_name)
            owner = t.parentNode.getAttribute("name")
            c_name = t.getAttribute("c:identifier")
            name = namespace + "." + owner + "." + local_name
            self._types[c_name] = name

        # enums etc. GTK_SOME_FLAG_FOO -> Gtk.SomeFlag.FOO
        for t in dom.getElementsByTagName("member"):
            parent = t.parentNode
            if parent.tagName == "bitfield" or parent.tagName == "enumeration":
                c_name = t.getAttribute("c:identifier")
                class_name = parent.getAttribute("name")
                field_name = t.getAttribute("name").upper()
                local_name = namespace + "." + class_name + "." + field_name
                self._types[c_name] = local_name

        # cairo_t -> cairo.Context
        for t in dom.getElementsByTagName("record"):
            c_name = t.getAttribute("c:type")
            type_name = t.getAttribute("name")
            self._types[c_name] = type_name

    def _parse_docs(self, ns):
        """Parse docs"""

        dom = ns.get_dom()

        for doc in dom.getElementsByTagName("doc"):
            docs = self._fix(doc.firstChild.nodeValue)

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

    def _fix(self, d):

        d = saxutils.unescape(d)

        def fixup_code(match):
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

        d = re.sub('#([A-Za-z0-9_]+)', fixup_class_refs, d)
        d = re.sub('%([A-Za-z0-9_]+)', fixup_class_refs, d)

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

        d = d.replace("NULL", ":obj:`None`")
        d = d.replace("%NULL", ":obj:`None`")
        d = d.replace("%TRUE", ":obj:`True`")
        d = d.replace("TRUE", ":obj:`True`")
        d = d.replace("%FALSE", ":obj:`False`")
        d = d.replace("FALSE", ":obj:`False`")

        return d

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

        docs = self._all.get(name, "")

        return """
class %s(%s):
    r'''
%s
    '''\n""" % (name.split(".")[-1], bases, docs.encode("utf-8"))

    def parse_properties(self, obj):
        if not hasattr(obj, "props"):
            return ""

        names = []
        for attr in dir(obj.props):
            if attr.startswith("_"):
                continue
            spec = getattr(obj.props, attr, None)
            if not spec:
                continue
            if spec.owner_type.pytype is obj:
                names.append((spec.name, spec.blurb))

        names = "\n".join([self._fix('    "%s", "%s"' % n) for n in names])

        if not names:
            return ""

        return '''
.. csv-table:: Properties
    :header: "Name", "Description"

%s
''' % names

    def parse_flags(self, name, obj):
        code = """
class %s(GObject.GFlags):
    r'''
%s
    '''
""" % (obj.__name__, self._all.get(name, ""))

        values = []
        for attr_name in dir(obj):
            attr = getattr(obj, attr_name)
            if not isinstance(attr, obj):
                continue
            values.append((int(attr), attr_name))

        values.sort()

        for val, n in values:
            code += "    %s = %r\n" % (n, val)
            doc_key = name + "." + n.lower()
            docs = self._all.get(doc_key, "")
            code += "    r'''%s'''\n" % docs

        return code

    def parse_function(self, name, owner, obj, method=False):
        """Returns python code for the object"""

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

        # still nothing, let sphinx handle it
        if not sig:
            return "%s = %s\n" % (func_name, name)

        arg_names = sig.arg_names
        if method:
            arg_names.insert(0, "self")
        arg_names = ", ".join(arg_names)

        docs = []
        for key, value in sig.args:
            param_key = name + "." + key
            text = self._parameters.get(param_key, "")
            docs.append(":param %s: %s" % (key, text))
            docs.append(":type %s: :class:`%s`" % (key, value))

        if sig.raises:
            docs.append(":raises: :class:`GObject.GError`")

        if name in self._returns:
            # don't allow newlines here
            text = self._returns[name]
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
            docs.append(self._all[name])

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
            final = """
def %s(%s):
    r'''
%s
    '''
""" % (func_name, arg_names, docs.encode("utf-8"))

        return final


class MainGenerator(object):

    DEST = "_docs"

    def __init__(self):
        if os.path.exists(self.DEST):
            shutil.rmtree(self.DEST)

        os.mkdir(self.DEST)
        self._subs = []

    def new_generator(self, namespace, name):
        gen = ModuleGenerator(self.DEST, namespace, name)
        self._subs.append(gen.get_index_name())
        return gen

    def finalize(self):
        with open(os.path.join(self.DEST, "index.rst"), "wb") as h:
            h.write("""\
Python GObject Introspection Documentation
==========================================

.. toctree::
    :maxdepth: 1

""")

            for sub in self._subs:
                h.write("    %s\n" % sub)

        del self._subs

        dest_conf = os.path.join(self.DEST, "conf.py")
        shutil.copy("conf.py", dest_conf)
        theme_dest = os.path.join(self.DEST, "minimalism")
        shutil.copytree("minimalism", theme_dest)


class FlagsGenerator(object):

    def __init__(self, dir_, module_fileobj):
        flags_path = os.path.join(dir_, "flags.rst")
        self.handle = open(flags_path, "wb")
        self.handle.write("""\
Flags
=====

""")

        self._flags = {}

        self._module = module_fileobj

    def add_flags(self, obj, code):
        assert isinstance(code, str)
        self._flags[obj] = code

    def get_name(self):
        return os.path.basename(self.handle.name)

    def finalize(self):
        classes = self._flags.keys()
        classes.sort(key=lambda x: x.__name__)

        for cls in classes:
            title = make_rest_title(cls.__name__, "-")
            self.handle.write("""
%s

.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:

""" % (title, cls.__module__ + "." + cls.__name__))

        for cls in classes:
            code = self._flags[cls]
            self._module.write(code + "\n")

        self.handle.close()


class ClassGenerator(object):

    def __init__(self, dir_, module_fileobj):
        self._sub_dir = sub_dir = os.path.join(dir_, "classes")
        os.mkdir(sub_dir)
        index_path = os.path.join(sub_dir, "index.rst")

        self._classes = {}  # cls -> code
        self._methods = {}  # cls -> code
        self._props = {}  # cls -> code

        self.index_handle = open(index_path, "wb")
        self.index_handle.write("""
Classes
=======

""")

        self._module = module_fileobj

    def add_class(self, obj, code):
        assert isinstance(code, str)
        self._classes[obj] = code

    def add_method(self, cls_obj, code):
        assert isinstance(code, str)
        if cls_obj in self._methods:
            self._methods[cls_obj].append(code)
        else:
            self._methods[cls_obj] = [code]

    def add_properties(self, cls, code):
        assert isinstance(code, str)
        self._props[cls] = code

    def get_name(self):
        return os.path.join("classes", "index.rst")

    def finalize(self):
        classes = self._classes.keys()

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

        # add classes to the index toctree
        self.index_handle.write(".. toctree::\n    :maxdepth: 1\n\n")
        for cls in sorted(classes, key=lambda x: x.__name__):
            self.index_handle.write("""\
    %s
""" % cls.__name__)

        # write the code
        for cls in classes:
            self._module.write(self._classes[cls])
            for method in self._methods.get(cls, []):
                self._module.write(indent(method) + "\n")

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

        self.index_handle.close()


class ModuleGenerator(object):

    def __init__(self, dir_, namespace, version):
        # create the basic package structure
        self.namespace = namespace
        self.version = version
        nick = "%s_%s" % (namespace, version)
        self.index_name = os.path.join(nick, "index")
        self.prefix = os.path.join(dir_, nick)
        os.mkdir(self.prefix)
        module_path = os.path.join(self.prefix, namespace + ".py")
        self.module = open(module_path, "wb")

        func_name = "functions.rst"
        func_path = os.path.join(self.prefix, func_name)
        self.func_handle = open(func_path, "wb")
        self.func_handle.write("""
Functions
=========
""")

        self._class_gen = ClassGenerator(self.prefix, self.module)
        self._flags_gen = FlagsGenerator(self.prefix, self.module)

        # utf-8 encoded .py
        self.module.write("# -*- coding: utf-8 -*-\n")

        self.add_dependency(namespace, version)

        # for flags
        self.add_dependency("GObject", "2.0")

    def get_index_name(self):
        return self.index_name

    def add_dependency(self, name, version):
        """Import the module in the generated code"""
        self.module.write("import pgi\n")
        self.module.write("pgi.set_backend('ctypes,null')\n")
        self.module.write("pgi.require_version('%s', '%s')\n" % (name, version))
        self.module.write("from pgi.repository import %s\n" % name)

    def add_function(self, name, code):
        """Add a toplevel function"""

        if not isinstance(code, str):
            code = code.encode("utf-8")

        self.module.write(code)
        h = self.func_handle
        h.write(".. autofunction:: %s\n\n" % name)

    def add_class(self, cls_obj, code):
        """Add a class"""

        if not isinstance(code, str):
            code = code.encode("utf-8")

        self._class_gen.add_class(cls_obj, code)

    def add_method(self, cls_obj, code):
        """Add a method"""

        if not isinstance(code, str):
            code = code.encode("utf-8")

        self._class_gen.add_method(cls_obj, code)

    def add_struct(self, name, code):
        self.add_class(name, code)

    def add_flags(self, obj, code):
        if not isinstance(code, str):
            code = code.encode("utf-8")
        self._flags_gen.add_flags(obj, code)

    def add_properties(self, cls_obj, code):
        if not isinstance(code, str):
            code = code.encode("utf-8")

        self._class_gen.add_properties(cls_obj, code)

    def finalize(self):
        func_name = os.path.basename(self.func_handle.name)
        class_name = self._class_gen.get_name()
        flags_name = self._flags_gen.get_name()

        with open(os.path.join(self.prefix, "index.rst"),  "wb") as h:
            title = "%s %s" % (self.namespace, self.version)
            h.write(title + "\n")
            h.write(len(title) * "=" + "\n")

            h.write("""

.. toctree::
    :maxdepth: 1

    %(functions)s
    %(classes)s
    %(flags)s

""" % {"functions": func_name, "classes": class_name, "flags": flags_name})

        self._class_gen.finalize()
        self._flags_gen.finalize()

        self.func_handle.close()
        self.module.close()

        # make sure the generated code is valid python
        with open(self.module.name, "rb") as h:
            exec h.read() in {}


def create_docs(main_gen, namespace, version):
    try:
        mod = import_namespace(namespace, version)
    except ImportError:
        print "Couldn't import %r, skipping" % namespace
        return

    gen = main_gen.new_generator(namespace, version)
    repo = Repository(namespace, version)

    # import the needed modules
    for dep in repo.get_dependencies():
        gen.add_dependency(*dep)

    from gi.repository import GObject
    class_base = GObject.Object
    iface_base = GObject.GInterface
    flags_base = GObject.GFlags

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
                gen.add_function(name, code)
        elif inspect.isclass(obj):
            if issubclass(obj, (iface_base, class_base)):

                code = repo.parse_class(name, obj, add_bases=True)
                gen.add_class(obj, code)

                code = repo.parse_properties(obj)
                gen.add_properties(obj, code)

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
                    if isinstance(attr_obj, types.MethodType):
                        code = repo.parse_function(func_key, obj, attr_obj, True)
                        if code:
                            gen.add_method(obj, code)
            elif issubclass(obj, flags_base):
                code = repo.parse_flags(name, obj)
                gen.add_flags(obj, code)
            else:
                # structs, enums, etc.
                code = repo.parse_class(key, obj)
                if code:
                    gen.add_class(obj, code)

    gen.finalize()


if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print "%s <namespace-version>..." % sys.argv[0]
        print "%s -a" % sys.argv[0]
        raise SystemExit(1)

    gen = MainGenerator()

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

    for arg in modules:
        namespace, version = arg.split("-")
        print "Create docs: Namespace=%s, Version=%s" % (namespace, version)
        if namespace == "cairo":
            print "cairo gets referenced to external docs, skipping"
            continue
        create_docs(gen, namespace, version)

    gen.finalize()

    print "done"
