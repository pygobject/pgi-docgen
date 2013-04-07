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
import subprocess
import shutil
import keyword


import pgi
pgi.install_as_gi()


def escape_keyword(text, reg=re.compile("^(%s)$" % "|".join(keyword.kwlist))):
    return reg.sub(r"\1_", text)


def import_namespace(namespace, version):
    import gi
    gi.require_version(namespace, version)
    module = __import__("gi.repository", fromlist=[namespace])
    return getattr(module, namespace)


class Namespace(object):
    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        with open(self.get_path(), "rb") as h:
            self._dom = parseString(h.read())

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
        self._functions = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        self._returns = {}

        # Gtk.FooBar -> "some doc"
        self._classes = {}

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
        namespace = ns.namespace

        for doc in dom.getElementsByTagName("doc"):
            parent = doc.parentNode
            docs = self._fix(doc.firstChild.nodeValue)
            parent_name = parent.tagName

            if parent_name == "parameter":
                up = parent.parentNode.parentNode
                if up.tagName == "function":
                    if up.parentNode.tagName == "namespace":
                        namespace = up.parentNode.getAttribute("name")
                        func_name = up.getAttribute("name")
                        param_name = parent.getAttribute("name")
                        name = namespace + "." + func_name + "." + param_name
                        self._parameters[name] = docs
                    else:
                        namespace = up.parentNode.parentNode
                        assert namespace.tagName == "namespace"
                        class_ = up.parentNode
                        ns = namespace.getAttribute("name")
                        cls = class_.getAttribute("name")
                        func = up.getAttribute("name")
                        param_name = parent.getAttribute("name")
                        name = ns + "." + cls + "." + func + "." + param_name
                        self._parameters[name] = docs
                elif up.tagName == "method":
                    namespace = up.parentNode.parentNode
                    assert namespace.tagName == "namespace"
                    namespace = namespace.getAttribute("name")
                    owner = up.parentNode.getAttribute("name")
                    method = up.getAttribute("name")
                    param = parent.getAttribute("name")
                    name = namespace + "." + owner + "." + method + "." + param
                    self._parameters[name] = docs
            elif parent_name == "method":
                up = parent.parentNode
                m_owner = up.getAttribute("name")
                namespace = up.parentNode.getAttribute("name")
                method = parent.getAttribute("name")
                name = namespace + "." + m_owner + "." + method
                self._functions[name] = docs
            elif parent_name == "function":
                up = parent.parentNode
                if up.tagName == "namespace":
                    namespace = up.getAttribute("name")
                    func_name = parent.getAttribute("name")
                    name = namespace + "." + func_name
                    self._functions[name] = docs
                elif up.tagName == "class":
                    assert up.parentNode.tagName == "namespace"
                    namespace = up.parentNode.getAttribute("name")
                    class_name = up.getAttribute("name")
                    func_name = parent.getAttribute("name")
                    name = namespace + "." + class_name + "." + func_name
                    self._functions[name] = docs
            elif parent_name == "return-value":
                up = parent.parentNode
                if up.tagName == "function" and \
                        up.parentNode.tagName == "namespace":
                    namespace = up.parentNode.getAttribute("name")
                    func_name = up.getAttribute("name")
                    name = namespace + "." + func_name
                    self._returns[name] = docs
            elif parent_name == "class":
                local_name = parent.getAttribute("name")
                self._classes[local_name] = docs

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
            # hide overrides by merging the bases in
            possible_bases = []
            for base in obj.__bases__:
                base_name = base.__name__
                if base_name == name:
                    for upper_base in base.__bases__:
                        possible_bases.append(upper_base)
                else:
                    possible_bases.append(base)

            # preserve the mro
            mro_bases = []
            for base in obj.__mro__:
                if base in possible_bases:
                    mro_bases.append(base)

            # prefix with the module if it's an external class
            for base in mro_bases:
                base_name = base.__name__
                if base.__module__ == self.namespace:
                    names.append(base_name)
                elif base_name == "object":
                    names.append(base_name)
                else:
                    base_name = base.__module__ + "." + base_name

        if not names:
            names = ["object"]

        bases = ", ".join(names)

        docs = self._classes.get(name, "")

        return """
class %s(%s):
    r'''
%s
    '''\n""" % (name, bases, docs.encode("utf-8"))

    def parse_function(self, name, obj, method=False):
        """Returns python code for the object"""

        doc = str(obj.__doc__)
        first_line = doc and doc.splitlines()[0] or ""
        match = re.match("(.*?)\((.*?)\)( -> )?(.*)", first_line)
        if not match:
            return

        groups = match.groups()
        func_name, args, dummy, ret = groups

        args = args and args.split(",") or []
        args = [a.strip() for a in args]

        ret = ret and ret.split(",") or []

        arg_map = [(a.split(":")[0].strip(), a.split(":")[-1].strip()) for a in args]

        arg_names = [a[0] for a in arg_map]
        if method:
            arg_names.insert(0, "self")
        arg_names = ", ".join(arg_names)

        docs = []
        for key, value in arg_map:
            param_key = name + "." + key
            text = self._fix(self._parameters.get(param_key, ""))
            docs.append(":param %s: %s" % (key, text))
            docs.append(":type %s: :class:`%s`" % (key, value))

        if name in self._returns:
            # don't allow newlines here
            text = self._fix(self._returns[name])
            doc_string = " ".join(text.splitlines())
            docs.append(":returns:")
            docs.append("    %s" % doc_string)
            if ret:
                docs.append("    , %s" % ", ".join(ret))
        elif ret:
            docs.append(":returns:")
            docs.append("    %s" % ", ".join(ret))
        docs.append("")

        if name in self._functions:
            docs.append(self._functions[name])

        docs = "\n".join(docs)

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

    def get_generator(self, namespace, name):
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


class ClassGenerator(object):

    def __init__(self, dir_, module_fileobj):
        class_name = "classes.rst"
        class_path = os.path.join(dir_, class_name)
        self._classes = {}  # cls -> code
        self._methods = {}  # cls -> code

        self.class_handle = open(class_path, "wb")
        self.class_handle.write("""
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

    def get_name(self):
        return self.class_handle.name

    def finalize(self):
        classes = self._classes.keys()

        # sort classes by how the should be defined in the code
        # so all bases are defined when needed
        counts = {}
        for x in classes:
            for y in classes:
                if x in y.__mro__:
                    if x not in counts:
                        counts[x] = 1
                    else:
                        counts[x] += 1
        counts = list(sorted(counts.items(), key=lambda x: x[1], reverse=True))
        order = [c[0] for c in counts]

        def indent(c):
            return "\n".join(["    %s" % l for l in c.splitlines()])

        # add the classes to the module
        for cls in order:
            self._module.write(self._classes[cls])
            for method in self._methods.get(cls, []):
                self._module.write(indent(method))
            name = cls.__module__ + "." + cls.__name__

            self.class_handle.write("""
.. inheritance-diagram:: %s

.. autoclass:: %s
    :show-inheritance:
    :members:
""" % (name, name))

        self.class_handle.close()


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

        # utf-8 encoded .py
        self.module.write("# -*- coding: utf-8 -*-\n")

    def get_index_name(self):
        return self.index_name

    def add_dependency(self, name, version):
        """Import the module in the generated code"""
        self.module.write("import gi\n")
        self.module.write("gi.require_version('%s', '%s')\n" % (name, version))
        self.module.write("from gi.repository import %s\n" % name)

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

    def finalize(self):
        func_name = os.path.basename(self.func_handle.name)
        class_name = os.path.basename(self._class_gen.get_name())

        with open(os.path.join(self.prefix, "index.rst"),  "wb") as h:
            title = "%s %s" % (self.namespace, self.version)
            h.write(title + "\n")
            h.write(len(title) * "=" + "\n")

            h.write("""

.. toctree::
    %(functions)s
    %(classes)s

""" % {"functions": func_name, "classes": class_name})

        self._class_gen.finalize()

        self.func_handle.close()
        self.module.close()

        # make sure the generated code is valid python
        with open(self.module.name, "rb") as h:
            exec h.read() in {}


def create_docs(main_gen, namespace, version):
    gen = main_gen.get_generator(namespace, version)
    mod = import_namespace(namespace, version)
    repo = Repository(namespace, version)

    # import the needed modules
    for dep in repo.get_dependencies():
        gen.add_dependency(*dep)

    from gi.repository import GObject
    class_base = GObject.Object
    #struct_base = GObject.Value.__mro__[-2]

    for key in dir(mod):
        if key.startswith("_"):
            continue
        obj = getattr(mod, key)

        name = "%s.%s" % (namespace, key)

        if isinstance(obj, types.FunctionType):
            code = repo.parse_function(name, obj)
            if code:
                gen.add_function(name, code)
        elif inspect.isclass(obj):
            if issubclass(obj, class_base):

                for attr in dir(obj):
                    if attr.startswith("_"):
                        continue

                    func_key = name + "." + attr
                    try:
                        attr_obj = getattr(obj, attr)
                    except NotImplementedError:
                        # FIXME.. pgi exposes methods it can't compile
                        continue
                    if isinstance(attr_obj, types.MethodType):
                        code = repo.parse_function(func_key, attr_obj, True)
                        if code:
                            gen.add_method(obj, code)

                code = repo.parse_class(key, obj, add_bases=True)
                if code:
                    gen.add_class(obj, code)
            else:
                # structs, enums, etc.
                code = repo.parse_class(key, obj)
                if code:
                    gen.add_class(obj, code)

    gen.finalize()


if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print "%s <namespace-version>..." % sys.argv[0]
        raise SystemExit(1)

    gen = MainGenerator()

    for arg in sys.argv[1:]:
        namespace, version = arg.split("-")
        print "Create docs: Namespace=%s, Version=%s" % (namespace, version)
        if namespace == "cairo":
            print "cairo gets referenced to external docs, skipping"
            continue
        create_docs(gen, namespace, version)

    gen.finalize()
